import threading
import time
from typing import Iterable, Optional

from social_faucet import settings


class RateLimiter:
    def __init__(self, db, excluded_users: Optional[Iterable[str]] = None):
        self.db = db
        if excluded_users is None:
            excluded_users = set()
        self.excluded_users = set(excluded_users)
        self._lock = threading.Lock()

    def add(self, user_id=None, address=None, seconds=settings.RATE_LIMIT):
        current_timestamp = int(time.time())
        limit_until = current_timestamp + seconds
        with self._lock:
            if user_id:
                self.db[self._user_key(user_id)] = str(limit_until)
            if address:
                self.db[self._address_key(address)] = str(limit_until)

    def remove(self, user_id=None, address=None):
        with self._lock:
            if user_id:
                del self.db[self._user_key(user_id)]
            if address:
                del self.db[self._address_key(address)]

    def get(self, value: str) -> int:
        if value.startswith("0x"):
            return self.get_address(value)
        return self.get_user(value)

    def get_user(self, user_id: str) -> int:
        with self._lock:
            return int(self.db.get(self._user_key(user_id), 0))

    def get_address(self, address: str) -> int:
        with self._lock:
            return int(self.db.get(self._address_key(address), 0))

    def is_rate_limited(self, user_id, address):
        if user_id in self.excluded_users or address in self.excluded_users:
            return False
        user_timestamp = self.get_user(user_id)
        address_timestamp = self.get_address(address)
        current_timestamp = int(time.time())
        return current_timestamp < max(user_timestamp, address_timestamp)

    @staticmethod
    def _user_key(user_id):
        return "user_id:{0}".format(user_id)

    @staticmethod
    def _address_key(address):
        return "address:{0}".format(address)
