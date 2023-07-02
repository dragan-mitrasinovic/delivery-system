FROM python:3

RUN mkdir -p /opt/src/authentication
WORKDIR /opt/src/authentication

COPY configuration.py ./configuration.py
COPY application.py ./application.py
COPY requirements.txt ./requirements.txt
COPY models.py ./models.py

RUN pip install -r ./requirements.txt

ENTRYPOINT ["python", "./application.py"]