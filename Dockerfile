FROM alpine

MAINTAINER <boyko.cxx@gmail.com>

RUN apk update && apk upgrade

RUN apk add python python-dev py-pip
RUN pip install irc 

ADD loggi.py /bin/
ADD entrypoint.sh /

RUN chmod +x /bin/loggi.py
RUN chmod +x /entrypoint.sh

RUN adduser -S loggi

WORKDIR /home/loggi/

USER loggi

ENTRYPOINT ["/entrypoint.sh"]
