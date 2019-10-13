#!/usr/bin/python -u

'''
boyko.cxx@gmail.com
Oct 2019
MIT License

Loggi is a simple logging bot for a small IRC server, written to keep channel history
on my home ngIRCd.

The bot is controlled by sending privmsg with commands to it (/msg <bot-nick> <command>).
The following commands are available:

join <channel>                | join the channel
part <channel>                | part from the channel
log <channel>                 | get logging status - returns 'enabled'/'disabled'
log <channel> set_enabled     | enable logging on channel
log <channel> set_disabled    | disable logging on channel
log <channel> length          | get max number of logged messages for channel, if no such limit - returns empty message
log <channel> length <number> | set max number of logged messages for channel
log <channel> read            | get logged messages in channel
log <channel> read <+-number> | get number of first/last logged messages in channel
log <channel> reset           | clear channel's log

NOTE per-channel logs (accessible through the /msg interface) are sotred in-memory.
NOTE To use 'log' and 'part' commands for a channel, you should be present on that channel

The interface is a bit raw/wordy/inconvenient, but I beleive user can handle it by
defining macroses on his client.

Logs are printed to stdout, so users can make further processing by attaching
to it (or just redirrect to /dev/null)
'''

#TODO add tests
#XXX tls cert verification

import irc
import irc.bot
import ssl
import time
import sys

#####################################################

class BotUsageException(Exception):
    ''' >:-( usage/abuse etc commited by users '''

def trim(list_of_str):
    return [s.strip() for s in list_of_str if s.strip()]

def unpack(args, defaults, min_args_len = 1):
    assert len(defaults) >= min_args_len

    if len(args) > len(defaults) or len(args) < min_args_len:
        raise BotUsageException("invalid number of arguments: %d" % len(args))

    return list(args) + defaults[len(args):]

#####################################################

log_channels = {}

class ChanLog:
    def __init__(self):
        self.is_enabled = False
        self.length_limit = None
        self.log = []

def channel_is_enabled(ch):
    return ch in log_channels and log_channels[ch].is_enabled

def channel_enable(ch):
    if not channel_is_enabled(ch):
        log_channels[ch] = ChanLog()
        log_channels[ch].is_enabled = True

def channel_disable(ch):
    if channel_is_enabled(ch):
        log_channels[ch].is_enabled = False

def channel_reset(ch):
    if ch in log_channels:
        log_channels[ch].log = []

def channel_log_length(ch):
    if ch in log_channels:
        return log_channels[ch].length_limit
    return None

def channel_log_length_set(ch, limit):
    if ch not in log_channels:
        log_channels[ch] = ChanLog()
    log_channels[ch].length_limit = limit
    log_channels[ch].log = log_channels[ch].log[-limit:]

def channel_log(ch, l):
    c = log_channels[ch]
    c.log.append(l)

    if c.length_limit != None and len(c.log) > c.length_limit:
        c.log.pop(0)

def channel_log_get(ch, begin = None, end = None):
    if ch in log_channels:
        return log_channels[ch].log[begin:end]
    return []

#####################################################

def is_src_on_channel(ch, src):
    src_nick = irc.client.NickMask(src).nick

    if ch not in bot.channels:
        return None
    if not bot.channels[ch].has_user(src_nick):
        return False
    return True

def cmd_channel_log_read(c, ch, reader, linenum):
    if linenum != None:
        try:
            linenum = int(linenum)
        except: raise BotUsageException("invalid 'linenum' argument: should be 'int'")

    for l in channel_log_get(ch, linenum):
        c.privmsg(reader, l)

def cmd_channel_log_length(c, ch, resp_dst, new_length):
    if new_length == None:
        l = channel_log_length(ch)
        c.privmsg(resp_dst, str(l) if l != None else '')
        return

    try:
        new_length = int(new_length)
    except: raise BotUsageException("invalid 'new_length' argument: should be 'int'")

    channel_log_length_set(ch, new_length)

def cmd_join(c, src, args):
    channel, password = unpack(args, [None, None])
    c.join(channel, password)

def cmd_part(c, src, args):
    channel, bye = unpack(args, [None, None])

    if not is_src_on_channel(channel, src):
        raise BotUsageException("to use the command '%s' should be on the channel '%s'" % (src, channel))

    c.part(channel, bye)

def cmd_log(c, src, args):
    channel, action, arg = unpack(args, [None, '', None])

    if not is_src_on_channel(channel, src):
        raise BotUsageException("to use the command '%s' should be on the channel '%s'" % (src, channel))

    action = action.lower()

    if action == '':
        c.privmsg(src, "enabled" if channel_is_enabled(channel) else "disabled")
    elif action == 'set_enabled':
        channel_enable(channel)
    elif action == 'set_disabled':
        channel_disable(channel)
    elif action == 'reset':
        channel_reset(channel)
    elif action == 'read':
        cmd_channel_log_read(c, channel, src, arg)
    elif action == 'length':
        cmd_channel_log_length(c, channel, src, arg)
    else:
        raise BotUsageException("invalid action: %s" % action)

#####################################################

class BotCmd:
    def __init__(self, cb, description):
        self.cb = cb
        self.desc = description

cmds = {
    "join" : BotCmd(cmd_join, 'join <channel> [password]') ,
    "part" : BotCmd(cmd_part, 'part <channel> [bye-message]'),
    "log" : BotCmd(cmd_log, 'log <channel> [action] [action-arg]'),
}

def on_privmsg(connection, event):
    src = event.source
    msg = event.arguments[0]
    msg = trim(msg.split())

    if len(msg) == 0:
        return

    cmd = msg[0]
    if cmd not in cmds:
        connection.privmsg(src, "'%s' invalid command" % cmd)
        return

    cmd_obj = cmds[cmd.lower()]

    try:
        cmd_obj.cb(connection, src, msg[1:])
    except BotUsageException as e:
        connection.privmsg(src, "%s (%s)" % (cmd_obj.desc, e))
        return

def on_channel_msg(connection, event):
    src = event.source
    channel = event.target
    msg = event.arguments[0]

    if channel_is_enabled(channel):
        log = u'[%s]%s: %s' % (time.time(), src, msg)
        channel_log(channel, log)

        log = u'[%s]%s>%s: %s' % (time.time(), src, channel, msg)
        print log

#####################################################

class ArgsChanDesc:
    def __init__(self):
       self.name = None
       self.key = None
       self.log_enable = False
       self.log_length = None

def cli_args_chan_str2desc(chan_str):
    def validate(p, v, t=None, v_whitelist=None):
        if v != None and t != None:
            try: v = t(v)
            except Exception as e:
                raise BotUsageException("invalid '%s' value '%s'" % (p, v))

        if callable(v_whitelist):
            if not v_whitelist(v):
                raise BotUsageException("invalid '%s' value '%s'" % (p, v))
        elif v_whitelist != None and v not in v_whitelist:
            raise BotUsageException("invalid '%s' value '%s'" % (p, v))

        return v

    c = ArgsChanDesc()

    for arg in trim(chan_str.split(',')):
        pv = trim(arg.split('='))
        p, v = unpack(pv, [None, None])

        if p == 'name':
            v = validate(p, v, str)
            c.name = v
        elif p == 'key':
            v = validate(p, v, str)
            c.key = v
        elif p == 'log':
            validate(p, v, None, [None])
            c.log_enable = True
        elif p == 'len':
            v = validate(p, v, int, lambda x: x > 0)
            c.log_length = v
        else:
            raise BotUsageException("invalid param '%s'" % p)

    if not c.name:
        raise BotUsageException("'name' param missed")

    return c

def cli_args_channels_parse(chans_str):
    chans = []

    for c in trim(chans_str.split(';')):
        chans.append(cli_args_chan_str2desc(c))

    return chans

def cli_args_parse():
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--server', required = True, help='IRC server IP address or domain name', type=str)
    parser.add_argument('-p', '--port', required = True, help='IRC server port', type=int, default=6667)
    parser.add_argument('-u', '--user', required = True, help='username on the IRC server', type=str)
    parser.add_argument('-k', '--key', help='user\'s key on the IRC server', type=str, default=None)

    parser.add_argument('-t', '--tls', help='use TLS for connection to IRC server', action='store_true', default=False)
    parser.add_argument('--tls-no-verify', help='use TLS for connection to IRC server (trust certificate)',
        action='store_true', default=False)
    parser.add_argument('-c', '--channels',  help="channels to autojoin and serve [,<parameter>[=<value>]]; example: 'name=#mychan,key=My123Pw2d,log,len=128;name=...'  ",
        type=str, default = '', dest='channels_str')

    parser.add_argument('--reconnection-interval', help='interval between reconnection attempts', type=int, default=60)

    args = parser.parse_args()

    try:
        args.channels = cli_args_channels_parse(args.channels_str)
    except BotUsageException as e:
        sys.exit("%s\nError parsing autojoin channel string: %s" % (parser.format_help(), e))

    return args

def join_channel(connection, channel):
    if channel.log_enable:
        channel_enable(channel.name)

    if channel.log_length != None:
        channel_log_length_set(channel.name, channel.log_length)

    connection.join(channel.name, channel.key)

def on_connect(connection, event):
    for channel in cli_args.channels:
        join_channel(connection, channel)

cli_args = cli_args_parse()

if cli_args.tls or cli_args.tls_no_verify:
    connect_factory = irc.connection.Factory(wrapper=ssl.wrap_socket)
else:
    connect_factory = irc.connection.Factory()

bot = irc.bot.SingleServerIRCBot(
        [(cli_args.server, cli_args.port, cli_args.key)],
        cli_args.user, cli_args.user,
        reconnection_interval = cli_args.reconnection_interval,
        connect_factory = connect_factory,
        username = cli_args.user)

# https://github.com/jbalogh/python-irclib/blob/master/irclib.py (numeric_events)
bot.connection.add_global_handler("welcome", on_connect)
bot.connection.add_global_handler("privmsg", on_privmsg)
bot.connection.add_global_handler("privnotice", on_privmsg)
bot.connection.add_global_handler("pubmsg", on_channel_msg)
bot.connection.add_global_handler("pubnotice", on_channel_msg)

try:
    bot.start()
except KeyboardInterrupt:
    pass
