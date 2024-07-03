import random
from collections import defaultdict

from slixmpp import Message, ClientXMPP, JID

from main import *
import get_api


class UserHandlerBot(Bot):
    def __init__(self, jid, password, room, nick="AFM"):
        Bot.__init__(self, jid, password, room, nick)
        self.handlers = {
            "help": Handler(self.show_functions, "显示所有命令"),
            "色图": Handler(self.send_img_api, "随机动漫色图"),
            "写真": Handler(self.send_img_api, "随机写真"),
            "龙图": Handler(self.send_img_api, "随机龙图"),
            "QQ": Handler(self.qq_information, "获取一个qq号的头像和邮箱"),
            "随机数": Handler(self.send_random, "获得输入两数间的随机数"),
            "统计": Handler(self.stats_mam, "获取n条内发言次数统计"),
            "加入": Handler(self.join_room, "加入指定jid的房间"),
            "上线欢迎": Handler(self.welcome, "开或关"),
            "下线道别": Handler(self.goodbye, "开或关"),
            "定时消息": Handler(self.scheduled_msg, "开或关 计时分钟数（大于10分钟） 定时发送的内容")
        }
        self.default_handler = Handler(self.default_handler, "默认回复功能")

    def default_handler(self, cmd, msg: Message):
        msg.reply("输入 {} help 来获取帮助".format(self.nick))

    def send_img_api(self, cmd, msg: Message):
        url = random.choice(get_api.apis[cmd[0]])()
        if not url:
            msg.reply("获取过于频繁或api出错")
            return False
        p_msg = Message()
        p_msg['type'] = msg['type']
        p_msg['to'] = msg['form']
        p_msg['body'] = url
        p_msg['oob']['url'] = url
        self.send(p_msg)
        msg.reply(url)

    def show_functions(self, cmd, msg: Message):
        res = "每个参数之间请用空格隔开,命令请勿有引用操作"
        for k, d in self.handlers.items():
            res = res + "{} : {}\n".format(k, d)
        msg.reply(res)

    def qq_information(self, cmd, msg: Message):
        try:
            res = get_api.qq_json(cmd[1])
            if res:
                msg.reply(res)
                p_msg = Message()
                p_msg['type'] = msg['type']
                p_msg['to'] = msg['from']
                p_msg['body'] = res
                p_msg['oob']['url'] = res
                self.send(p_msg)
            else:
                msg.reply('出错')
        except IndexError:
            msg.reply('没有输入')

    def send_random(self, cmd, msg: Message):
        try:
            res = random.randint(int(cmd[1]), int(cmd[2]))
            msg.reply(str(res))
        except TypeError:
            msg.reply('不是数字')
        except IndexError:
            msg.reply('没有输入')
        except ValueError:
            msg.reply('范围错误')

    async def stats_mam(self, cmd, msg: Message):
        try:
            num = int(cmd[1])
            mam = self.plugin['xep_0313'].iterate(jid=JID(msg.get_mucroom()), total=num, reverse=True)
            res = defaultdict(int)
            # 计数
            async for m in mam:
                res[m['mam_result']['forwarded']['message']['from'].resource] += 1
            res_str = '在最近的{}以内条中：\n'.format(num)
            for nick, times in res.items():
                res_str += '{}:{}次 '.format(nick, times)
            msg.reply(res_str)
        except IndexError:
            msg.reply('请输入参数')
        except TypeError:
            msg.reply('输入的不是数')

    def join_room(self, cmd, msg: Message):
        try:
            self.plugin['xep_0045'].join_muc(cmd[1], nick=self.nick)
            msg.reply('尝试加入 {}'.format(cmd[1]))
        except IndexError:
            msg.reply('请输入房间')

    def welcome(self, cmd, msg: Message):
        try:
            if msg['type'] != "groupchat":
                msg.reply('请在群聊中使用这条命令')
                return False
            if cmd[1] == '开':
                self.add_event_handler("muc::%s::got_online" % msg.get_mucroom(), self.when_muc_joined)
                msg.reply('开启')
            else:
                self.del_event_handler("muc::%s::got_online" % msg.get_mucroom(), self.when_muc_joined)
                msg.reply('关闭')
        except IndexError:
            msg.reply('请输入开或关')

    def goodbye(self, cmd, msg: Message):
        try:
            if msg['type'] != "groupchat":
                msg.reply('请在群聊中使用这条命令')
                return False
            if cmd[1] == '开':
                self.add_event_handler("muc::%s::got_offline" % msg.get_mucroom(), self.when_muc_offed)
                msg.reply('开启')
            else:
                self.del_event_handler("muc::%s::got_offline" % msg.get_mucroom(), self.when_muc_offed)
                msg.reply('关闭')
        except IndexError:
            msg.reply('请输入开或关')

    def scheduled_msg(self, cmd, msg: Message):
        try:
            if cmd[1] == '开':
                def send():
                    to_msg = cmd[3:]
                    msg.reply(to_msg)

                if cmd[2] <= 10:
                    msg.reply('时间太短了')
                    return False

                self.schedule("%s" % msg.get_from(), int(cmd[2]) * 60, send, repeat=True)
                msg.reply('开启')
            else:
                self.cancel_schedule("%s" % msg.get_from())
                msg.reply('关闭')
        except IndexError:
            msg.reply('请输入分钟数')
        except ValueError:
            msg.reply('请输入整数分钟')

    def when_muc_joined(self, msg):
        self.send_message(mto=msg['from'].bare,
                          mbody='欢迎{}!'.format(msg['from'].resource),
                          mtype='groupchat')

    def when_muc_offed(self, msg):
        self.send_message(mto=msg['from'].bare,
                          mbody='再见{}!'.format(msg['from'].resource),
                          mtype='groupchat')


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
