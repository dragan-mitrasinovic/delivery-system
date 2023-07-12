import os

database_url = os.environ["DATABASE_URL"]
ethereum_url = os.environ["ETHEREUM_URL"]


class Configuration:
    SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://root:root@{database_url}/store"
    ETHEREUM_URI = f"http://{ethereum_url}:8545"
    JWT_SECRET_KEY = "SUPER_SECRET"
