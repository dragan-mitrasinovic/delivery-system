from flask import Flask, request, make_response, jsonify, Response
from flask_jwt_extended import JWTManager
from web3 import HTTPProvider, Web3, Account

from configuration import Configuration
from models import database, Order
from role_check import role_check

web3 = Web3(HTTPProvider(Configuration.ETHEREUM_URI))

application = Flask(__name__)
application.config.from_object(Configuration)

jwt = JWTManager(application)

database.init_app(application)


def read_file(path):
    with open(path, "r") as file:
        return file.read()


@application.route("/orders_to_deliver", methods=["GET"])
@role_check("courier")
def orders_to_deliver():
    orders_rows = Order.query \
        .with_entities(Order.id, Order.email) \
        .filter(Order.status == "CREATED") \
        .all()
    orders = [
        {"id": row.id, "email": row.email}
        for row in orders_rows
    ]
    return make_response(jsonify(orders=orders), 200)


@application.route("/pick_up_order", methods=["POST"])
@role_check("courier")
def pick_up_order():
    order_id = request.json.get("id", None)
    if not order_id:
        return make_response(jsonify(message="Missing order id."), 400)

    try:
        order_id = int(order_id)
        if order_id <= 0:
            return make_response(jsonify(message="Invalid order id."), 400)
    except ValueError:
        return make_response(jsonify(message="Invalid order id."), 400)

    order = Order.query.filter(Order.id == order_id).first()
    if not order or order.status != "CREATED":
        return make_response(jsonify(message="Invalid order id."), 400)

    order.status = "PENDING"
    database.session.add(order)

    address = request.json.get("address", None)
    if not address:
        database.session.rollback()
        return make_response(jsonify(message="Missing address."), 400)

    if not web3.is_address(address):
        database.session.rollback()
        return make_response(jsonify(message="Invalid address."), 400)

    address = web3.to_checksum_address(address)

    abi = read_file("solidity/order.abi")
    contract = web3.eth.contract(address=order.contract_address, abi=abi)

    if not contract.functions.paid().call():
        database.session.rollback()
        return make_response(jsonify(message="Transfer not complete."), 400)

    with open("keys.json", "r") as file:
        private_key = Account.decrypt(file.read(), "iepblockchain").hex()

    owner_account = Account.from_key(private_key)

    transaction = contract.functions.setCourier(address).build_transaction({
        "from": owner_account.address,
        "nonce": web3.eth.get_transaction_count(owner_account.address),
        "gasPrice": 21000,
    })

    signed_transaction = web3.eth.account.sign_transaction(transaction, private_key)
    transaction_hash = web3.eth.send_raw_transaction(signed_transaction.rawTransaction)
    receipt = web3.eth.wait_for_transaction_receipt(transaction_hash)

    database.session.commit()
    return Response(status=200)


if __name__ == "__main__":
    application.run(debug=True, host="0.0.0.0", port=5003)
