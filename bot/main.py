#!../.venv/bin/python
import logging

from slixmpp import ClientXMPP
from slixmpp import JID, InvalidJID
from slixmpp.exceptions import IqError, IqTimeout


class Bot(ClientXMPP):

    def __init__(self, jid, password,room="whatever@conference.jerrynya.fun",nick="AFM"):
        ClientXMPP.__init__(self, jid, password)
        
        self.room = JID(room)
        self.nick = nick
        
        self.add_event_handler("session_start", self.start)
        self.add_event_handler("message", self.message)
        self.add_event_handler("groupchat_message", self.muc_message)
        
        # If you wanted more functionality, here's how to register plugins:
        self.register_plugin('xep_0030') # Service Discovery
        # self.register_plugin('xep_0199') # XMPP Ping

        self.register_plugin('xep_0045') # muc plugin

    async def start(self, event):
        await self.get_roster()
        self.send_presence()
        self.plugin['xep_0045'].join_muc(self.room,self.nick)

    # 私信处理
    def message(self, msg):
        if msg['type'] in ('chat', 'normal'):
            msg.reply("Thanks for sending\n%(body)s" % msg).send()
    
    # 群聊处理
    async def muc_message(self, msg):
        # 判断被@
        print(msg)
        room_jid, acquire_user = str(msg['from']).split('/',1)
        if msg['mucnick'] != self.nick and self.nick in msg['body']:

            if 'DO' in msg['body']:
                if 'list_users' in msg['body']:
                    nones = await self.plugin['xep_0045'].get_roles_list(room_jid, role='none')
                    visitors = await self.plugin['xep_0045'].get_roles_list(room_jid, role='visitor')
                    moderators = await self.plugin['xep_0045'].get_roles_list(room_jid,role='moderator')
                    participants = await self.plugin['xep_0045'].get_roles_list(room_jid, role='participant')
                    self.send_message(mto=msg['from'].bare,
                                      mbody=str("nones: %s \nvisitors: %s\nmoderators: %s\nparticipants: %s"
                                                %(nones,visitors,moderators,participants)),
                                      mtype='groupchat'
                                      )
            if 'ADMIN' in msg['body']:
                cmd = msg['body'].split(' ')
                moderators = await self.plugin['xep_0045'].get_roles_list(room_jid, role='moderator')
                if acquire_user in moderators:
                    if 'get_jid' in cmd:
                        nick_to_search = cmd[cmd.index('get_jid')+1]
                        jid_got = self.plugin['xep_0045'].get_jid_property(room_jid,nick_to_search,'jid')



                        self.send_message(mto=msg['from'].bare,
                                          mbody=jid_got,
                                          mtype='groupchat'
                                          )
                else:
                    self.send_message(
                        mto=msg['from'].bare,
                        mbody='not an admin',
                        mtype='groupchat'

                    )





            

if __name__ == '__main__':

    logging.basicConfig(level=logging.DEBUG,
                        format='%(levelname)-8s %(message)s')

    xmpp = Bot('bot@jerrynya.fun', 'dqjJ8lFWGQlK7fkKqSjZ0QGcxi8ZnsK3Ppt5B25SAKE=',"whatever@conference.jerrynya.fun","AFM")
    xmpp.connect()
    xmpp.process(forever=True)