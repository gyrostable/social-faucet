import asyncio
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
        self.message_queue = []

    async def on_ready(self):
        logging.info(f"logged in discord as {self.user}")
        asyncio.create_task(self.process_queue())

    async def on_message(self, message: DiscordMessage):
        if self.channels is not None and message.channel.name not in self.channels:
            return

        self.message_queue.append(message)

    async def process_queue(self):
        while True:
            if not self.message_queue:
                await asyncio.sleep(0.1)
                continue

            message = self.message_queue.pop(0)
            faucet_message = Message(
                source="discord",
                id=str(message.id),
                user_id=message.author.id,  # type: ignore
                text=message.content,
            )
            status = self.faucet_executor.process_message(faucet_message)
            emoji = EMOJIS[status]
            await message.add_reaction(emoji)
