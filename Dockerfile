FROM python:3.12.3-slim-bookworm

ARG BOT_NAME
ARG TIMEZONE

ENV BOT_NAME=$BOT_NAME
ENV TZ=$TIMEZONE

WORKDIR /usr/src/app/"${BOT_NAME}"

RUN ln -sf /usr/share/zoneinfo/"${TZ}" /etc/localtime
RUN apt-get update -y && apt-get install -y gcc

COPY requirements.txt /usr/src/app/"${BOT_NAME}"
RUN pip install --upgrade pip
RUN pip install -r /usr/src/app/"${BOT_NAME}"/requirements.txt

COPY . /usr/src/app/"${BOT_NAME}"