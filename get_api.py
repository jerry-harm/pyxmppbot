from urllib.request import Request, urlopen
import random
import ssl
import json

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.132 Safari/537.36 QIHU 360SE"}



def api1(url="https://sex.nyan.xyz/api/v2/"):
    """
    色图api sex.nyan.xyz
    :return: url
    """
    r18 = random.randint(0, 1)
    url = url + "?r18=" + str(r18)
    try:
        req = Request(url=url, headers=headers)
        res = urlopen(url=req, context=ssl.create_default_context())
        if int(res.status) == 200:
            json_str = res.read().decode("utf-8")
            return json.loads(json_str)['data'][0]['url']
    except ConnectionError as e:
        print(e)
        return False

def api2(url='https://image.anosu.top/pixiv/json'):
    """
    色图api image.anosu.top
    :param url:
    :return:
    """
    r18 = 2
    url = url + "?r18=" + str(r18)
    try:
        req = Request(url=url, headers=headers)
        res = urlopen(url=req, context=ssl.create_default_context())
        if int(res.status) == 200:
            json_str = res.read().decode("utf-8")
            return json.loads(json_str)[0]['url']
    except ConnectionError as e:
        print(e)
        return False

def api3(url='https://api.r10086.com/%E6%A8%B1%E9%81%93%E9%9A%8F%E6%9C%BA%E5%9B%BE%E7%89%87api%E6%8E%A5%E5%8F%A3.php?%E5%9B%BE%E7%89%87%E7%B3%BB%E5%88%97=%E6%97%A5%E6%9C%ACCOS%E4%B8%AD%E5%9B%BDCOS'):
    """
    cosplay https://api.r10086.com
    :return:
    """
    try:
        req=Request(url,headers=headers)
        res=urlopen(req,context=ssl.create_default_context())
        if int(res.status)==200:
            return res.url

    except ConnectionError as e:
        print(e)
        return False

setu_apis=[api1,api2]
cosplay_apis=[api3]

if __name__ == '__main__':
    print(api2())

