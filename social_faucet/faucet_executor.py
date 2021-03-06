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
        if transaction.get("gasPrice") == 0:
            transaction.pop("gasPrice", None)
        transaction.update(
            {
                "chainId": self.web3.eth.chain_id,
                "nonce": nonce,
                "maxFeePerGas": self.web3.toWei(settings.GAS_PRICE, "gwei"),
                "maxPriorityFeePerGas": self.web3.toWei(
                    settings.MAX_PRIORITY_FEE_PER_GAS, "gwei"
                ),
            }
        )
        return transaction

    def send_transaction(self, address: str, raw_tx: dict):
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
            logging.error("failed to send transaction %s: %s", raw_tx, exc_info=ex)
            return Status.ERROR

    def _execute_transaction(
        self,
        tx_builder: TransactionBuilder,
        address: str,
        retries: int = 3,
    ):
        result = Status.SUCCESS
        for i in range(retries + 1):
            transaction = None
            warn_params = {}
            try:
                transaction = self.create_transaction(tx_builder, address)
                result = self.send_transaction(address, transaction)
                if result == Status.SUCCESS:
                    return result
                error = f"received status {result}"
            except Exception as ex:
                error = str(ex)
                warn_params = {"exc_info": ex}

            time_to_sleep = 2 ** i
            logging.warning(
                "failed to send transaction %s: %s, sleeping %ss",
                transaction,
                error,
                time_to_sleep,
                **warn_params,
            )
            time.sleep(time_to_sleep)
        return result

    def send_transactions(self, address: str, user_id: Optional[str] = None):
        self.rate_limiter.add(address=address, user_id=user_id)
        for tx_builder in self.transaction_builders:
            result = self._execute_transaction(tx_builder, address)
            if result != Status.SUCCESS:
                self.rate_limiter.remove(address=address, user_id=user_id)
                return result
        return Status.SUCCESS

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

        return self.send_transactions(address, user_id=message.user_id)
