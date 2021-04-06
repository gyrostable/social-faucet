import argparse
import dbm
import logging
import os
import time
from typing import List

import tweepy
import web3
from dotenv import load_dotenv

LOG_FORMAT = "%(asctime)-15s - %(levelname)s - %(message)s"

RATE_LIMIT = 86400
ADDRESS_LENGTH = 42
DB_PATH = "rate_limit.db"

SEND_VALUE = 2 * 10 ** 17


load_dotenv()

TWEET_TEXTS = ["#GyrosoftWeatherSimulator", "@GyroStable", "0x", "Kovan"]

KOVAN_ADDRESS = os.environ["KOVAN_ADDRESS"]
KOVAN_PRIVATE_KEY = os.environ["KOVAN_PRIVATE_KEY"]

TWITTER_API_KEY = os.environ["TWITTER_API_KEY"]
TWITTER_SECRET_KEY = os.environ["TWITTER_SECRET_KEY"]
TWITTER_ACCESS_TOKEN = os.environ["TWITTER_ACCESS_TOKEN"]
TWITTER_ACCESS_TOKEN_SECRET = os.environ["TWITTER_ACCESS_TOKEN_SECRET"]

BASE_TRANSACTION = {"value": SEND_VALUE, "gasPrice": 10 ** 9, "gas": 25000}


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
        return current_timestamp - max(user_timestamp, address_timestamp) < RATE_LIMIT

    @staticmethod
    def _user_key(user_id):
        return "user_id:{0}".format(user_id)

    @staticmethod
    def _address_key(address):
        return "address:{0}".format(address)


class FaucetStreamListener(tweepy.StreamListener):
    def __init__(self, rate_limiter: RateLimiter, web3: web3.Web3):
        super().__init__()
        self.rate_limiter = rate_limiter
        self.web3 = web3

    def on_status(self, status):
        if not self.is_valid(status):
            logging.warning(
                "tweet %s was not valid, skipping: %s", status.id, status.text
            )
            return
        address = self.extract_address(status.text)
        if not address:
            logging.warning(
                "no address found in %s, skipping: %s", status.id, status.text
            )
            return
        user_id = status.author.id_str
        if self.rate_limiter.is_rate_limited(user_id, address):
            logging.warning("(%s, %s) was rate limited, skipping", user_id, address)
            return

        logging.info("sending %s ETH to %s", SEND_VALUE, address)
        nonce = self.web3.eth.get_transaction_count(KOVAN_ADDRESS)
        transaction = {"to": address, "nonce": nonce}
        transaction.update(BASE_TRANSACTION)
        signed_tx = self.web3.eth.account.sign_transaction(
            transaction, KOVAN_PRIVATE_KEY
        )
        try:
            tx = self.web3.eth.send_raw_transaction(signed_tx.rawTransaction)
            logging.info("sent transaction %s", tx.hex())
            receipt = self.web3.eth.waitForTransactionReceipt(tx)
            tx_hash = receipt["transactionHash"].hex()
            self.rate_limiter.add(user_id, address)
            logging.info("sent %s ETH to %s: %s", SEND_VALUE, address, tx_hash)
        except Exception as ex:
            logging.error("failed to send transaction %s: %s", transaction, ex)

    @staticmethod
    def extract_address(text):
        address_index = text.index("0x")
        address = text[address_index : address_index + ADDRESS_LENGTH]
        try:
            return web3.Web3.toChecksumAddress(address)
        except ValueError:
            return False

    @staticmethod
    def is_valid(status):
        if getattr(status, "retweeted_status", None):
            return False
        return all(v in status.text for v in TWEET_TEXTS)

    def on_error(self, status_code):
        logging.error("event listener failed with code %s", status_code)
        return False


def authenticate():
    auth = tweepy.OAuthHandler(TWITTER_API_KEY, TWITTER_SECRET_KEY)
    auth.access_token = TWITTER_ACCESS_TOKEN
    auth.access_token_secret = TWITTER_ACCESS_TOKEN_SECRET
    return auth


def listen(keywords: List[str]):
    from web3.auto.infura.kovan import w3

    with dbm.open(DB_PATH, "c") as db:
        rate_limiter = RateLimiter(db)
        auth = authenticate()
        faucet_stream_listener = FaucetStreamListener(rate_limiter, w3)
        stream = tweepy.Stream(auth=auth, listener=faucet_stream_listener)
        stream.filter(track=keywords)


def main():
    parser = argparse.ArgumentParser(prog="twitter-faucet")
    parser.add_argument("keywords", nargs="+")
    logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)
    args = parser.parse_args()
    keywords = args.keywords
    listen(keywords)


if __name__ == "__main__":
    main()
