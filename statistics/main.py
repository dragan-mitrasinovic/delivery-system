import json
import os
import subprocess

from flask import Flask, make_response, jsonify

application = Flask(__name__)


@application.route("/product_statistics", methods=["GET"])
def product_statistics():
    os.environ["SPARK_APPLICATION_PYTHON_LOCATION"] = "/app/statistics/product_statistics.py"
    os.environ["SPARK_SUBMIT_ARGS"] \
        = "--driver-class-path /app/mysql-connector-j-8.0.33.jar --jars /app/mysql-connector-j-8.0.33.jar"

    result = subprocess.check_output(["/template.sh"]).decode().split("!!!!!*****")[1]
    result = json.loads(result)
    return make_response(jsonify(statistics=result), 200)


@application.route("/category_statistics", methods=["GET"])
def category_statistics():
    os.environ["SPARK_APPLICATION_PYTHON_LOCATION"] = "/app/statistics/category_statistics.py"
    os.environ["SPARK_SUBMIT_ARGS"] \
        = "--driver-class-path /app/mysql-connector-j-8.0.33.jar --jars /app/mysql-connector-j-8.0.33.jar"

    result = subprocess.check_output(["/template.sh"]).decode().split("!!!!!*****")[1]
    result = json.loads(result)
    return make_response(jsonify(statistics=result), 200)


if __name__ == "__main__":
    application.run(debug=True, host="0.0.0.0", port=5004)
