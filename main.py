#!../.venv/bin/python
import inspect
import logging
import re
import sys
from argparse import ArgumentParser
from getpass import getpass
import typing

from slixmpp import ClientXMPP
from slixmpp import JID
from slixmpp.stanza.message import Message
from slixmpp.types import MessageTypes


class Handler:
    def __init__(self, method: typing.Callable, description: str, user_admin: bool = False, self_admin: bool = False):
        self.method = method
        self.description = description
        self.user_admin = user_admin
        self.self_admin = self_admin

    async def __call__(self, cmd, msg: Message):
        try:
            if inspect.iscoroutinefunction(self.method):
                await self.method(cmd, msg)
            else:
                self.method(cmd, msg)
        except Exception:
            print('unknown error')

    def __str__(self):
        return self.description


class Bot(ClientXMPP):

    def __init__(self, jid:str, password:str, room:str, handlers: typing.Dict[str:Handler], default_handler: Handler, nick: str):
        ClientXMPP.__init__(self, jid, password)

        self.room = JID(room)
        self.nick = nick

        self.add_event_handler("session_start", self.start)
        self.add_event_handler("message", self.message)
        self.add_event_handler("groupchat_message", self.muc_message)
        self.add_event_handler("groupchat_direct_invite", self.invited)

        # If you wanted more functionality, here's how to register plugins:
        self.register_plugin('xep_0030')  # Service Discovery
        self.register_plugin('xep_0313')  # mam
        self.register_plugin('xep_0199')  # XMPP Ping

        self.register_plugin('xep_0045')  # muc plugin
        self.register_plugin('xep_0249')  # muc invite
        self.register_plugin('xep_0066')  # my out of band
        self.register_plugin('xep_0084')  # avatar

        self.handlers: typing.Dict[str, Handler] = handlers
        self.default_handler: Handler = default_handler

    # base
    def invited(self, msg: Message):
        """
        被邀请之后直接加入房间
        :param msg:
        :return:
        """
        self.plugin['xep_0045'].join_muc(msg['groupchat_invite']['jid'], self.nick)

    def confirm_from_room(self, msg: Message) -> bool:
        """
        test if the message is from muc
        :param msg:
        :return:
        """
        if msg['from'].bare in self.plugin['xep_0045'].get_joined_rooms():
            return True
        else:
            return False

    async def confirm_room_admin(self, msg: Message) -> bool:
        """
        confirm if usr in muc is admin
        :param msg:
        :return: bool
        """
        moderators = await self.plugin['xep_0045'].get_roles_list(JID(msg['from'].bare), role='moderator')
        if msg['from'].resource in moderators:
            return True
        else:
            self.send_message(msg['from'].bare, "you are not admin", mtype='groupchat')
            return False

    async def confirm_self_room_admin(self, msg: Message) -> bool:
        """
        confirm if self in muc is admin
        :param msg:
        :return: bool
        """
        moderators = await self.plugin['xep_0045'].get_roles_list(JID(msg['from'].bare), role='moderator')
        if self.nick in moderators:
            return True
        else:
            self.send_message(msg['from'].bare, "I'm not admin", mtype='groupchat')
            return False

    async def resolve_muc_cmd(self, msg: Message):
        """
        handler the admin cmd
        :param msg:
        :return:
        """
        cmd = re.split('\\s', msg['body'])
        # confirm called
        right_called = False

        for i in cmd:
            if i in self.handlers:
                # called
                right_called = True
                await self.handlers[i](cmd[cmd.index(i):], msg)
        if not right_called:
            if self.default_handler:
                await self.default_handler(cmd, msg)

    async def resolve_chat(self, msg: Message):
        """
        普通私信处理,现在用不上，直接给到muc处理
        :param msg:
        :return:
        """
        await self.resolve_muc_cmd(msg)

    async def start(self, event):
        """
        处理启动，启动时加入命令行指定的聊天室
        :param event:
        :return:
        """
        await self.get_roster()
        self.send_presence()
        if self.room:
            await self.plugin['xep_0045'].join_muc(self.room, self.nick)

    async def message(self, msg: Message):
        """
        私信处理
        :param msg:
        :return:
        """
        if msg['type'] in ('chat', 'normal'):
            msg.reply("Thanks for sending\n%s" % msg['body']).send()
            # 判断是否来自群聊
            if self.confirm_from_room(msg):
                await self.resolve_muc_cmd(msg)
            else:
                # 普通私聊处理
                await self.resolve_chat(msg)

    async def muc_message(self, msg: Message):
        """
        群聊处理
        :param msg:
        :return:
        """
        # 被提到
        if msg['mucnick'] != self.nick and self.nick in msg['body'] and ">" not in msg['body']:
            await self.resolve_muc_cmd(msg)
