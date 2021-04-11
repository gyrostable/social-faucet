import os
from os import path

from dotenv import load_dotenv

load_dotenv()

PROJECT_ROOT = path.dirname(path.dirname(__file__))
DATA_PATH = path.join(PROJECT_ROOT, "data")

TWEET_TEXTS = ["#GyrosoftWeatherSimulator", "@GyroStable", "0x", "Kovan"]

KOVAN_ADDRESS = os.environ.get("KOVAN_ADDRESS")
KOVAN_PRIVATE_KEY = os.environ.get("KOVAN_PRIVATE_KEY")

TWITTER_API_KEY = os.environ.get("TWITTER_API_KEY")
TWITTER_SECRET_KEY = os.environ.get("TWITTER_SECRET_KEY")
TWITTER_ACCESS_TOKEN = os.environ.get("TWITTER_ACCESS_TOKEN")
TWITTER_ACCESS_TOKEN_SECRET = os.environ.get("TWITTER_ACCESS_TOKEN_SECRET")

DISCORD_BOT_TOKEN = os.environ.get("DISCORD_BOT_TOKEN")
DISCORD_CHANNELS = ("testnet-faucet",)

META_FAUCET_ADDRESS = "0x8F9d07DF84B387d05f3bb1de77B9cc577cF3507E"
META_FAUCET_GAS = 250_000


LOG_FORMAT = "%(asctime)-15s - %(levelname)s - %(message)s"

RATE_LIMIT = 86400
ADDRESS_LENGTH = 42
DB_PATH = "rate_limit.db"

SEND_VALUE = 2 * 10 ** 17
GAS_PRICE = 10 ** 9
