# social-faucet

This is a simple faucet implementation that allows to give away ETH or custom
tokens using social media to verify user's identity.

Supported social media:

* Twitter
* Discord

The faucet enables rate limiting for address/user id using a local on-disk database.

## Installation

```
git clone https://github.com/stablecoin-labs/social-faucet.git
cd social-faucet
pip install -e .
```

## Usage

First, copy `.env.example` to `.env` and fill in the details.
Then, check `settings.py` and modify as needed.
Finally run `social-faucet -h` to see the different options.
