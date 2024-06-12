#!../.venv/bin/python
import inspect
import logging
import random
import sys
from argparse import ArgumentParser
from collections import defaultdict
from getpass import getpass

from slixmpp import ClientXMPP
from slixmpp import JID
from slixmpp.stanza.message import Message
from slixmpp.types import MessageTypes

import get_api


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
        self.register_plugin('xep_0313')  # mam
        # self.register_plugin('xep_0199') # XMPP Ping

        self.register_plugin('xep_0045')  # muc plugin
        self.register_plugin('xep_0249')  # muc invite
        self.register_plugin('xep_0066')  # my out of band
        self.cmds = {
            "help": [self.show_functions, 0, "显示所有命令"],
            "色图": [self.send_img, 0, "随机动漫色图"],
            "写真": [self.send_img, 0, "随机写真"],
            "龙图": [self.send_img, 0, "随机龙图"],
            "QQ": [self.qq_information, 1, "获取一个qq号的头像和邮箱"],
            "随机数": [self.send_random, 2, "获得输入两数间的随机数"],
            "统计": [self.stats_mam, 1, "获取n条内发言次数统计，请不要超过500条"]
        }
        self.admin_cmd = {"获取JID": [self.get_jid, 1, "管理员获取JID"],
                          "help": [self.admin_help, 0, "管理员帮助"],
                          "驱逐": [self.outcast, 1, "驱逐一个JID"],
                          '设置从属关系': [self.set_aff, 2, "设置一个nick的从属关系"]
                          }

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
        for i in cmd:
            if i in self.admin_cmd:
                if inspect.iscoroutinefunction(self.admin_cmd[i][0]):
                    self.admin_cmd[i][0](re_jid=re_jid, mtype=mtype,
                                         args=cmd[cmd.index(i):cmd.index(i) + self.admin_cmd[i][1] + 1])

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

        for i in cmd:
            if i in self.cmds:
                if inspect.iscoroutinefunction(self.cmds[i][0]):
                    await self.cmds[i][0](re_jid=re_jid, mtype=mtype,
                                          args=cmd[cmd.index(i):cmd.index(i) + self.cmds[i][1] + 1])
                else:
                    self.cmds[i][0](re_jid=re_jid, mtype=mtype,
                                    args=cmd[cmd.index(i):cmd.index(i) + self.cmds[i][1] + 1])

    async def resolve_chat(self, msg: Message):
        """
        普通私信处理
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

    # user
    def send_img(self, re_jid, mtype, args):
        url = random.choice(get_api.apis[args[0]])()
        if not url:
            self.send_message(
                mto=re_jid,
                mbody="wrong",
                mtype=mtype
            )
            return 0
        msg = Message()
        msg['type'] = mtype
        msg['to'] = re_jid
        msg['body'] = url
        msg['oob']['url'] = url
        self.send(msg)
        self.send_message(mto=re_jid, mbody=url, mtype=mtype)

    def show_functions(self, re_jid, mtype, args):
        res = ""
        for k, d in self.cmds.items():
            res = res + "{} : {},需要{}个参数\n".format(k, d[2], d[1])
        self.send_message(mto=re_jid, mbody=res, mtype=mtype)

    def qq_information(self, re_jid, mtype, args):
        try:
            res = get_api.qq_json(args[1])
            if res:
                self.send_message(mtype=mtype, mto=re_jid,
                                  mbody="头像：{}\n邮箱：{}".format(res["touxiang"], res["email"]))
                msg = Message()
                msg['type'] = mtype
                msg['to'] = re_jid
                msg['body'] = res['touxiang']
                msg['oob']['url'] = res['touxiang']
                self.send(msg)
            else:
                self.send_message(mbody="调用出错", mtype=mtype, mto=re_jid)
        except IndexError:
            self.send_message(re_jid, '没有输入', mtype=mtype)

    def send_random(self, re_jid, mtype, args):
        try:
            res = random.randint(int(args[1]), int(args[2]))
            self.send_message(mto=re_jid, mbody=str(res), mtype=mtype)
        except TypeError:
            self.send_message(mto=re_jid, mbody='不是两个数', mtype=mtype)
        except IndexError:
            self.send_message(re_jid, '没有输入', mtype=mtype)
        except ValueError:
            self.send_message(re_jid, '范围出错', mtype=mtype)

    async def stats_mam(self, re_jid, mtype, args):
        try:
            num = int(args[1])
            mam = self.plugin['xep_0313'].iterate(re_jid.bare, total=num, reverse=True)
            res = defaultdict(int)
            async for m in mam:
                res[m['mam_result']['forwarded']['message']['from'].resource] += 1
            res_str = '在最近的{}以内条中：\n'.format(num)
            for nick, times in res.items():
                res_str += '{}:{}次 '.format(nick, times)
            self.send_message(re_jid, mbody=res_str, mtype=mtype)
        except IndexError:
            self.send_message(re_jid, mbody='请输入条数', mtype=mtype)
        except TypeError:
            self.send_message(re_jid, mbody='输入的不是数！', mtype=mtype)

    # admin
    def get_jid(self, re_jid, mtype, args):
        try:
            nick_to_search = args[1]
            self.send_message(mto=re_jid,
                              mbody=self.plugin['xep_0045'].get_jid_property(re_jid, nick_to_search,
                                                                             'jid'),
                              mtype=mtype
                              )
        except IndexError:
            self.send_message(re_jid, '没有输入', mtype=mtype)

    def admin_help(self, re_jid, mtype, args):
        res = ""
        for k, d in self.admin_cmd.items():
            res = res + "{} : {},需要{}个参数\n".format(k, d[2], d[1])
        self.send_message(mto=re_jid, mbody=res, mtype=mtype)

    async def outcast(self, re_jid, mtype, args):
        try:
            jid_to_outcast = JID(args[1])

            if jid_to_outcast.bare != self.jid:
                await self.plugin['xep_0045'].set_affiliation(re_jid, 'outcast', jid=jid_to_outcast)
                self.send_message(
                    mto=re_jid,
                    mbody='驱逐 %s ' % jid_to_outcast,
                    mtype=mtype
                )
        except IndexError:
            self.send_message(re_jid, '没有输入', mtype=mtype)

    async def set_aff(self, re_jid, mtype, args):
        try:
            nick_to_set = args[1]
            nick_set_to = args[2]
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
        except IndexError:
            self.send_message(re_jid, '没有输入', mtype=mtype)


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
