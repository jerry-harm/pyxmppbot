import time
import urllib.error
from typing import Any
from urllib.request import Request, urlopen
import random
import ssl
import json
import feedparser

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:129.0) Gecko/20100101 Firefox/129.0"
}


def open_ssl(url, api='') -> Any:
    try:

        req = Request(url=url + api, headers=headers)
        res = urlopen(url=req, context=ssl.create_default_context())
        return res
    except urllib.error.HTTPError as e:
        print(e)
        return False
    except urllib.error.URLError as e:
        print(e)
        return False
    except ValueError:
        return False


def api1(url="https://sex.nyan.xyz/api/v2/"):
    """
    色图api sex.nyan.xyz
    :return: url
    """
    r18 = random.randint(0, 1)
    api = "?r18=" + str(r18)
    res = open_ssl(url, api)
    if res:
        json_str = res.read().decode('utf-8')
        return json.loads(json_str)['data'][0]['url']


def api2(url='https://image.anosu.top/pixiv/json'):
    """
    色图api image.anosu.top
    :param url:
    :return:
    """
    r18 = 2
    api = "?r18=" + str(r18)
    res = open_ssl(url, api)
    if res:
        json_str = res.read().decode('utf-8')
        return json.loads(json_str)[0]['url']


def api3():
    """
    cosplay https://api.r10086.com
    :return:
    """
    url = random.choice([
        'https://api.r10086.com/%E6%A8%B1%E9%81%93%E9%9A%8F%E6%9C%BA%E5%9B%BE%E7%89%87api%E6%8E%A5%E5%8F%A3.php?%E5%9B%BE%E7%89%87%E7%B3%BB%E5%88%97=%E6%9E%81%E5%93%81%E7%BE%8E%E5%A5%B3%E5%9B%BE%E7%89%87',
        'https://api.r10086.com/%E6%A8%B1%E9%81%93%E9%9A%8F%E6%9C%BA%E5%9B%BE%E7%89%87api%E6%8E%A5%E5%8F%A3.php?%E5%9B%BE%E7%89%87%E7%B3%BB%E5%88%97=%E6%9E%81%E5%93%81%E7%BE%8E%E5%A5%B3%E5%9B%BE%E7%89%87',
        'https://api.r10086.com/%E6%A8%B1%E9%81%93%E9%9A%8F%E6%9C%BA%E5%9B%BE%E7%89%87api%E6%8E%A5%E5%8F%A3.php?%E5%9B%BE%E7%89%87%E7%B3%BB%E5%88%97=%E6%97%A5%E6%9C%ACCOS%E4%B8%AD%E5%9B%BDCOS',
        'https://api.r10086.com/%E6%A8%B1%E9%81%93%E9%9A%8F%E6%9C%BA%E5%9B%BE%E7%89%87api%E6%8E%A5%E5%8F%A3.php?%E5%9B%BE%E7%89%87%E7%B3%BB%E5%88%97=%E6%AD%BB%E5%BA%93%E6%B0%B4%E8%90%9D%E8%8E%89',

    ])
    res = open_ssl(url)
    if res:
        return res.url


def api4(url='https://api.lolimi.cn/API/meinv/api.php'):
    """
    cosplay
    :param url:
    :return:
    """
    res = open_ssl(url)
    if res:
        json_str = res.read().decode('utf-8')
        return json.loads(json_str)['data']['image']


def api5():
    """
    龙图api
    :return:
    """
    base_url = "https://git.acwing.com/Est/dragon/-/raw/main/"
    extensions = ['.jpg', '.png', '.gif']

    batch_choice = random.choice(['batch1/', 'batch2/', 'batch3/'])
    if batch_choice == 'batch1/':
        selected_image_number = random.randint(1, 500)
    elif batch_choice == 'batch2/':
        selected_image_number = random.randint(501, 1000)
    else:
        selected_image_number = random.randint(1001, 1516)
    for ext in extensions:
        image_url = f"{base_url}{batch_choice}dragon_{selected_image_number}_{ext}"
        if open_ssl(image_url):
            return image_url
    return False


def feed_to_string(url):
    try:
        res = feedparser.parse(url)
        # print(time.mktime(time.localtime()) - time.mktime(res.entries[0].updated_parsed))
        if time.mktime(time.localtime()) - time.mktime(res.entries[0].updated_parsed) < 60:
            msg = '''
            _{}_
            {}
            {}
            {}
            {}\n
            '''.format(res.feed.title, res.entries[0].title, res.entries[0].link, res.entries[0].description, res.entries[0].updated)
            return msg
        else:
            return ''
    except Exception as e:
        print(e)
        return False


apis = {
    "色图": [api2],
    "写真": [api3, api4],
    "龙图": [api5]
}


def qq_json(qq):
    return "https://q2.qlogo.cn/headimg_dl?dst_uin={}&spec=100".format(qq)
