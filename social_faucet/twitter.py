import logging

import tweepy

from social_faucet import settings
from social_faucet.faucet_executor import FaucetExecutor
from social_faucet.types import Message


class TwitterFaucetStreamListener(tweepy.StreamListener):
    def __init__(self, faucet: FaucetExecutor):
        super().__init__()
        self.faucet_executor = faucet

    def on_status(self, status):
        is_retweet = getattr(status, "retweeted_status", None) is not None
        message = Message(
            source="twitter",
            id=status.id,
            user_id=status.author.id_str,
            text=status.text,
            extra={"is_retweet": is_retweet},
        )
        self.faucet_executor.process_message(message)

    def on_error(self, status_code):
        logging.error("event listener failed with code %s", status_code)
        return False
