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


def run_faucet(web3: Web3, faucet: Faucet, db_path: str):
    with dbm.open(db_path, "c") as db:
        rate_limiter = RateLimiter(db)
        transaction_builders = faucet.create_transaction_builders(web3)
        validators = faucet.create_validators()
        faucet_executor = FaucetExecutor(
            web3,
            rate_limiter,
            transaction_builders=transaction_builders,
            validators=validators,
        )

        faucet.listen(faucet_executor)


def run_kovan_faucet(faucet: Faucet, db_path: str):
    from web3.auto.infura.kovan import w3

    run_faucet(w3, faucet, db_path)


def run_twitter_kovan_faucet(keywords: List[str], db_path: str):
    faucet = TwitterKovanFaucet(keywords)
    run_kovan_faucet(faucet, db_path)


def run_discord_tokens_kovan_faucet(db_path: str):
    faucet = DiscordMintTokensAsOwnerKovanFaucet()
    run_kovan_faucet(faucet, db_path)
