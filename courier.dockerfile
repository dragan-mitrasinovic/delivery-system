FROM python:3

RUN mkdir -p /opt/src/courier
WORKDIR /opt/src/courier

COPY courier/configuration.py ./configuration.py
COPY courier/application.py ./application.py
COPY courier/requirements.txt ./requirements.txt
COPY models.py ./models.py
COPY role_check.py ./role_check.py

RUN pip install -r ./requirements.txt

ENTRYPOINT ["python", "./application.py"]