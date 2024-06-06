#!../.venv/bin/python
import logging
import sys

from slixmpp import ClientXMPP
from slixmpp import JID
from slixmpp.stanza.message import Message
from slixmpp.types import MessageTypes



class Bot(ClientXMPP):

    def __init__(self, jid, password, room="whatever@conference.jerrynya.fun", nick="AFM"):
        ClientXMPP.__init__(self, jid, password)

        self.room = JID(room)
        self.nick = nick

        self.add_event_handler("session_start", self.start)
        self.add_event_handler("message", self.message)
        self.add_event_handler("groupchat_message", self.muc_message)

        # If you wanted more functionality, here's how to register plugins:
        self.register_plugin('xep_0030')  # Service Discovery
        # self.register_plugin('xep_0199') # XMPP Ping

        self.register_plugin('xep_0045')  # muc plugin
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
        self.send_message(msg['from'].bare,str(moderators),mtype='groupchat')
        if self.nick in moderators:
            # Bot is admin
            if msg['from'].resource in moderators:
                self.send_message(msg['from'].bare,"do it",mtype='groupchat')
                return True
            else:
                self.send_message(msg['from'].bare,"not admin",mtype='groupchat')
                return False
        else:
            self.send_message(msg['from'].bare,"I'm not admin",mtype='groupchat')
            return False

    async def resolve_admin_cmd(self, msg: Message):
        """
        resolve the admin cmd
        :param msg:
        :return:
        """
        cmd = msg['body'].split(' ')
        room_jid = msg['from'].bare
        print(room_jid)
        # 怎么来的怎么回去
        mtype: MessageTypes = msg['type']

        if '获取JID' in cmd:
            nick_to_search = cmd[cmd.index('get_jid') + 1]
            self.send_message(mto=room_jid,
                              mbody=self.plugin['xep_0045'].get_jid_property(room_jid, nick_to_search,
                                                                             'jid'),
                              mtype=mtype
                              )
        if '获得聊天室设置' in cmd:
            self.send_message(mto=room_jid,
                              mbody=str(await self.plugin['xep_0045'].get_room_config(room_jid)),
                              mtype=mtype
                              )
        if '驱逐' in cmd:
            jid_to_outcast = JID(cmd[cmd.index('驱逐') + 1])

            if jid_to_outcast.bare != self.jid:
                await self.plugin['xep_0045'].set_affiliation(room_jid, 'outcast', jid=jid_to_outcast)
                self.send_message(
                    mto=room_jid,
                    mbody='驱逐 %s ' % jid_to_outcast,
                    mtype=mtype
                )
        if '设置从属关系' in cmd:
            nick_to_set = cmd[cmd.index('设置从属关系') + 1]
            nick_set_to = cmd[cmd.index('设置从属关系') + 2]
            if nick_set_to not in ['member', 'admin', 'owner', 'none']:
                self.send_message(mto=room_jid,
                                  mbody='not an affiliation',
                                  mtype=mtype
                                  )
            else:
                await self.plugin['xep_0045'].set_affiliation(room_jid, nick_set_to, nick=nick_to_set)
                self.send_message(mto=room_jid,
                                  mbody='affiliation set done',
                                  mtype=mtype
                                  )


    def resolve_usr_cmd(self,msg:Message):
        """
        handel user's cmd
        :param msg:
        :return:
        """
        cmd = msg['body'].split(' ')
        room_jid = msg['from'].bare
        # 怎么来的怎么回去
        mtype: MessageTypes = msg['type']



    async def start(self, event):
        await self.get_roster()
        self.send_presence()
        await self.plugin['xep_0045'].join_muc(self.room, self.nick)

    # 私信处理
    async def message(self, msg: Message):

        if msg['type'] in ('chat', 'normal'):
            msg.reply("Thanks for sending\n%s" % msg['body']).send()
            # 判断是否来自群聊
            if self.confirm_from_room(msg):
                if 'ADMIN' in msg['body']:
                    if self.confirm_room_admin(msg):
                        await self.resolve_admin_cmd(msg)
                elif 'DO' in msg['body']:
                    self.resolve_usr_cmd(msg)
            else:
                # 普通私聊处理
                self.send_message(mto=msg['from'].bare,
                                  mbody="来自%s，你说%s" % (msg['from'], msg['body']),
                                  mtype="groupchat"
                                  )

    # 群聊处理
    async def muc_message(self, msg: Message):
        # 被提到
        if msg['mucnick'] != self.nick and self.nick in msg['body']:
            if 'ADMIN' in msg['body']:
                if await self.confirm_room_admin(msg):
                    await self.resolve_admin_cmd(msg)
            elif 'DO' in msg['body']:
                self.resolve_usr_cmd(msg)
            else:
                # 普通群聊处理
                self.send_message(mto=msg['from'].bare,
                                  mbody="来自%s，你说%s" % (msg['from'], msg['body']),
                                  mtype="groupchat"
                                  )


if __name__ == '__main__':
    if sys.platform == 'win32':
        import asyncio

        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    logging.basicConfig(level=logging.DEBUG,
                        format='%(levelname)-8s %(message)s')
    get_jid = input('jid:')
    get_passwd = input('passwd:')
    xmpp = Bot(get_jid, get_passwd, "whatever@conference.jerrynya.fun", "AFM")
    xmpp.connect()
    xmpp.process()
