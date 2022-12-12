FROM python:3.10 

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y proj-bin