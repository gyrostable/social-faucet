import logging
import time
from typing import List, Optional

import web3

from social_faucet import settings
from social_faucet.rate_limiter import RateLimiter
from social_faucet.transaction_builder import TransactionBuilder
from social_faucet.types import Message, Status
from social_faucet.validation import ValidationError, Validator


def extract_address(text):
    try:
        address_index = text.index("0x")
        address = text[address_index : address_index + settings.ADDRESS_LENGTH]
        return web3.Web3.toChecksumAddress(address)
    except ValueError:
        return False


class FaucetExecutor:
    def __init__(
        self,
        web3: web3.Web3,
        rate_limiter: RateLimiter,
        transaction_builders: List[TransactionBuilder],
        validators: List[Validator] = None,
        private_key: Optional[str] = settings.KOVAN_PRIVATE_KEY,
    ):
        super().__init__()
        if validators is None:
            validators = []
        self.validators = validators
        self.transaction_builders = transaction_builders
        self.rate_limiter = rate_limiter
        self.web3 = web3
        self.private_key = private_key

    def log_issue(self, message: Message, error: str):
        logging.warning(
            "could not process message %s from %s (%s): %s",
            message.id,
            message.source,
            message.text,
            error,
        )

    def run_validators(self, message: Message) -> bool:
        try:
            for validator in self.validators:
                validator.validate(message)
            return True
        except ValidationError as ex:
            self.log_issue(message, f"invalid: {ex}")
            return False

    def create_transaction(self, tx_builder: TransactionBuilder, address: str) -> dict:
        nonce = self.web3.eth.get_transaction_count(settings.KOVAN_ADDRESS)
        transaction = tx_builder.build_transaction(address)
        transaction.update({"nonce": nonce, "gasPrice": settings.GAS_PRICE})
        return transaction

    def send_transaction(self, message: Message, address: str, raw_tx: dict):
        logging.info("sending %s", raw_tx)
        signed_tx = self.web3.eth.account.sign_transaction(raw_tx, self.private_key)
        try:
            tx = self.web3.eth.send_raw_transaction(signed_tx.rawTransaction)
            logging.info("sent transaction %s", tx.hex())
            receipt = self.web3.eth.waitForTransactionReceipt(tx, timeout=20)
            tx_hash = receipt["transactionHash"].hex()
            logging.info("transaction %s to %s confirmed", tx_hash, address)
            return Status.SUCCESS
        except Exception as ex:
            logging.error("failed to send transaction %s: %s", raw_tx, str(ex))
            return Status.ERROR

    def _execute_transaction(
        self,
        tx_builder: TransactionBuilder,
        address: str,
        message: Message,
        retries: int = 3,
    ):
        result = Status.SUCCESS
        for i in range(retries + 1):
            transaction = self.create_transaction(tx_builder, address)
            result = self.send_transaction(message, address, transaction)
            if result == Status.SUCCESS:
                return result
            time_to_sleep = 2 ** 1
            logging.warning("failed to send transaction, sleeping %ss", time_to_sleep)
            time.sleep(2 ** i)
        return result

    def process_message(self, message: Message) -> Status:
        if not self.run_validators(message):
            return Status.INVALID

        address = extract_address(message.text)
        if not address:
            self.log_issue(message, "address not found")
            return Status.INVALID

        if self.rate_limiter.is_rate_limited(message.user_id, address):
            logging.warning(
                "(%s, %s) was rate limited, skipping", message.user_id, address
            )
            return Status.RATE_LIMITED

        for tx_builder in self.transaction_builders:
            result = self._execute_transaction(tx_builder, address, message)
            if result != Status.SUCCESS:
                return result

        self.rate_limiter.add(message.user_id, address)
        return Status.SUCCESS
