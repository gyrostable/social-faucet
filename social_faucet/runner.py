import dbm
from threading import Thread
from typing import Iterable, List, Optional

from web3.main import Web3

from social_faucet.http import app
from social_faucet.faucet import (
    DiscordMintTokensAsOwnerKovanFaucet,
    Faucet,
    TwitterKovanFaucet,
)
from social_faucet.faucet_executor import FaucetExecutor
from social_faucet.rate_limiter import RateLimiter


def launch_control_app(
    port: int, rate_limiter: RateLimiter, faucet_executor: FaucetExecutor
):
    app.rate_limiter = rate_limiter
    app.faucet_executor = faucet_executor
    app_thread = Thread(
        target=app.run, kwargs={"port": port, "debug": False}, daemon=True
    )
    app_thread.start()


def run_faucet(
    web3: Web3,
    faucet: Faucet,
    db_path: str,
    control_port: int,
    rate_limited_exclusions: Optional[Iterable[str]],
):
    with dbm.open(db_path, "c") as db:
        rate_limiter = RateLimiter(db, excluded_users=rate_limited_exclusions)
        transaction_builders = faucet.create_transaction_builders(web3)
        validators = faucet.create_validators()
        faucet_executor = FaucetExecutor(
            web3,
            rate_limiter,
            transaction_builders=transaction_builders,
            validators=validators,
        )

        launch_control_app(control_port, rate_limiter, faucet_executor)

        faucet.listen(faucet_executor)


def run_kovan_faucet(
    faucet: Faucet,
    db_path: str,
    control_port: int,
    rate_limited_exclusions: Optional[Iterable[str]],
):
    from web3.auto.infura.kovan import w3

    run_faucet(w3, faucet, db_path, control_port, rate_limited_exclusions)


def run_twitter_kovan_faucet(
    keywords: List[str],
    db_path: str,
    control_port: int,
    rate_limited_exclusions: Optional[Iterable[str]],
):
    faucet = TwitterKovanFaucet(keywords)
    run_kovan_faucet(faucet, db_path, control_port, rate_limited_exclusions)


def run_discord_tokens_kovan_faucet(
    db_path: str, control_port: int, rate_limited_exclusions: Optional[Iterable[str]]
):
    faucet = DiscordMintTokensAsOwnerKovanFaucet()
    run_kovan_faucet(faucet, db_path, control_port, rate_limited_exclusions)
