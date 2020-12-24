FROM python:alpine

WORKDIR /NCMBot

RUN apk update && apk add  --no-cache tzdata alpine-sdk libffi-dev git ca-certificates
ADD requirements.txt /tmp/
RUN pip3 install --no-cache-dir -r /tmp/requirements.txt && rm /tmp/requirements.txt
COPY . /NCMBot

ENV TZ=Asia/Shanghai




