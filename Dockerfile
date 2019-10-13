FROM alpine

MAINTAINER <boyko.cxx@gmail.com>

RUN apk update && apk upgrade

RUN apk add python python-dev py-pip
RUN pip install irc 

ADD bot.py /bin/
ADD entrypoint.sh /

RUN chmod +x /bin/bot.py
RUN chmod +x /entrypoint.sh

RUN adduser -S bot 

WORKDIR /home/bot/

USER bot

ENTRYPOINT ["/entrypoint.sh"]
