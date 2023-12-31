import math
from datetime import datetime

from flask import Flask, request, make_response, jsonify, Response
from flask_jwt_extended import JWTManager, get_jwt_identity
from sqlalchemy import and_
from web3 import Web3, HTTPProvider, Account

from configuration import Configuration

web3 = Web3(HTTPProvider(Configuration.ETHEREUM_URI))

from configuration import Configuration
from models import database, ProductInCategory, Product, Order, ProductInOrder
from role_check import role_check

application = Flask(__name__)
application.config.from_object(Configuration)

jwt = JWTManager(application)

database.init_app(application)


def read_file(path):
    with open(path, "r") as file:
        return file.read()


@application.route("/search", methods=["GET"])
@role_check("customer")
def search():
    name = request.args.get("name", "")
    category = request.args.get("category", "")

    categories_rows = ProductInCategory.query.join(Product) \
        .with_entities(ProductInCategory.category_name) \
        .filter(and_(ProductInCategory.category_name.like(f"%{category}%"), Product.name.like(f"%{name}%"))) \
        .group_by(ProductInCategory.category_name) \
        .all()
    categories = [
        row.category_name
        for row in categories_rows
    ]

    product_categories = {product.id: product.categories for product in Product.query.all()}
    products_rows = ProductInCategory.query.join(Product) \
        .with_entities(Product.id, Product.name, Product.price) \
        .filter(and_(ProductInCategory.category_name.like(f"%{category}%"), Product.name.like(f"%{name}%"))) \
        .group_by(Product.id) \
        .all()

    products = [
        {"categories": [cat.name for cat in product_categories[row.id]],
         "id": row.id, "name": row.name, "price": row.price}
        for row in products_rows
    ]

    return make_response(jsonify(categories=categories, products=products), 200)


@application.route("/order", methods=["POST"])
@role_check("customer")
def order_products():
    requests = request.json.get("requests", None)
    if not requests:
        return make_response(jsonify(message="Field requests is missing."), 400)

    total_price = 0
    email = get_jwt_identity()
    products_in_order = []
    products = {product.id: product for product in Product.query.all()}
    for i, req in enumerate(requests):
        product_id = req.get("id", None)
        quantity = req.get("quantity", None)

        if not product_id:
            database.session.rollback()
            return make_response(jsonify(message=f"Product id is missing for request number {i}."), 400)
        if not quantity:
            database.session.rollback()
            return make_response(jsonify(message=f"Product quantity is missing for request number {i}."), 400)

        try:
            product_id = int(product_id)
            if product_id <= 0:
                database.session.rollback()
                return make_response(jsonify(message=f"Invalid product id for request number {i}."), 400)
        except ValueError:
            database.session.rollback()
            return make_response(jsonify(message=f"Invalid product id for request number {i}."), 400)

        try:
            quantity = int(quantity)
            if quantity <= 0:
                database.session.rollback()
                return make_response(jsonify(message=f"Invalid product quantity for request number {i}."), 400)
        except ValueError:
            database.session.rollback()
            return make_response(jsonify(message=f"Invalid product quantity for request number {i}."), 400)

        if product_id not in products:
            database.session.rollback()
            return make_response(jsonify(message=f"Invalid product for request number {i}."), 400)

        products_in_order.append((product_id, quantity))

        total_price += quantity * products[product_id].price

        products[product_id].waiting += quantity
        database.session.add(products[product_id])

    address = request.json.get("address", None)
    if not address:
        database.session.rollback()
        return make_response(jsonify(message="Field address is missing."), 400)

    if not web3.is_address(address):
        database.session.rollback()
        return make_response(jsonify(message="Invalid address."), 400)

    order = Order(total_price=total_price, status="CREATED", created_on=datetime.now().isoformat(), email=email)
    database.session.add(order)
    database.session.flush()
    for product_id, quantity in products_in_order:
        database.session.add(ProductInOrder(product_id=product_id, order_id=order.id, quantity=quantity))

    address = web3.to_checksum_address(address)

    with open("keys.json", "r") as file:
        private_key = Account.decrypt(file.read(), "iepblockchain").hex()

    owner_account = Account.from_key(private_key)

    bytecode = read_file("solidity/order.bin")
    abi = read_file("solidity/order.abi")
    contract = web3.eth.contract(bytecode=bytecode, abi=abi)

    transaction = contract.constructor(address, math.ceil(order.total_price)).build_transaction({
        "from": owner_account.address,
        "nonce": web3.eth.get_transaction_count(owner_account.address),
        "gasPrice": 21000
    })

    signed_transaction = web3.eth.account.sign_transaction(transaction, private_key)
    transaction_hash = web3.eth.send_raw_transaction(signed_transaction.rawTransaction)
    receipt = web3.eth.wait_for_transaction_receipt(transaction_hash)

    order.contract_address = receipt.contractAddress

    database.session.commit()
    return make_response(jsonify(id=order.id), 200)


@application.route("/status", methods=["GET"])
@role_check("customer")
def status():
    product_quantities = {(pio.product_id, pio.order_id): pio.quantity for pio in ProductInOrder.query.all()}
    order_rows = Order.query.filter(Order.email == get_jwt_identity()).all()
    orders = [
        {"products":
             [{"categories": [category.name for category in product.categories],
               "name": product.name, "price": product.price, "quantity": product_quantities[(product.id, row.id)]}
              for product in row.products
              ],
         "price": row.total_price, "status": row.status, "timestamp": row.created_on.isoformat()}
        for row in order_rows
    ]
    return make_response(jsonify(orders=orders), 200)


@application.route("/delivered", methods=["POST"])
@role_check("customer")
def delivered():
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
    if not order or order.status != "PENDING":
        return make_response(jsonify(message="Invalid order id."), 400)

    order.status = "COMPLETE"
    database.session.add(order)

    quantities = {
        pio.product_id: pio.quantity
        for pio in ProductInOrder.query.filter(ProductInOrder.order_id == order.id).all()
    }

    for product in order.products:
        product.waiting -= quantities[product.id]
        product.sold += quantities[product.id]
    database.session.add_all(order.products)

    keys = request.json.get("keys", None)
    if not keys:
        database.session.rollback()
        return make_response(jsonify(message="Missing keys."), 400)

    passphrase = request.json.get("passphrase", "")
    if len(passphrase) == 0:
        database.session.rollback()
        return make_response(jsonify(message="Missing passphrase."), 400)

    try:
        keys = keys.replace("'", '"')
        private_key = Account.decrypt(keys, passphrase)
    except ValueError:
        database.session.rollback()
        return make_response(jsonify(message="Invalid credentials."), 400)

    address = web3.eth.account.from_key(private_key).address

    abi = read_file("solidity/order.abi")
    contract = web3.eth.contract(address=order.contract_address, abi=abi)

    if contract.functions.customer().call() != address:
        database.session.rollback()
        return make_response(jsonify(message="Invalid customer account."), 400)

    try:
        transaction = contract.functions.distributeFunds().build_transaction({
            "from": address,
            "nonce": web3.eth.get_transaction_count(address),
            "gasPrice": 21000
        })

        signed_transaction = web3.eth.account.sign_transaction(transaction, private_key)
        transaction_hash = web3.eth.send_raw_transaction(signed_transaction.rawTransaction)
        receipt = web3.eth.wait_for_transaction_receipt(transaction_hash)

    except ValueError as e:
        database.session.rollback()
        return make_response(jsonify(message=e), 400)

    database.session.commit()
    return Response(status=200)


@application.route("/pay", methods=["POST"])
@role_check("customer")
def pay():
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
    if not order:
        return make_response(jsonify(message="Invalid order id."), 400)

    keys = request.json.get("keys", None)
    if not keys:
        database.session.rollback()
        return make_response(jsonify(message="Missing keys."), 400)

    passphrase = request.json.get("passphrase", "")
    if len(passphrase) == 0:
        database.session.rollback()
        return make_response(jsonify(message="Missing passphrase."), 400)

    try:
        private_key = Account.decrypt(keys, passphrase)
    except ValueError:
        database.session.rollback()
        return make_response(jsonify(message="Invalid credentials."), 400)

    address = web3.eth.account.from_key(private_key).address

    abi = read_file("solidity/order.abi")
    contract = web3.eth.contract(address=order.contract_address, abi=abi)

    if contract.functions.paid().call():
        database.session.rollback()
        return make_response(jsonify(message="Transfer already complete."), 400)

    try:
        transaction = contract.functions.payOrder().build_transaction({
            "from": address,
            "nonce": web3.eth.get_transaction_count(address),
            "gasPrice": 21000,
            "value": math.ceil(order.total_price)
        })

        signed_transaction = web3.eth.account.sign_transaction(transaction, private_key)
        transaction_hash = web3.eth.send_raw_transaction(signed_transaction.rawTransaction)
        receipt = web3.eth.wait_for_transaction_receipt(transaction_hash)
    except ValueError as e:
        database.session.rollback()
        return make_response(jsonify(message=e), 400)

    return Response(status=200)


if __name__ == "__main__":
    application.run(debug=True, host="0.0.0.0", port=5002)
