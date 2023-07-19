FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=Etc/UTC
RUN apt-get update && apt-get -y install python3 python3-pip
RUN pip install cisco-gnmi

COPY ./ /

ENV PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION=python

CMD python3 run.py --host ${TARGET_HOST:=localhost}
