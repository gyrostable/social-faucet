from abc import ABC, abstractmethod
from typing import List
from social_faucet.types import Message


class Validator(ABC):
    @abstractmethod
    def validate(self, message: Message):
        pass


class ValidationError(ValueError):
    pass


class KeywordsValidator(Validator):
    def __init__(self, keywords: List[str]):
        self.keywords = keywords

    def validate(self, message: Message):
        for keyword in self.keywords:
            if keyword not in message.text:
                raise ValidationError(f"{keyword} not found in {message.text}")


class RetweetValidator(Validator):
    def validate(self, message: Message):
        if message.extra.get("is_retweet", False):
            raise ValidationError("message is a retweet")
