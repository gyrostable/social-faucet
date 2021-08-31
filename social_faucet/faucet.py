import json
from abc import ABC, abstractmethod
from os import path
from social_faucet.discord_bot import FaucetDiscordClient
from typing import List, Optional, Set, Tuple

import tweepy
from web3.main import Web3

from social_faucet import settings
from social_faucet.faucet_executor import FaucetExecutor
from social_faucet.transaction_builder import (
    MintAsOwnerTransactionBuilder,
    SendETHTransactionBuilder,
    TransactionBuilder,
)
from social_faucet.twitter import TwitterFaucetStreamListener
from social_faucet.validation import KeywordsValidator, RetweetValidator, Validator


class Faucet(ABC):
    @abstractmethod
    def listen(self, faucet_executor: FaucetExecutor):
        pass

    @abstractmethod
    def create_transaction_builders(self, web3: Web3) -> List[TransactionBuilder]:
        pass

    @abstractmethod
    def create_validators(self) -> List[Validator]:
        pass


class WithMintOwnerTxBuilder:
    def __init__(self, address, gas, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.address = address
        self.gas = gas

    def create_mint_as_owner_transaction_builder(self, web3):
        with open(path.join(settings.DATA_PATH, "meta-faucet.json")) as f:
            abi = json.load(f)
        contract = web3.eth.contract(abi=abi, address=self.address)  # type: ignore
        return MintAsOwnerTransactionBuilder(contract=contract, gas=self.gas)


class TwitterKovanFaucet(WithMintOwnerTxBuilder, Faucet):
    def __init__(
        self,
        keywords: List[str],
        address: str = settings.META_FAUCET_ADDRESS,
        gas: int = settings.META_FAUCET_GAS,
    ):
        super().__init__(address, gas)
        self.keywords = keywords

    def create_transaction_builders(self, web3: Web3):
        return [
            SendETHTransactionBuilder(),
            self.create_mint_as_owner_transaction_builder(web3),
        ]

    def create_validators(self) -> List[Validator]:
        return [RetweetValidator(), KeywordsValidator(settings.TWEET_TEXTS)]

    def listen(self, faucet_executor: FaucetExecutor):
        faucet_stream_listener = TwitterFaucetStreamListener(faucet_executor)
        auth = self._authenticate()
        stream = tweepy.Stream(auth=auth, listener=faucet_stream_listener)
        stream.filter(track=self.keywords)

    def _authenticate(self):
        auth = tweepy.OAuthHandler(
            settings.TWITTER_API_KEY, settings.TWITTER_SECRET_KEY
        )
        auth.access_token = settings.TWITTER_ACCESS_TOKEN
        auth.access_token_secret = settings.TWITTER_ACCESS_TOKEN_SECRET
        return auth


class DiscordMintTokensAsOwnerKovanFaucet(WithMintOwnerTxBuilder, Faucet):
    def __init__(
        self,
        channels: Optional[List[str]] = settings.DISCORD_CHANNELS,
        address: str = settings.META_FAUCET_ADDRESS,
        gas: int = settings.META_FAUCET_GAS,
    ):
        super().__init__(address, gas)
        self.channels = set(channels) if channels else None

    def create_transaction_builders(self, web3: Web3) -> List[TransactionBuilder]:
        return [
            SendETHTransactionBuilder(),
            self.create_mint_as_owner_transaction_builder(web3),
        ]

    def create_validators(self) -> List[Validator]:
        return []

    def listen(self, faucet_executor: FaucetExecutor):
        client = FaucetDiscordClient(faucet_executor, channels=self.channels)
        client.run(settings.DISCORD_BOT_TOKEN)
