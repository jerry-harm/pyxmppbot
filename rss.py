import feedparser


class RSS:
    def __init__(self, url):
        self.url = url
        self.last_id: str = self.get_last_id()

    def get_last_id(self):
        try:
            feeds = feedparser.parse(self.url)
            print(feeds.entries[0].title)
            return feeds.entries[0].title
        except IndexError:
            return ''

    def __call__(self):
        msg = ''
        try:
            feeds = feedparser.parse(self.url)
            for feed in feeds.entries:
                if feed.title != self.last_id:
                    msg += '*{}*\n{}\n{}\n{}\n'.format(feeds.feed.title, feed.title, feed.link, feed.updated)
                else:
                    break
            self.last_id = feeds.entries[0].title
        finally:
            return msg

    def __str__(self):
        return self.url

    def get_by_num(self, num: int):
        msg = ''
        try:
            feeds = feedparser.parse(self.url)
            for i in range(num):
                msg += '*{}*\n{}\n{}\n{}\n'.format(feeds.feed.title, feeds.entries[i].title, feeds.entries[i].link,
                                                   feeds.entries[i].updated)
        finally:
            return msg
