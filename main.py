#!../.venv/bin/python
import logging
import sys

from argparse import ArgumentParser
from getpass import getpass

from slixmpp import ClientXMPP
from slixmpp import JID
from slixmpp.stanza.message import Message
from slixmpp.types import MessageTypes

import get_img


class Bot(ClientXMPP):

    def __init__(self, jid, password, room, nick="AFM"):
        ClientXMPP.__init__(self, jid, password)

        self.room = JID(room)
        self.nick = nick

        self.add_event_handler("session_start", self.start)
        self.add_event_handler("message", self.message)
        self.add_event_handler("groupchat_message", self.muc_message)
        self.add_event_handler("groupchat_direct_invite", self.invited)
        # If you wanted more functionality, here's how to register plugins:
        self.register_plugin('xep_0030')  # Service Discovery
        # self.register_plugin('xep_0199') # XMPP Ping

        self.register_plugin('xep_0045')  # muc plugin
        self.register_plugin('xep_0249')  # muc invite
        self.register_plugin('xep_0066')  # my out of band

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

    async def resolve_admin_cmd(self, msg: Message):
        """
        resolve the admin cmd
        :param msg:
        :return:
        """
        cmd = msg['body'].split(' ')
        # 怎么来的怎么回去
        mtype: MessageTypes = msg['type']
        if (msg['type'] == 'groupchat'):
            re_jid = msg['from'].bare
        else:
            re_jid = msg['from']

        if '获取JID' in cmd:
            nick_to_search = cmd[cmd.index('获取JID') + 1]
            self.send_message(mto=re_jid,
                              mbody=self.plugin['xep_0045'].get_jid_property(re_jid, nick_to_search,
                                                                             'jid'),
                              mtype=mtype
                              )
        if '获得聊天室设置' in cmd:
            self.send_message(mto=re_jid,
                              mbody=str(await self.plugin['xep_0045'].get_room_config(re_jid)),
                              mtype=mtype
                              )
        if '驱逐' in cmd:
            jid_to_outcast = JID(cmd[cmd.index('驱逐') + 1])

            if jid_to_outcast.bare != self.jid:
                await self.plugin['xep_0045'].set_affiliation(re_jid, 'outcast', jid=jid_to_outcast)
                self.send_message(
                    mto=re_jid,
                    mbody='驱逐 %s ' % jid_to_outcast,
                    mtype=mtype
                )
        if '设置从属关系' in cmd:
            nick_to_set = cmd[cmd.index('设置从属关系') + 1]
            nick_set_to = cmd[cmd.index('设置从属关系') + 2]
            if nick_set_to not in ['member', 'admin', 'owner', 'none']:
                self.send_message(mto=re_jid,
                                  mbody='not an affiliation',
                                  mtype=mtype
                                  )
            else:
                await self.plugin['xep_0045'].set_affiliation(re_jid, nick_set_to, nick=nick_to_set)
                self.send_message(mto=re_jid,
                                  mbody='affiliation set done',
                                  mtype=mtype
                                  )

    def resolve_usr_cmd(self, msg: Message):
        """
        handel user's cmd
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
        if "色图" in cmd:
            body = get_img.api1()
            if not body:
                self.send_message(
                    mto=re_jid,
                    mbody="wrong",
                    mtype=mtype
                )
                return 0
            #             xml_tmp = """
            # <message xmlns="jabber:client" xml:lang="en" to="%s" type="%s" >
            #   <x xmlns="jabber:x:oob">
            #     <url>%s</url>
            # </x>
            #   <markable xmlns="urn:xmpp:chat-markers:0" />
            #   <body>%s</body>
            # </message>""" % (re_jid, mtype, body['url'], body['url'])
            #             self.send_xml(ET.XML(xml_tmp))
            msg=Message()
            msg['type'] = mtype
            msg['to'] = re_jid
            msg['body']=body['url']
            msg['oob']['url'] = body['url']
            self.send(msg)

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
                        await self.resolve_admin_cmd(msg)
                else:
                    self.resolve_usr_cmd(msg)
            else:
                # 普通私聊处理
                self.send_message(mto=msg['from'].bare,
                                  mbody="来自%s，你说%s" % (msg['from'], msg['body']),
                                  mtype="chat"
                                  )

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
                    await self.resolve_admin_cmd(msg)
            else:
                self.resolve_usr_cmd(msg)
                # self.send_message(mto=msg['from'].bare,
                #                   mbody="来自%s，你说%s" % (msg['from'], msg['body']),
                #                   mtype="groupchat"
                #                   )


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

    args = parser.parse_args()

    # Setup logging.
    logging.basicConfig(level=args.loglevel,
                        format='%(levelname)-8s %(message)s')

    if args.jid is None:
        args.jid = input("Username: ")
    if args.password is None:
        args.password = getpass("Password: ")
    if args.nick is None:
        args.nick = getpass("nick: ")

    xmpp = Bot(args.jid, args.password, args.room, args.nick)
    xmpp.connect()
    xmpp.process()
