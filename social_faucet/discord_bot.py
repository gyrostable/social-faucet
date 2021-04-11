import logging
from typing import Optional, Set

import discord
from discord.message import Message as DiscordMessage

from social_faucet.faucet_executor import FaucetExecutor
from social_faucet.types import Message, Status


EMOJIS = {
    Status.SUCCESS: "👍",
    Status.RATE_LIMITED: "🚓",
    Status.INVALID: "🤷‍♀️",
    Status.ERROR: "🚧",
}


class FaucetDiscordClient(discord.Client):
    def __init__(
        self, faucet_executor: FaucetExecutor, channels: Optional[Set[str]] = None
    ):
        super().__init__()
        self.channels = channels
        self.faucet_executor = faucet_executor

    async def on_ready(self):
        logging.info(f"logged in discord as {self.user}")

    async def on_message(self, message: DiscordMessage):
        if self.channels is not None and message.channel.name not in self.channels:
            return

        faucet_message = Message(
            source="discord",
            id=str(message.id),
            user_id=message.author.id,  # type: ignore
            text=message.content,
        )
        status = self.faucet_executor.process_message(faucet_message)
        emoji = EMOJIS[status]
        await message.add_reaction(emoji)
