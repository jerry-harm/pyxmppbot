#!../.venv/bin/python
import inspect
import logging
import sys
from argparse import ArgumentParser
from getpass import getpass

from slixmpp import ClientXMPP
from slixmpp import JID
from slixmpp.stanza.message import Message
from slixmpp.types import MessageTypes

from admin_handler import AdminHandler
from usr_handler import UserHandler


class Bot(ClientXMPP):

    def __init__(self, jid, password, room, nick="AFM"):
        ClientXMPP.__init__(self, jid, password)

        self.room = JID(room)
        self.nick = nick
        self.user_handler = UserHandler(self)
        self.admin_handler = AdminHandler(self)

        self.add_event_handler("session_start", self.start)
        self.add_event_handler("message", self.message)
        self.add_event_handler("groupchat_message", self.muc_message)
        self.add_event_handler("groupchat_direct_invite", self.invited)
        # If you wanted more functionality, here's how to register plugins:
        self.register_plugin('xep_0030')  # Service Discovery
        self.register_plugin('xep_0313')  # mam
        # self.register_plugin('xep_0199') # XMPP Ping

        self.register_plugin('xep_0045')  # muc plugin
        self.register_plugin('xep_0249')  # muc invite
        self.register_plugin('xep_0066')  # my out of band

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
        test if a msg is from room and an
        :param msg:
        :return: bool
        """
        moderators = await self.plugin['xep_0045'].get_roles_list(JID(msg['from'].bare), role='moderator')
        print(moderators)
        if self.nick in moderators:
            # Bot is admin
            if msg['from'].resource in moderators:
                return True
            else:
                self.send_message(msg['from'].bare, "not admin", mtype='groupchat')
                return False
        else:
            self.send_message(msg['from'].bare, "I'm not admin", mtype='groupchat')
            return False

    async def resolve_muc_admin_cmd(self, msg: Message):
        """
        resolve the admin cmd
        :param msg:
        :return:
        """
        cmd = msg['body'].split(' ')
        # 怎么来的怎么回去
        mtype: MessageTypes = msg['type']
        if msg['type'] == 'groupchat':
            re_jid = msg['from'].bare
        else:
            re_jid = msg['from']
        right_called = False
        for i in cmd:
            if i in self.admin_handler.cmds:
                right_called = True
                if inspect.iscoroutinefunction(self.admin_handler.cmds[i][0]):
                    await self.admin_handler.cmds[i][0](
                        re_jid=re_jid, mtype=mtype,
                        args=cmd[cmd.index(i):])
                else:
                    self.admin_handler.cmds[i][0](
                        re_jid=re_jid, mtype=mtype,
                        args=cmd[cmd.index(i):])
            if not right_called:
                self.send_message(re_jid, mtype=mtype, mbody="""
                    输入参数无效或为输入参数，请输入 {} ADMIN help 来获取帮助
                    """.format(self.nick))

    async def resolve_muc_usr_cmd(self, msg: Message):
        """
        handel user's cmd
        :param msg:
        :return:
        """
        cmd: list = msg['body'].split(' ')
        # 怎么来的怎么回去
        mtype: MessageTypes = msg['type']
        if msg['type'] == 'groupchat':
            re_jid = msg['from'].bare
        else:
            re_jid = msg['from']
        right_called = False
        for i in cmd:
            if i in self.user_handler.cmds:
                right_called = True
                # 只调用一次
                if inspect.iscoroutinefunction(self.user_handler.cmds[i][0]):
                    await self.user_handler.cmds[i][0](re_jid=re_jid, mtype=mtype,
                                                       args=cmd[cmd.index(i):])
                    break
                else:
                    self.user_handler.cmds[i][0](re_jid=re_jid, mtype=mtype,
                                                 args=cmd[cmd.index(i):])
                    break
        if not right_called:
            self.send_message(re_jid, mtype=mtype, mbody="""
                输入参数无效或为输入参数，请输入 {} help 来获取帮助
                """.format(self.nick))

    async def resolve_chat(self, msg: Message):
        """
        普通私信处理,现在用不上，直接给到muc处理
        :param msg:
        :return:
        """
        await self.resolve_muc_usr_cmd(msg)

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
                if 'ADMIN' in msg['body']:
                    if self.confirm_room_admin(msg):
                        await self.resolve_muc_admin_cmd(msg)
                else:
                    await self.resolve_muc_usr_cmd(msg)
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
        if msg['mucnick'] != self.nick and self.nick in msg['body']:
            if 'ADMIN' in msg['body']:
                if await self.confirm_room_admin(msg):
                    await self.resolve_muc_admin_cmd(msg)
            else:
                await self.resolve_muc_usr_cmd(msg)


if __name__ == '__main__':
    if sys.platform == 'win32':
        import asyncio

        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    # Set up the command line arguments.
    parser = ArgumentParser()
    parser.add_argument("-q", "--quiet", help="set logging to ERROR",
                        action="store_const",
                        dest="loglevel",
                        const=logging.ERROR,
                        default=logging.INFO)
    parser.add_argument("-d", "--debug", help="set logging to DEBUG",
                        action="store_const",
                        dest="loglevel",
                        const=logging.DEBUG,
                        default=logging.INFO)

    # JID and password options.
    parser.add_argument("-j", "--jid", dest="jid",
                        help="JID to use")
    parser.add_argument("-p", "--password", dest="password",
                        help="password to use")
    parser.add_argument("-r", "--room", dest="room",
                        help="room to join")
    parser.add_argument("-n", "--nick", dest="nick",
                        help="nick to use")

    argsg = parser.parse_args()

    # Setup logging.
    logging.basicConfig(level=argsg.loglevel,
                        format='%(levelname)-8s %(message)s')

    if argsg.jid is None:
        argsg.jid = input("Username: ")
    if argsg.password is None:
        argsg.password = getpass("Password: ")
    if argsg.nick is None:
        argsg.nick = getpass("nick: ")

    xmpp = Bot(argsg.jid, argsg.password, argsg.room, argsg.nick)
    xmpp.connect()
    xmpp.process()
