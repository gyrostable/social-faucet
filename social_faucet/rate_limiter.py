import time

from social_faucet import settings


class RateLimiter:
    def __init__(self, db):
        self.db = db

    def add(self, user_id, address):
        current_timestamp = int(time.time())
        self.db[self._user_key(user_id)] = str(current_timestamp)
        self.db[self._address_key(address)] = str(current_timestamp)

    def is_rate_limited(self, user_id, address):
        current_timestamp = int(time.time())
        user_timestamp = int(self.db.get(self._user_key(user_id), 0))
        address_timestamp = int(self.db.get(self._address_key(address), 0))
        return (
            current_timestamp - max(user_timestamp, address_timestamp)
            < settings.RATE_LIMIT
        )

    @staticmethod
    def _user_key(user_id):
        return "user_id:{0}".format(user_id)

    @staticmethod
    def _address_key(address):
        return "address:{0}".format(address)
