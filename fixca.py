from friend_import import *

class RequestManager:
    BASEURL = "https://ranked-osudroid.ml/api/"
    with open("fixca_api_key.txt", 'r') as f:
        key = f.read().strip()

    def __init__(self, bot):
        self.bot = bot
        if bot is not None:
            self.session = bot.session

    async def _post(self, url, data=None, **kwargs):
        if data is None:
            data = dict()
        async with self.session.post(self.BASEURL+url, data=data|kwargs) as res:
            if res.status != 200:
                return HttpError('POST', url, res)
            if (resdata := await res.json(encoding='utf-8'))['status'] == 'failed':
                return FixcaError('POST', url, resdata)
            return resdata

    async def _get(self, url, data=None, **kwargs):
        if data is None:
            data = dict()
        async with self.session.get(self.BASEURL+url, data=data|kwargs) as res:
            if res.status != 200:
                return HttpError('GET', url, res)
            if (resdata := await res.json(encoding='utf-8'))['status'] == 'failed':
                return FixcaError('GET', url, resdata)
            return resdata
    
    async def recent_record(self, name):
        return await self._post('recentRecord', 
                                key=self.key, name=name)
    
    async def create_playID(self, uuid, mapid, mapsetid):
        return await self._post('createPlayID', 
                                key=self.key, uuid=uuid, mapid=mapid, mapsetid=mapsetid)

    async def get_user_byuuid(self, uuid):
        return await self._post('userInfo', 
                                key=self.key, uuid=uuid)

    async def get_user_bydiscord(self, d_id):
        return await self._post('userInfoDiscord',
                                key=self.key, discordid=d_id)


class HttpError(Exception):
    def __init__(self, method: str, url: str, data=None):
        super().__init__()
        self.method = method
        self.url = url
        self.data = data

    def __str__(self):
        return f"Getting datas from {self.method} {self.url} failed."

class FixcaError(Exception):
    def __init__(self, method: str, url: str, data=None):
        super().__init__()
        self.method = method
        self.url = url
        self.data = data

    def __str__(self):
        return f"Got datas from {self.method} {self.url} with status 'failed'."
