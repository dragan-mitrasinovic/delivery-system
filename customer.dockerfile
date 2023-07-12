FROM python:3

RUN mkdir -p /opt/src/customer
WORKDIR /opt/src/customer

COPY customer/configuration.py ./configuration.py
COPY customer/application.py ./application.py
COPY customer/requirements.txt ./requirements.txt
COPY models.py ./models.py
COPY role_check.py ./role_check.py
COPY keys.json ./keys.json
COPY solidity ./solidity

RUN pip install -r ./requirements.txt

ENTRYPOINT ["python", "./application.py"]