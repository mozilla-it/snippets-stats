FROM google/cloud-sdk:slim

COPY . /workspace/

WORKDIR /workspace

RUN mkdir /workspace/snippets-stats

RUN apt update && \
    apt install -y python3 python3-pip unixodbc-dev python3-dev && \
    apt clean

RUN pip3 install --upgrade --no-cache-dir .
