FROM python:alpine

WORKDIR /NCMBot
RUN apk update && apk add tzdata alpine-sdk libffi-dev git ca-certificates  --no-cache&& \
git clone https://github.com/tgbot-collection/NCMBot /NCMBot && cd /NCMBot &&\
pip install --no-cache-dir -r requirements.txt

ENV TZ=Asia/Shanghai




