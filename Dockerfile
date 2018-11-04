FROM ubuntu:xenial

RUN apt-get update &&\
    apt-get install -y \
    python3 \
    python3-pip

RUN pip3 install --upgrade pip

RUN mkdir /aws
WORKDIR /aws
COPY requirements.txt /aws/requirements.txt
RUN pip3 install -r requirements.txt

COPY aws.py /aws/aws.py

ENTRYPOINT ["python3", "/aws/aws.py"]
