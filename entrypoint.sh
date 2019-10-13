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

loggi.py -s $LOGGI_SERVER -p $LOGGI_PORT -u $LOGGI_USER -k $LOGGI_KEY -c $LOGGI_CHANNELS $TLS $TLS_NO_VERIFY $RECONNECTION_INTERVAL
