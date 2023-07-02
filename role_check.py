from functools import wraps

from flask import make_response, jsonify
from flask_jwt_extended import verify_jwt_in_request, get_jwt


def role_check(role: object):
    def inner_role(function):
        @wraps(function)
        def decorator(*arguments, **keyword_arguments):
            verify_jwt_in_request()
            claims = get_jwt()
            if claims["role"] == role:
                return function(*arguments, **keyword_arguments)
            else:
                return make_response(jsonify(msg="Missing Authorization Header"), 401)

        return decorator

    return inner_role
