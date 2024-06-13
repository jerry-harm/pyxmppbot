from slixmpp import JID, ClientXMPP


class AdminHandler:
    def __init__(self, client: ClientXMPP,to,mtype,nick):
        self.client = client
        self.cmds = {"获取JID": [self.get_jid, 1, "管理员获取JID"],
                     "help": [self.admin_help, 0, "管理员帮助"],
                     "驱逐": [self.outcast, 1, "驱逐一个JID"],
                     '设置从属关系': [self.set_aff, 2, "设置一个nick的从属关系"]
                     }
        self.to = to
        self.mtype = mtype
        self.nick = nick

    # admin
    def get_jid(self, args):
        try:
            nick_to_search = args[1]
            self.client.send_message(mto=self.to,
                                     mbody=self.client.plugin['xep_0045'].get_jid_property(self.to, nick_to_search,
                                                                                           'jid'),
                                     mtype=self.mtype
                                     )
        except IndexError:
            self.client.send_message(self.to, '没有输入', mtype=self.mtype)

    def admin_help(self, args):
        res = ""
        for k, d in self.cmds.items():
            res = res + "{} : {},需要{}个参数\n".format(k, d[2], d[1])
        self.client.send_message(mto=self.to, mbody=res, mtype=self.mtype)

    async def outcast(self, args):
        try:
            jid_to_outcast = JID(args[1])

            if jid_to_outcast.bare != self.client.jid:
                await self.client.plugin['xep_0045'].set_affiliation(room=JID(self.to.bare), affiliation='outcast',
                                                                     jid=jid_to_outcast)
                self.client.send_message(
                    mto=self.to,
                    mbody='驱逐 %s ' % jid_to_outcast,
                    mtype=self.mtype
                )
        except IndexError:
            self.client.send_message(self.to, '没有输入', mtype=self.mtype)

    async def set_aff(self, args):
        try:
            nick_to_set = args[1]
            nick_set_to = args[2]
            if nick_set_to not in ['member', 'admin', 'owner', 'none']:
                self.client.send_message(mto=self.to,
                                         mbody='not an affiliation',
                                         mtype=self.mtype
                                         )
            else:
                await self.client.plugin['xep_0045'].set_affiliation(self.to, nick_set_to, nick=nick_to_set)
                self.client.send_message(mto=self.to,
                                         mbody='affiliation set done',
                                         mtype=self.mtype
                                         )
        except IndexError:
            self.client.send_message(self.to, '没有输入', mtype=self.mtype)
