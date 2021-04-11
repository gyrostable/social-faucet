import dbm
from typing import List

from web3.main import Web3

from social_faucet import settings
from social_faucet.faucet import (
    DiscordMintTokensAsOwnerKovanFaucet,
    Faucet,
    TwitterKovanFaucet,
)
from social_faucet.faucet_executor import FaucetExecutor
from social_faucet.rate_limiter import RateLimiter


def run_faucet(web3: Web3, faucet: Faucet):
    with dbm.open(settings.DB_PATH, "c") as db:
        rate_limiter = RateLimiter(db)
        transaction_builder = faucet.create_transaction_builder(web3)
        validators = faucet.create_validators()
        faucet_executor = FaucetExecutor(
            web3,
            rate_limiter,
            transaction_builder=transaction_builder,
            validators=validators,
        )

        faucet.listen(faucet_executor)


def run_kovan_faucet(faucet: Faucet):
    from web3.auto.infura.kovan import w3

    run_faucet(w3, faucet)


def run_twitter_kovan_faucet(keywords: List[str]):
    faucet = TwitterKovanFaucet(keywords)
    run_kovan_faucet(faucet)


def run_discord_tokens_kovan_faucet():
    faucet = DiscordMintTokensAsOwnerKovanFaucet()
    run_kovan_faucet(faucet)
