# sync_worker.py
import threading
import time
import requests
from local_queue import init_db, fetch_batch, delete_ids
from requests.exceptions import RequestException


API_BASE_URL = "https://web-production-f83f0.up.railway.app"


CHECK_INTERVAL = 5  # seconds between sync attempts
BATCH_SIZE =20
class SyncWorker:
    def __init__(self, api_base_url = str,status_callback=None, token= None):
        
        self.api_base_url =api_base_url
        self.status_callback = status_callback
        self.token =token
        init_db()
        self._stop = threading.Event()
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()

    def _set_status(self, text: str):
        if self.status_callback:
            try:
                self.status_callback(text)
            except Exception:
                pass

    def stop(self):
        self._stop.set()
        self.thread.join(timeout=2)

    def _run(self):
        self._set_status("Idle")
        while not self._stop.is_set():
            try:
                batch = fetch_batch(BATCH_SIZE)
                if not batch:
                    self._set_status("All synced")
                    time.sleep(CHECK_INTERVAL)
                    continue

                success_ids = []
                self._set_status(f"Syncing {len(batch)} item(s)…")

                for row_id, payload in batch:
                    try:
                        email = payload.get("email")
                        blink_count = int(payload.get("blink_count", 1))

                        if not email:
            # Skip invalid entries
                            success_ids.append(row_id)
                            continue

                        json_data = {
                            "email": email,
                            "blink_count": blink_count
                        }
                        print("Sending JSON:", json_data)  # debug
                        headers = {"Authorization": f"Bearer {self.token}"}
        # Send POST request with proper JSON
                        r = requests.post(
                            f"{API_BASE_URL}/blink",
                            json=json_data,
                            headers= headers,# <-- JSON body, not params
                            timeout=5
                        )

                        if r.status_code == 200:
                            success_ids.append(row_id)
                        elif r.status_code == 422:
            # Validation error from FastAPI
                            print("Validation error:", r.text)
            # Skip this item to avoid blocking others
                            success_ids.append(row_id)
                            self._set_status(f"Skipped invalid item (422)")
                        else:
                            print("Server error:", r.status_code, r.text)
                            self._set_status(f"Server error {r.status_code}; retrying later")
                            break

                    except requests.RequestException as e:
                        print("Request failed:", e)
                        self._set_status("Offline/server error; retrying…")
                        break
                    except Exception as e:
                        print("Unknown error:", e)
                        self._set_status("Error; retrying…")
                        break

# Delete successfully synced items
                if success_ids:
                    delete_ids(success_ids)
                    self._set_status(f"Last sync ok ({len(success_ids)} sent)")
                else:
                    self._set_status("No items synced")



                time.sleep(CHECK_INTERVAL)

            except RequestException:
                self._set_status("Offline/server error; retrying…")
                time.sleep(CHECK_INTERVAL)
            except Exception:
                # Unknown error — wait and continue
                self._set_status("Error; retrying…")
                time.sleep(CHECK_INTERVAL)
