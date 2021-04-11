from abc import ABC, abstractmethod

from web3.contract import Contract

from social_faucet import settings


class TransactionBuilder(ABC):
    @abstractmethod
    def build_transaction(self, receiver: str) -> dict:
        pass


class SendETHTransactionBuilder(TransactionBuilder):
    def __init__(self, send_value: int = settings.SEND_VALUE):
        self.send_value = send_value

    def build_transaction(self, receiver: str) -> dict:
        return {"value": self.send_value, "gas": 25000, "to": receiver}


class MintAsOwnerTransactionBuilder(TransactionBuilder):
    def __init__(self, contract: Contract, gas: int):
        self.contract = contract
        self.gas = gas

    def build_transaction(self, receiver: str) -> dict:
        tx = self.contract.functions.mintAsOwner(dst=receiver)
        return tx.buildTransaction({"gas": self.gas})  # type: ignore
