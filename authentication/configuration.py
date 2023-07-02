from datetime import timedelta
import os

database_url = os.environ["DATABASE_URL"]


class Configuration:
    SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://root:root@{database_url}/authentication"
    JWT_SECRET_KEY = "SUPER_SECRET"
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
