#!../.venv/bin/python
import logging

from slixmpp import ClientXMPP
from slixmpp.exceptions import IqError, IqTimeout


class Bot(ClientXMPP):

    def __init__(self, jid, password,room="whatever@conference.jerrynya.fun",nick="AFM"):
        ClientXMPP.__init__(self, jid, password)
        
        self.room=room
        self.nick=nick
        
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
    def muc_message(self, msg):
        # 判断被@
        if msg['mucnick'] != self.nick and self.nick in msg['body']:
            
            self.send_message(mto=msg['from'].bare,
                              mbody="get %s from %s." % (msg['body'],msg['mucnick']),
                              mtype='groupchat')
            

if __name__ == '__main__':

    logging.basicConfig(level=logging.DEBUG,
                        format='%(levelname)-8s %(message)s')

    xmpp = Bot('bot@jerrynya.fun', 'dqjJ8lFWGQlK7fkKqSjZ0QGcxi8ZnsK3Ppt5B25SAKE=',"whatever@conference.jerrynya.fun","AFM")
    xmpp.connect()
    xmpp.process(forever=True)