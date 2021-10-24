from friend_import import *

class RequestManager:
    BASEURL = "http://ranked-osudroid.kro.kr/api/"

    def __init__(self, bot):
        self.bot = bot
        if bot is not None:
            self.session = bot.session

    async def post(self, url, data):
        async with self.session.post(BASEURL+url, data=data) as res:
            if res.status != 200:
                return f'POST {url} failed.', res
            if (resdata := await res.json(encoding='utf-8'))['status'] == 'failed':
                return f'POST {url} had had occured', res
            return resdata

    async def get(self, url, data):
        async with self.session.get(BASEURL+url, data=data) as res:
            if res.status != 200:
                return f'POST {url} failed.', res
            if (resdata := await res.json(encoding='utf-8'))['status'] == 'failed':
                return f'POST {url} had had occured', res
            return resdata
    