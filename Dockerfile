FROM python:3.7-alpine3.11

VOLUME /urlhaus_db

ADD ./src /urlhaus_db/
ADD ./requirements.txt /urlhaus_db/

WORKDIR /urlhaus_db

RUN pip install -r requirements.txt

CMD ["python", "downloader.py"]
