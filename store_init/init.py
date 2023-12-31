from flask import Flask
from sqlalchemy_utils import database_exists, create_database
from web3 import Account, HTTPProvider, Web3

from configuration import Configuration
from models import database

application = Flask(__name__)
application.config.from_object(Configuration)

database.init_app(application)
if not database_exists(Configuration.SQLALCHEMY_DATABASE_URI):
    create_database(Configuration.SQLALCHEMY_DATABASE_URI)

with application.app_context():
    database.create_all()
    database.session.commit()

with open("keys.json", "r") as file:
    private_key = Account.decrypt(file.read(), "iepblockchain").hex()

owner_account = Account.from_key(private_key)

web3 = Web3(HTTPProvider(Configuration.ETHEREUM_URI))

web3.eth.send_transaction({
    "from": web3.eth.accounts[0],
    "to": owner_account.address,
    "value": web3.to_wei(5, "ether")
})
