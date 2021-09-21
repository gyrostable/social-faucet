import argparse
import logging
import os

from social_faucet import runner, settings

parser = argparse.ArgumentParser(prog="social-faucet")

subparsers = parser.add_subparsers(dest="command")
twitter_kovan_parser = subparsers.add_parser(
    "twitter-kovan", help="Runs Twitter Kovan Faucet sending ETH"
)
twitter_kovan_parser.add_argument("keywords", nargs="+")
twitter_kovan_parser.add_argument("--db", required=True, help="Path to rate limit DB")
twitter_kovan_parser.add_argument(
    "--control-port",
    type=int,
    required=True,
    help="HTTP port to use to control the process",
)

discord_kovan_parser = subparsers.add_parser(
    "discord-kovan-tokens", help="Runs Discord Kovan Faucet sending tokens"
)
discord_kovan_parser.add_argument("--db", required=True, help="Path to rate limit DB")
discord_kovan_parser.add_argument(
    "--control-port",
    type=int,
    required=True,
    help="HTTP port to use to control the process",
)


def run():
    logging.basicConfig(level=logging.INFO, format=settings.LOG_FORMAT)
    args = parser.parse_args()

    if not args.command:
        parser.error("no command provided")

    rate_limit_exclusions = None
    if settings.RATE_LIMIT_EXCLUSIONS:
        rate_limit_exclusions = [
            v.strip() for v in settings.RATE_LIMIT_EXCLUSIONS.split(",")
        ]

    if args.command == "twitter-kovan":
        runner.run_twitter_kovan_faucet(
            args.keywords, args.db, args.control_port, rate_limit_exclusions
        )
    elif args.command == "discord-kovan-tokens":
        runner.run_discord_tokens_kovan_faucet(
            args.db, args.control_port, rate_limit_exclusions
        )


if __name__ == "__main__":
    run()
