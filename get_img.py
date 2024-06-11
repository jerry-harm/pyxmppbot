from urllib.request import Request, urlopen
import random
import ssl
import json

# api_lists = [
#     "https://image.anosu.top/pixiv/direct",
#     "https://moe.jitsu.top/img",
#     "https://sex.nyan.xyz/api/v2/img",
#     "https://api.r10086.com/%E6%A8%B1%E9%81%93%E9%9A%8F%E6%9C%BA%E5%9B%BE%E7%89%87api%E6%8E%A5%E5%8F%A3.php?%E5%9B%BE%E7%89%87%E7%B3%BB%E5%88%97=%E5%B0%91%E5%A5%B3%E5%86%99%E7%9C%9F1",
#     "https://api.r10086.com/%E6%A8%B1%E9%81%93%E9%9A%8F%E6%9C%BA%E5%9B%BE%E7%89%87api%E6%8E%A5%E5%8F%A3.php?%E5%9B%BE%E7%89%87%E7%B3%BB%E5%88%97=%E6%97%A5%E6%9C%ACCOS%E4%B8%AD%E5%9B%BDCOS",
#     "https://api.r10086.com/%E6%A8%B1%E9%81%93%E9%9A%8F%E6%9C%BA%E5%9B%BE%E7%89%87api%E6%8E%A5%E5%8F%A3.php?%E5%9B%BE%E7%89%87%E7%B3%BB%E5%88%97=%E6%AD%BB%E5%BA%93%E6%B0%B4%E8%90%9D%E8%8E%89"
# ]

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.132 Safari/537.36 QIHU 360SE"}


def api1():
    """
    色图api sex.nyan.xyz
    :param:
    :return:
    """
    url = "https://sex.nyan.xyz/api/v2/"
    r18 = random.randint(0, 1)
    url = url + "?r18=" + str(r18)
    try:
        req = Request(url=url, headers=headers)
        res = urlopen(url=req, context=ssl.create_default_context())
        if int(res.status) == 200:
            json_str = res.read().decode("utf-8")
            return json.loads(json_str)['data'][0]
    except ConnectionError as e:
        print(e)
        return False


# def get_rand_img():
#     """
#     chose a random api
#     :return:
#     """
#     url = api_lists[random.randint(0, len(api_lists) - 1)]
#     print(url)
#     get_real_url(url)

if __name__ == '__main__':
    print(api1())

