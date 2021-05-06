from setuptools import setup, find_packages


setup(
    name="social-faucet",
    packages=find_packages(),
    install_requires=["tweepy", "python-dotenv", "web3", "discord", "flask"],
    entry_points={"console_scripts": ["social-faucet=social_faucet.cli:run"]},
)
