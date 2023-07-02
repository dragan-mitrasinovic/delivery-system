FROM python:3

RUN mkdir -p /opt/src/owner
WORKDIR /opt/src/owner

COPY owner/configuration.py ./configuration.py
COPY owner/application.py ./application.py
COPY owner/requirements.txt ./requirements.txt
COPY models.py ./models.py
COPY role_check.py ./role_check.py

RUN pip install -r ./requirements.txt

ENTRYPOINT ["python", "./application.py"]