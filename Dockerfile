FROM python:3.7.6-alpine3.11

VOLUME /urlhaus_db
ADD ./ /urlhaus_db/
WORKDIR /urlhaus_db

RUN pip install -r requirements.txt

CMD ["python3", "downloader.py"]
