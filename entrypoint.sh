#!/bin/sh

if [ "$IRC_TLS" != "" ]
then
    TLS=--tls
fi

if [ "$IRC_TLS_NO_VERIFY" != "" ]
then
    TLS_NO_VERIFY=--tls-no-verify
fi

if [ "$IRC_RECONNECTION_INTERVAL" != "" ]
then
    RECONNECTION_INTERVAL="--reconnection-interval $IRC_RECONNECTION_INTERVAL"
fi

bot.py -s $IRC_SERVER -p $IRC_PORT -u $IRC_USER -k $IRC_KEY -c $IRC_CHANNELS $TLS $TLS_NO_VERIFY $RECONNECTION_INTERVAL
