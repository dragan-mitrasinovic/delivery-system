FROM python:3

RUN mkdir -p /opt/src/store_init
WORKDIR /opt/src/store_init

COPY store_init/configuration.py ./configuration.py
COPY store_init/init.py ./init.py
COPY store_init/requirements.txt ./requirements.txt
COPY models.py ./models.py

RUN pip install -r ./requirements.txt

ENTRYPOINT ["python", "./init.py"]