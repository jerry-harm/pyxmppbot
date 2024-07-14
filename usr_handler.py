import random
import socket
import typing

from rss import RSS
from collections import defaultdict
import asyncio

from slixmpp import Message, ClientXMPP, JID

from main import *
import get_api


class UserHandlerBot(Bot):
    def __init__(self, jid, password, room, nick="AFM"):
        self.handlers = {
            "help": Handler(self.show_functions, "显示所有命令"),
            "色图": Handler(self.send_img_api, "随机动漫色图"),
            "写真": Handler(self.send_img_api, "随机写真"),
            "龙图": Handler(self.send_img_api, "随机龙图"),
            "QQ": Handler(self.qq_information, "获取一个qq号的头像"),
            "随机数": Handler(self.send_random, "获得输入两数间的随机数"),
            "统计": Handler(self.stats_mam, "获取n条内发言次数统计"),
            "加入": Handler(self.join_room, "加入指定jid的房间"),
            "上线欢迎": Handler(self.welcome, "开或关"),
            "下线道别": Handler(self.goodbye, "开或关"),
            "定时消息": Handler(self.scheduled_msg, "开或关 计时分钟数（大于5分钟） 定时发送的内容"),
            "订阅": Handler(self.feed,
                            "添加 名称 feed网址(网址请带https前缀);查询;删除 名称;开;关;last feed网址/名称 条数（可选）"),
        }
        self.default_handler = Handler(self.default_handler, "默认回复功能")
        self.feeds: typing.Dict[str, RSS] = {'hackernews': RSS('https://hnrss.org/newest?points=100'),
                                             'prosody': RSS('https://blog.prosody.im/index.xml'),
                                             '澎湃新闻': RSS('https://plink.anyfeeder.com/thepaper'),
                                             '少数派': RSS('https://feeds.appinn.com/appinns/'),
                                             '机核': RSS('https://www.gcores.com/rss'),
                                             '人民日报': RSS('http://www.people.com.cn/rss/ywkx.xml'),
                                             'Jerry的技术分享': RSS('https://jerrynya.fun/rss2.xml')}
        Bot.__init__(self, jid, password, room, self.handlers, self.default_handler, nick)

    def default_handler(self, cmd, msg: Message):
        self.send(msg.reply("输入 {} help 来获取帮助".format(self.nick)))

    def send_img_api(self, cmd, msg: Message):
        url = random.choice(get_api.apis[cmd[0]])()
        if not url:
            self.send(msg.reply("获取过于频繁或api出错"))
            return False
        p_msg = Message()
        p_msg['type'] = msg['type']
        p_msg['to'] = msg['from'].bare
        p_msg['body'] = url
        p_msg['oob']['url'] = url
        self.send(p_msg)
        self.send(msg.reply(url))

    def show_functions(self, cmd, msg: Message):
        res = "每个参数之间请用空格隔开,命令请勿有引用操作"
        for k, d in self.handlers.items():
            res = res + "{} : {}\n".format(k, d)
        self.send(msg.reply(res))

    def qq_information(self, cmd, msg: Message):
        try:
            res = get_api.qq_json(cmd[1])
            if res:
                self.send(msg.reply(res))
                p_msg = Message()
                p_msg['type'] = msg['type']
                p_msg['to'] = msg['from'].bare
                p_msg['body'] = res
                p_msg['oob']['url'] = res
                self.send(p_msg)
            else:
                self.send(msg.reply('出错'))
        except IndexError:
            self.send(msg.reply('没有输入'))

    def send_random(self, cmd, msg: Message):
        try:
            res = random.randint(int(cmd[1]), int(cmd[2]))
            self.send(msg.reply(str(res)))
        except TypeError:
            self.send(msg.reply('不是数字'))
        except IndexError:
            self.send(msg.reply('没有输入'))
        except ValueError:
            self.send(msg.reply('范围错误'))

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
            self.send(msg.reply(res_str))
        except IndexError:
            self.send(msg.reply('请输入参数'))
        except TypeError:
            self.send(msg.reply('输入的不是数'))

    def join_room(self, cmd, msg: Message):
        try:
            self.plugin['xep_0045'].join_muc(cmd[1], nick=self.nick)
            self.send(msg.reply('尝试加入 {}'.format(cmd[1])))
        except IndexError:
            self.send(msg.reply('请输入房间'))

    def welcome(self, cmd, msg: Message):
        try:
            if msg['type'] != "groupchat":
                self.send(msg.reply('请在群聊中使用这条命令'))
                return False
            if cmd[1] == '开':
                self.add_event_handler("muc::%s::got_online" % msg.get_mucroom(), self.when_muc_joined)
                self.send(msg.reply('开启'))
            else:
                self.del_event_handler("muc::%s::got_online" % msg.get_mucroom(), self.when_muc_joined)
                self.send(msg.reply('关闭'))
        except IndexError:
            self.send(msg.reply('请输入开或关'))

    def goodbye(self, cmd, msg: Message):
        try:
            if msg['type'] != "groupchat":
                self.send(msg.reply('请在群聊中使用这条命令'))
                return False
            if cmd[1] == '开':
                self.add_event_handler("muc::%s::got_offline" % msg.get_mucroom(), self.when_muc_offed)
                self.send(msg.reply('开启'))
            else:
                self.del_event_handler("muc::%s::got_offline" % msg.get_mucroom(), self.when_muc_offed)
                self.send(msg.reply('关闭'))
        except IndexError:
            self.send(msg.reply('请输入开或关'))

    def scheduled_msg(self, cmd, msg: Message):
        try:
            if cmd[1] == '开':
                def send():
                    to_msg = cmd[3:]
                    self.send(msg.reply(to_msg))

                if int(cmd[2]) <= 5:
                    self.send(msg.reply('时间太短了'))
                    return False

                self.schedule("msg::%s" % msg.get_from(), int(cmd[2]) * 60, send, repeat=True)
                self.send(msg.reply('开启'))
            else:
                self.cancel_schedule("%s" % msg.get_from())
                self.send(msg.reply('关闭'))
        except IndexError:
            self.send(msg.reply('请输入分钟数'))
        except ValueError:
            self.send(msg.reply('请输入整数分钟'))

    def when_muc_joined(self, msg):
        self.send_message(mto=msg['from'].bare,
                          mbody='欢迎{}!'.format(msg['from'].resource),
                          mtype='groupchat')

    def when_muc_offed(self, msg):
        self.send_message(mto=msg['from'].bare,
                          mbody='再见{}!'.format(msg['from'].resource),
                          mtype='groupchat')

    def check_feed(self,msg:Message):
        print('called')
        for f in self.feeds.values():
            r = f()
            if r != '':
                if msg.get_type() == 'groupchat':
                    self.send_message(mto=msg['from'].bare,mbody=r,mtype='groupchat')
                else:
                    self.send_message(mto=msg['from'].bare, mbody=r)
            else:
                pass

    def feed(self, cmd, msg):

        try:
            if cmd[1] == "查询":
                res = ''
                for k, v in self.feeds.items():
                    res += k + ' ' + v.url + '\n'
                self.send(msg.reply(res))
                return True
            elif cmd[1] == "关":
                self.cancel_schedule("feed:%s" % msg.get_from())
            elif cmd[1] == "开":
                self.schedule("feed:%s" % msg.get_from(), 600, self.check_feed,args=tuple([msg]), repeat=True)
                print('schedule')
            elif cmd[1] == "删除":
                del self.feeds[cmd[2]]
            elif cmd[1] == "last":
                if cmd[2] in self.feeds:
                    num: int = 1
                    try:
                        num = int(cmd[3])
                    except IndexError:
                        num = 1
                    finally:
                        res = self.feeds[cmd[2]].get_by_num(num)
                        self.send(msg.reply(res))
                else:
                    num: int = 1
                    try:
                        num = int(cmd[3])
                    except IndexError:
                        num = 1
                    finally:
                        res = RSS(cmd[2]).get_by_num(num)
                        self.send(msg.reply(res))

            elif cmd[1] == "添加":
                print(cmd[2], cmd[3])
                self.feeds[cmd[2]] = RSS(cmd[3])
        except IndexError:
            self.send(msg.reply('未输入参数'))
        except ValueError:
            self.send(msg.reply('值错误'))


if __name__ == '__main__':
    if sys.platform == 'win32':
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
    socket.setdefaulttimeout(5)
    xmpp = UserHandlerBot(args.jid, args.password, args.room, args.nick)
    xmpp.connect()
    xmpp.init_plugins()
    xmpp.loop.run_forever()
