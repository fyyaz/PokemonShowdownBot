# The MIT License (MIT)
#
# Copyright (c) 2015 QuiteQuiet
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

from datetime import datetime, timedelta
import random
import re

class Message:
    def __init__(self, sent, msg):
        self.sent = sent
        self.msg = msg
    def replyFormat(self):
        return 'From {user}: {msg}'.format(user = self.sent, msg = self.msg)

class MessageDatabase:
    # Constant
    def NOTIFICATION_GAP(self): return timedelta(hours = 1)

    def __init__(self):
        self.messages = {}
        self.lastNotification = {}

    def pendingMessages(self, user):
        cnt = len(self.messages[user])
        return 'You have {nr} message{s} waiting for you.\nUse ~read [number] to get [number] of messages shown to you'.format(nr = cnt, s = 's' if cnt > 1 else '')
    def addMessage(self, to, sent, msg):
        if to not in self.messages: self.messages[to] = {}
        # Set last notification to something far in the past so it triggers the first time always
        if to not in self.lastNotification: self.lastNotification[to] = datetime(2015, 1, 1)
        if sent in self.messages[to]: return False

        self.messages[to][re.sub(r'[^a-zA-z0-9,]', '', sent).lower()] = Message(sent, msg)
        return True

    def getMessage(self, user):
        return self.removeRandomMessage(user).replyFormat()

    def getMessages(self, user, amnt):
        ''' This removes amnt number of messages from the message service '''

        # This can be super-spammy for users with a lot of pending messages
        # as they can opt to look at all at once
        reply = ''
        if amnt > len(self.messages[user]): amnt = len(self.messages[user])
        while amnt > 0:
            reply += self.getMessage(user) + ('\n' if amnt > 1 else '')
            amnt -= 1
        # Remove the user from the list if there's no messages left
        # and clear the last notification time
        if not self.messages[user]:
            self.messages.pop(user)
            self.lastNotification.pop(user)
        return reply

    def getAllMessages(self, user):
        ''' This gets and delete every message to this user from storage '''

        # No need to test for existance, this assumes a message exists
        # and usage should first test for existance.
        messages = self.removeAllMessages(user)
        combine = []
        for msg in messages:
            combine.append(messages[msg].replyFormat())
        return '\n'.join(combine)

    def shouldNotifyMessage(self, user):
        if self.hasMessage(user):
            now = datetime.now()
            if now - self.lastNotification[user] > self.NOTIFICATION_GAP():
                self.lastNotification[user] = now
                return True
        return False

    def hasMessage(self, user):
        return user in self.messages

    def alreadySentMessage(self, user, frm):
        return user in self.messages and frm in self.messages[user]

    def removeRandomMessage(self, to):
        return self.messages[to].pop(random.choice(list(self.messages[to].keys())), None)
    def removeMessage(self, to, frm):
        msg = self.messages[to].pop(frm, None)
        # If the user has no message left, clear the name entry
        if len(self.messages[to]) < 1: self.messages.pop(to)
        return msg

    # Unused but still supported
    def removeAllMessages(self, to):
        return self.messages.pop(to, None)

# Commands
def tell(bot, cmd, room, msg, user):
    notes = bot.usernotes
    if not msg: return 'You need to specify a user and a message to send in the format: [user], [message]', False
    msg = msg.split(',')
    to = bot.toId(msg[0])
    message = ','.join(msg[1:]).lstrip()
    if notes.alreadySentMessage(to, user.id): return 'You already have a message to this user waiting', False
    if not message: return 'You forgot a message', True
    if len(message) > 150: return 'Message is too long. Max limit is 150 characters', False
    notes.addMessage(to, user.name, message)
    return "I'll be sure to tell {user} that.".format(user = to), True

def read(bot, cmd, room, msg, user):
    notes = bot.usernotes
    if not notes.hasMessage(user.id): return 'You have no messages waiting', False
    if not msg:
        # If the user didn't speify any amount to return, give back a single message
        return notes.getMessages(user.id, 1), False
    if not msg.isdigit() and int(msg) < 1: return 'Please enter a whole, positive number', False
    return notes.getMessages(user.id, int(msg)), False

def untell(bot, cmd, room, msg, user):
    notes = bot.usernotes
    if not msg: return 'You need to specify a user to remove', False
    if not notes.hasMessage(msg): return 'This user has no waiting messages', False
    if not notes.removeMessage(msg, user.id): return 'You have no message to this user waiting', False
    return 'Message removed', True
