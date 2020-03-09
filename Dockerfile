FROM python:3.7-alpine3.11

VOLUME /aquarium

ADD ./src /aquarium/
ADD ./requirements.txt /aquarium/

WORKDIR /aquarium

RUN apk add build-base \
  	    gcc \
	    postgresql-dev && \
    pip install -r requirements.txt

CMD ["python", "-u", "worker.py"]
