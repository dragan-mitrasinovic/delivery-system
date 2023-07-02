import csv
import io
import os

import requests
from flask import Flask, request, make_response, jsonify, Response
from flask_jwt_extended import JWTManager

from configuration import Configuration
from models import Product, ProductInCategory, Category, database
from role_check import role_check

application = Flask(__name__)
application.config.from_object(Configuration)

jwt = JWTManager(application)

database.init_app(application)

STATISTICS_SERVER_URL = os.environ["STATISTICS_SERVER_URL"]


@application.route("/update", methods=["POST"])
@role_check("owner")
def update():
    if not request.files.get("file", None):
        return make_response(jsonify(message="Field file is missing."), 400)

    content = request.files["file"].stream.read().decode("utf-8")
    stream = io.StringIO(content)
    reader = csv.reader(stream)

    products = set([product.name for product in Product.query.all()])
    categories = set([category.name for category in Category.query.all()])
    new_categories = []
    products_in_categories = []
    line = 0
    for row in reader:
        if len(row) != 3:
            database.session.rollback()
            return make_response(jsonify(message=f"Incorrect number of values on line {line}."), 400)

        try:
            price = float(row[2])
            if price <= 0:
                database.session.rollback()
                return make_response(jsonify(message=f"Incorrect price on line {line}."), 400)
        except ValueError:
            database.session.rollback()
            return make_response(jsonify(message=f"Incorrect price on line {line}."), 400)

        name = row[1]
        if name in products:
            database.session.rollback()
            return make_response(jsonify(message=f"Product {name} already exists."), 400)

        product = Product(name=row[1], price=price, sold=0, waiting=0)
        database.session.add(product)
        products.add(row[1])

        for category in row[0].split('|'):
            if category not in categories:
                categories.add(category)
                new_categories.append(category)
            products_in_categories.append((product.name, category))
        line += 1

    categories = [Category(name=name) for name in new_categories]
    database.session.add_all(categories)
    database.session.commit()

    product_name_id = {}
    for product in Product.query.all():
        product_name_id[product.name] = product.id

    products_in_categories = [
        ProductInCategory(product_id=product_name_id[product_name], category_name=category_name)
        for product_name, category_name in products_in_categories
    ]
    database.session.add_all(products_in_categories)
    database.session.commit()
    return Response(status=200)


@application.route("/product_statistics", methods=["GET"])
@role_check("owner")
def product_statistics():
    resp = requests.get(f"http://{STATISTICS_SERVER_URL}:5004/product_statistics")
    return resp.text, resp.status_code, resp.headers.items()


@application.route("/category_statistics", methods=["GET"])
@role_check("owner")
def category_statistics():
    resp = requests.get(f"http://{STATISTICS_SERVER_URL}:5004/category_statistics")
    return resp.text, resp.status_code, resp.headers.items()


if __name__ == "__main__":
    application.run(debug=True, host="0.0.0.0", port=5001)
