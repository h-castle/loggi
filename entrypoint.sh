#!/bin/sh

if [ "$LOGGI_TLS" != "" ]
then
    TLS=--tls
fi

if [ "$LOGGI_TLS_NO_VERIFY" != "" ]
then
    TLS_NO_VERIFY=--tls-no-verify
fi

if [ "$LOGGI_RECONNECTION_INTERVAL" != "" ]
then
    RECONNECTION_INTERVAL="--reconnection-interval $LOGGI_RECONNECTION_INTERVAL"
fi

if [ "$LOGGI_NICK" != "" ]
then
    NICK="-n $LOGGI_NICK"
fi

if [ "$LOGGI_REALNAME" != "" ]
then
    REALNAME="-r $LOGGI_REALNAME"
fi

loggi.py -s $LOGGI_SERVER -p $LOGGI_PORT -u $LOGGI_USER -k $LOGGI_KEY -c $LOGGI_CHANNELS \
    $TLS $TLS_NO_VERIFY $RECONNECTION_INTERVAL $NICK $REALNAME
