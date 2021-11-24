from friend_import import *


class HttpError(Exception):
    def __init__(self, method: str, url: str, data=None):
        super().__init__()
        self.method = method
        self.url = url
        self.data = data

    def __str__(self):
        return f"Failed getting datas from {self.method} {self.url} " \
               f"(HttpError : {self.data.status})"


class FixcaError(Exception):
    def __init__(self, method: str, url: str, data=None):
        super().__init__()
        self.method = method
        self.url = url
        self.data = data

    def __str__(self):
        return f"Failed gettng datas from {self.method} {self.url} " \
               f"(FixcaError : {FixcaErrorCode.desc[self.data['code']]})"


class FixcaErrorCode:
    INVALID_KEY = 0
    INVALID_QUERY = 1
    INVALID_SECURE = 2
    DATABASE_ERROR = 3
    INTERNAL_SERVER_ERROR = 4
    USER_NOT_EXIST = 5
    EXPIRED_PLAYID = 6
    PLAYID_NOT_FOUND = 7
    ALREADY_REGISTERED = 8
    PLAYER_NO_RECORDS = 9
    MAP_NOT_EXIST = 10
    TOKEN_NOT_EXIST = 11
    TOKEN_LOCKED = 12
    TOKEN_EXPIRED = 13
    ILLEGAL_LOGIN = 14
    desc = ['INVALID_KEY', 'INVALID_QUERY', 'INVALID_SECURE', 'DATABASE_ERROR', 'INTERNAL_SERVER_ERROR',
            'USER_NOT_EXIST', 'EXPIRED_PLAYID', 'PLAYID_NOT_FOUND', 'ALREADY_REGISTERED', 'PLAYER_NO_RECORDS',
            'MAP_NOT_EXIST', 'TOKEN_NOT_EXIST', 'TOKEN_LOCKED', 'TOKEN_EXPIRED', 'ILLEGAL_LOGIN']


class RequestManager:
    BASEURL = "https://ranked-osudroid.ml/api/"
    ERRORS = (HttpError, FixcaError)
    with open("fixca_api_key.txt", 'r') as f:
        key = f.read().strip()

    def __init__(self, bot):
        self.bot = bot
        if bot is not None:
            self.session = bot.session

    async def _post(self, url, data=None, **kwargs):
        if data is None:
            data = dict()
        data |= kwargs
        print(f'[fixca] Sending POST {url}')
        print(data)
        async with self.session.post(self.BASEURL+url, data=data) as res:
            if res.status != 200:
                print(f'[fixca] POST {url} failed (HTTP {res.status})')
                print(await res.text())
                return HttpError('POST', url, res)
            if not (resdata := await res.json(content_type=None, encoding='utf-8'))['status']:
                print(f'[fixca] POST {url} failed (Error code {resdata["code"]})')
                print(resdata)
                return FixcaError('POST', url, resdata)
            return resdata['output']

    async def _get(self, url, data=None, **kwargs):
        if data is None:
            data = dict()
        data |= kwargs
        print(f'[fixca] Sending GET {url}')
        print(data)
        async with self.session.get(self.BASEURL+url, data=data) as res:
            if res.status != 200:
                print(f'[fixca] GET {url} failed (HTTP {res.status})')
                print(await res.text())
                return HttpError('GET', url, res)
            if not (resdata := await res.json(content_type=None, encoding='utf-8'))['status']:
                print(f'[fixca] GET {url} failed (Errorcode {resdata["code"]})')
                print(resdata)
                return FixcaError('GET', url, resdata)
            return resdata['output']
    
    async def recent_record(self, name):
        return await self._post('recentRecord', 
                                key=self.key, name=name)
    
    async def create_playID(self, uuid, mapid, mapsetid):
        return await self._post('createPlayId',
                                key=self.key, uuid=uuid, mapid=mapid, mapsetid=mapsetid)

    async def get_user_byuuid(self, uuid):
        return await self._post('userInfo', 
                                key=self.key, uuid=uuid)

    async def get_user_bydiscord(self, d_id):
        return await self._post('userInfo',
                                key=self.key, discordid=d_id)

