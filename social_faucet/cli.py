import argparse
import logging

from social_faucet import runner, settings

parser = argparse.ArgumentParser(prog="social-faucet")

subparsers = parser.add_subparsers(dest="command")
twitter_kovan_parser = subparsers.add_parser(
    "twitter-kovan", help="Runs Twitter Kovan Faucet sending ETH"
)
twitter_kovan_parser.add_argument("keywords", nargs="+")

discordkovan_parser = subparsers.add_parser(
    "discord-kovan-tokens", help="Runs Discord Kovan Faucet sending tokens"
)


def run():
    logging.basicConfig(level=logging.INFO, format=settings.LOG_FORMAT)
    args = parser.parse_args()

    if not args.command:
        parser.error("no command provided")

    if args.command == "twitter-kovan":
        runner.run_twitter_kovan_faucet(args.keywords)
    elif args.command == "discord-kovan-tokens":
        runner.run_discord_tokens_kovan_faucet()


if __name__ == "__main__":
    run()
