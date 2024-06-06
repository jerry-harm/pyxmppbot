#!../.venv/bin/python
import logging

from slixmpp import ClientXMPP
from slixmpp import JID, InvalidJID
from slixmpp.exceptions import IqError, IqTimeout
from slixmpp.stanza.message import Message


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

    #

    async def start(self, event):
        await self.get_roster()
        self.send_presence()
        self.plugin['xep_0045'].join_muc(self.room,self.nick)

    # 私信处理
    def message(self, msg):
        if msg['type'] in ('chat', 'normal'):
            msg.reply("Thanks for sending\n%(body)s" % msg).send()
            # 判断是否来自群聊
            if msg['from'].bare in self.plugin['xep_0045'].get_joined_rooms():
                msg.reply("got").send()


    
    # 群聊处理
    async def muc_message(self, msg:Message):
        # 判断被@
        room_jid, acquire_user = msg['from'].bare,msg['from'].resource
        cmd = msg['body'].split(' ')
        if msg['mucnick'] != self.nick and self.nick in msg['body']:

            if 'DO' in cmd:
                if 'list_users' in cmd:
                    nones = await self.plugin['xep_0045'].get_roles_list(room_jid, role='none')
                    visitors = await self.plugin['xep_0045'].get_roles_list(room_jid, role='visitor')
                    moderators = await self.plugin['xep_0045'].get_roles_list(room_jid,role='moderator')
                    participants = await self.plugin['xep_0045'].get_roles_list(room_jid, role='participant')
                    self.send_message(mto=room_jid,
                                      mbody=str("nones: %s \nvisitors: %s\nmoderators: %s\nparticipants: %s"
                                                %(nones,visitors,moderators,participants)),
                                      mtype='groupchat'
                                      )
            if 'ADMIN' in cmd:
                
                moderators = await self.plugin['xep_0045'].get_roles_list(room_jid, role='moderator')
                if acquire_user in moderators:
                    if 'get_jid' in cmd:
                        nick_to_search = cmd[cmd.index('get_jid')+1]
                        self.send_message(mto=room_jid,
                                          mbody=self.plugin['xep_0045'].get_jid_property(room_jid,nick_to_search,'jid'),
                                          mtype='groupchat'
                                          )
                    if 'get_conf' in cmd:
                        self.send_message(mto = msg['from'],
                                          mbody = str(await self.plugin['xep_0045'].get_room_config(room_jid)),
                                          mtype = 'chat'
                                          )
                    if 'outcast' in cmd:
                        jid_to_outcast = JID(cmd[cmd.index('outcast') + 1])

                        if jid_to_outcast.bare != self.jid:
                            await self.plugin['xep_0045'].set_affiliation(room_jid,'outcast',jid=jid_to_outcast)
                            self.send_message(
                            mto=room_jid,
                            mbody='outcast %s ' % jid_to_outcast,
                            mtype='groupchat'
                        )
                    if 'set_user' in cmd:
                        nick_to_set = cmd[cmd.index('set_user') + 1]
                        nick_set_to = cmd[cmd.index('set_user') + 2]
                        if nick_set_to not in ['member', 'admin', 'owner', 'none']:
                            self.send_message(mto=room_jid,
                                              mbody='not an affiliation',
                                              mtype='groupchat'
                                              )
                        else:
                            await self.plugin['xep_0045'].set_affiliation(room_jid,nick_set_to,nick=nick_to_set)
                            self.send_message(mto=room_jid,
                                              mbody='affiliation set done',
                                              mtype='groupchat'
                                              )

                        
                else:
                    self.send_message(
                        mto=room_jid,
                        mbody='not an admin',
                        mtype='groupchat'

                    )





            

if __name__ == '__main__':

    logging.basicConfig(level=logging.DEBUG,
                        format='%(levelname)-8s %(message)s')
    jid = input('jid:')
    passwd= input('passwd:')
    xmpp = Bot(jid,passwd,"whatever@conference.jerrynya.fun","AFM")
    xmpp.connect()
    xmpp.process(forever=True)