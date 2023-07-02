import json

from web3 import Account
from web3 import HTTPProvider
from web3 import Web3

web3 = Web3(HTTPProvider("http://127.0.0.1:8545"))


def read_file(path):
    with open(path, "r") as file:
        return file.read()


keys = json.loads(read_file("keys.json"))

address = web3.to_checksum_address(keys["address"])
private_key = Account.decrypt(keys, "iepblockchain").hex()
