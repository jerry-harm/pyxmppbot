import random
from collections import defaultdict

from slixmpp import Message, ClientXMPP, JID

import get_api


class UserHandler:
    def __init__(self, client: ClientXMPP, to, mtype, nick, handlers: tuple):
        self.client = client
        self.cmds = {
            "help": [self.show_functions, 0, "显示所有命令"],
            "色图": [self.send_img, 0, "随机动漫色图"],
            "写真": [self.send_img, 0, "随机写真"],
            "龙图": [self.send_img, 0, "随机龙图"],
            "QQ": [self.qq_information, 1, "获取一个qq号的头像和邮箱"],
            "随机数": [self.send_random, 2, "获得输入两数间的随机数"],
            "统计": [self.stats_mam, 1, "获取n条内发言次数统计"],
            "加入": [self.join_room, 1, "加入指定jid的房间"],
            "上线欢迎": [self.welcome, 1, "开或关"],
            "下线道别": [self.goodbye, 1, "开或关"],
            "定时消息": [self.scheduled_msg, 3, "开或关 计时分钟数 定时发送的内容"]
        }
        self.event_handlers = {"上线欢迎": handlers[0],
                               "下线道别": handlers[1]}
        self.to = JID(to)
        self.mtype = mtype
        self.nick = nick

    def send_img(self, args):
        url = random.choice(get_api.apis[args[0]])()
        if not url:
            self.client.send_message(
                mto=self.to,
                mbody="wrong",
                mtype=self.mtype
            )
            return 0
        msg = Message()
        msg['type'] = self.mtype
        msg['to'] = self.to
        msg['body'] = url
        msg['oob']['url'] = url
        self.client.send(msg)
        self.client.send_message(mto=self.to, mbody=url, mtype=self.mtype)

    def show_functions(self, args):
        res = "每个参数之间请用空格隔开,命令请勿有引用操作"
        for k, d in self.cmds.items():
            res = res + "{} : {},需要{}个参数\n".format(k, d[2], d[1])
        self.client.send_message(mto=self.to, mbody=res, mtype=self.mtype)

    def qq_information(self, args):
        try:
            res = get_api.qq_json(args[1])
            if res:
                self.client.send_message(mtype=self.mtype, mto=self.to,
                                         mbody=res)
                msg = Message()
                msg['type'] = self.mtype
                msg['to'] = self.to
                msg['body'] = res
                msg['oob']['url'] = res
                self.client.send(msg)
            else:
                self.client.send_message(mbody="调用出错", mtype=self.mtype, mto=self.to)
        except IndexError:
            self.client.send_message(self.to, '没有输入', mtype=self.mtype)

    def send_random(self, args):
        try:
            res = random.randint(int(args[1]), int(args[2]))
            self.client.send_message(mto=self.to, mbody=str(res), mtype=self.mtype)
        except TypeError:
            self.client.send_message(mto=self.to, mbody='不是两个数', mtype=self.mtype)
        except IndexError:
            self.client.send_message(self.to, '没有输入', mtype=self.mtype)
        except ValueError:
            self.client.send_message(self.to, '范围出错', mtype=self.mtype)

    async def stats_mam(self, args):
        try:
            num = int(args[1])
            mam = self.client.plugin['xep_0313'].iterate(self.to.bare, total=num, reverse=True)
            res = defaultdict(int)
            async for m in mam:
                res[m['mam_result']['forwarded']['message']['from'].resource] += 1
            res_str = '在最近的{}以内条中：\n'.format(num)
            for nick, times in res.items():
                res_str += '{}:{}次 '.format(nick, times)
            self.client.send_message(self.to, mbody=res_str, mtype=self.mtype)
        except IndexError:
            self.client.send_message(self.to, mbody='请输入条数', mtype=self.mtype)
        except TypeError:
            self.client.send_message(self.to, mbody='输入的不是数！', mtype=self.mtype)

    def join_room(self, args):
        try:
            self.client.plugin['xep_0045'].join_muc(args[1], nick=self.nick)
            self.client.send_message(mtype=self.mtype, mto=self.to, mbody='尝试加入')
        except IndexError:
            self.client.send_message(self.to, mbody='请输入房间', mtype=self.mtype)

    def welcome(self, args):
        try:
            if self.mtype != "groupchat":
                self.client.send_message(mto=self.to, mtype=self.mtype, mbody='请在群聊中使用此命令')
                return False
            if args[1] == '开':
                self.client.add_event_handler("muc::%s::got_online" % self.to, self.event_handlers['上线欢迎'])
                self.client.send_message(mto=self.to, mtype=self.mtype, mbody='处理完成')
            else:
                self.client.del_event_handler("muc::%s::got_online" % self.to, self.event_handlers['上线欢迎'])
                self.client.send_message(mto=self.to, mtype=self.mtype, mbody='处理完成')
        except IndexError:
            self.client.send_message(mto=self.to, mtype=self.mtype, mbody='请输入开或关')

    def goodbye(self, args):
        try:
            if self.mtype != "groupchat":
                self.client.send_message(mto=self.to, mtype=self.mtype, mbody='请在群聊中使用此命令')
                return False
            if args[1] == '开':
                self.client.add_event_handler("muc::%s::got_offline" % self.to, self.event_handlers['下线道别'])
                self.client.send_message(mto=self.to, mtype=self.mtype, mbody='处理完成')
            else:
                self.client.del_event_handler("muc::%s::got_offline" % self.to, self.event_handlers['下线道别'])
                self.client.send_message(mto=self.to, mtype=self.mtype, mbody='处理完成')
        except IndexError:
            self.client.send_message(mto=self.to, mtype=self.mtype, mbody='请输入开或关')

    def scheduled_msg(self, args):
        try:
            if args[1] == '开':
                def send():
                    msg = args[3:]
                    self.client.send_message(mto=self.to, mbody=msg, mtype=self.mtype)

                self.client.schedule("%s" % self.to, int(args[2]) * 60, send)
                self.client.send_message(mto=self.to, mtype=self.mtype, mbody='处理完成')
            else:
                self.client.cancel_schedule("%s" % self.to)
                self.client.send_message(mto=self.to, mtype=self.mtype, mbody='处理完成')
        except IndexError:
            self.client.send_message(mto=self.to, mtype=self.mtype, mbody='请输入开或关')
        except TypeError:
            self.client.send_message(mto=self.to, mtype=self.mtype, mbody='请输入延时分钟数')
