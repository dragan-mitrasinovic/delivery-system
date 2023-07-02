import re
from email.utils import parseaddr

from flask import Flask, request, Response, jsonify, make_response
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from sqlalchemy import and_
from sqlalchemy.exc import IntegrityError
from sqlalchemy_utils import database_exists, create_database

from configuration import Configuration
from models import database, Role, User

application = Flask(__name__)
application.config.from_object(Configuration)

jwt = JWTManager(application)

database.init_app(application)
if not database_exists(Configuration.SQLALCHEMY_DATABASE_URI):
    create_database(Configuration.SQLALCHEMY_DATABASE_URI)

email_regex = re.compile(r"[a-zA-Z0-9_-]+@[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]{2,}")

with application.app_context():
    database.create_all()

    customer_role = Role.query.filter(Role.name == "customer").first()
    courier_role = Role.query.filter(Role.name == "courier").first()
    owner_role = Role.query.filter(Role.name == "owner").first()

    if customer_role is None:
        customer_role = Role(name="customer")
        database.session.add(customer_role)
    if courier_role is None:
        courier_role = Role(name="courier")
        database.session.add(courier_role)
    if owner_role is None:
        owner_role = Role(name="owner")
        database.session.add(owner_role)

    owner_account = User.query.filter(User.email == "onlymoney@gmail.com").first()
    if owner_account is None:
        database.session.add(
            User(email="onlymoney@gmail.com", password="evenmoremoney", forename="Scrooge",
                 surname="McDuck", roleId=owner_role.id)
        )

    database.session.commit()


@application.route("/register_customer", methods=["POST"])
def register_customer():
    return register("customer")


@application.route("/register_courier", methods=["POST"])
def register_courier():
    return register("courier")


@application.route("/login", methods=["POST"])
def login():
    email = request.json.get("email", "")
    password = request.json.get("password", "")

    if len(email) == 0:
        return make_response(jsonify(message="Field email is missing."), 400)
    if len(password) == 0:
        return make_response(jsonify(message="Field password is missing."), 400)

    email_valid = parseaddr(email)
    if len(email_valid[1]) == 0 or not re.fullmatch(email_regex, email):
        return make_response(jsonify(message="Invalid email."), 400)

    user = User.query.filter(and_(User.email == email, User.password == password)).first()
    if not user:
        return make_response(jsonify(message="Invalid credentials."), 400)

    additional_claims = {
        "forename": user.forename,
        "surname": user.surname,
        "role": user.role.name
    }
    access_token = create_access_token(identity=user.email, additional_claims=additional_claims)
    return make_response(jsonify(accessToken=access_token), 200)


@application.route("/delete", methods=["POST"])
@jwt_required()
def delete():
    email = get_jwt_identity()

    user = User.query.filter(User.email == email).first()
    if not user:
        return make_response(jsonify(message="Unknown user."), 400)

    database.session.delete(user)
    database.session.commit()
    return Response(status=200)


def register(role_name):
    email = request.json.get("email", "")
    password = request.json.get("password", "")
    forename = request.json.get("forename", "")
    surname = request.json.get("surname", "")

    if len(forename) == 0:
        return make_response(jsonify(message="Field forename is missing."), 400)
    if len(surname) == 0:
        return make_response(jsonify(message="Field surname is missing."), 400)
    if len(email) == 0:
        return make_response(jsonify(message="Field email is missing."), 400)
    if len(password) == 0:
        return make_response(jsonify(message="Field password is missing."), 400)

    email_valid = parseaddr(email)
    if len(email_valid[1]) == 0 or not re.fullmatch(email_regex, email):
        return make_response(jsonify(message="Invalid email."), 400)
    if len(password) < 8:
        return make_response(jsonify(message="Invalid password."), 400)

    role = Role.query.filter(Role.name == role_name).first()
    user = User(email=email, password=password, forename=forename, surname=surname, roleId=role.id)

    try:
        database.session.add(user)
        database.session.commit()
        return Response(status=200)
    except IntegrityError:
        return make_response(jsonify(message="Email already exists."), 400)


if __name__ == "__main__":
    application.run(debug=True, host="0.0.0.0", port=5000)
