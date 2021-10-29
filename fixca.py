from friend_import import *

class RequestManager:
    BASEURL = "http://ranked-osudroid.kro.kr/api/"
    with open("fixca_api_key.txt", 'r') as f:
        key = f.read().strip()

    def __init__(self, bot):
        self.bot = bot
        if bot is not None:
            self.session = bot.session

    async def _post(self, url, data, **kwargs):
        async with self.session.post(BASEURL+url, data=data|kwargs) as res:
            if res.status != 200:
                return False, f'POST {url} failed.', res
            if (resdata := await res.json(encoding='utf-8'))['status'] == 'failed':
                return False, f'POST {url} had had occured', res
            return True, resdata

    async def _get(self, url, data, **kwargs):
        async with self.session.get(BASEURL+url, data=data|kwargs) as res:
            if res.status != 200:
                return f'POST {url} failed.', res
            if (resdata := await res.json(encoding='utf-8'))['status'] == 'failed':
                return f'POST {url} had had occured', res
            return True, resdata
    
    async def recent_record(self, name):
        return await self._post('recentRecord', 
                                key=self.key, name=name)
    
    async def create_playID(self, uuid, mapid, mapsetid):
        return await self._post('createPlayID', 
                                key=self.key, uuid=uuid, mapid=mapid, mapsetid=mapsetid)

    async def get_user(self, uuid):
        return await self._post('userInfo', key=self.key, uuid=uuid)
    
