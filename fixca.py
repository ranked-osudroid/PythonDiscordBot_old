from friend_import import *

if TYPE_CHECKING:
    from match_new import MatchScrim


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
               f"(FixcaError : {FixcaErrorCode(self.data['code']).name})"


class FixcaMapMode(IntEnum):
    NM = 0
    HD = 1
    HR = 2
    DT = 3
    FM = 4
    TB = 5


class FixcaErrorCode(IntEnum):
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
    PLAYER_NO_TOKENS = 15
    ALREADY_BANNED = 16
    MAPPOOL_NOT_EXIST = 17


class RequestManager:
    BASEURL = "https://ranked-osudroid.ml/api/"
    ERRORS = (HttpError, FixcaError)
    with open("fixca_api_key.txt", 'r') as f:
        __key = f.read().strip()
    __base_data = {'key': __key}

    def __init__(self, bot):
        self.bot = bot
        if bot is not None:
            self.session = bot.session
        else:
            raise AttributeError("bot.session")

    @staticmethod
    def censor(s: str):
        return s.replace(RequestManager.__key, 'key')

    async def _post(self, url, data=None, **kwargs):
        if data is None:
            data = dict()
        data |= kwargs
        print(f"[{get_nowtime_str()}] RequestManager: Sending POST {url}")
        print(data)
        async with self.session.post(self.BASEURL+url, data=data|self.__base_data) as res:
            if res.status != 200:
                print(f'[{get_nowtime_str()}] RequestManager: POST {url} failed (HTTP {res.status})')
                print(await res.text())
                return HttpError('POST', url, res)
            if not (resdata := await res.json(
                    content_type=None, encoding='utf-8', loads=lambda dt: json.loads(dt, parse_float=d)))['status']:
                print(f'[{get_nowtime_str()}] RequestManager: POST {url} failed (Error code {resdata["code"]})')
                print(resdata)
                return FixcaError('POST', url, resdata)
            return resdata['output']

    async def _get(self, url, data=None, **kwargs):
        if data is None:
            data = dict()
        data |= kwargs
        print(f'[{get_nowtime_str()}] RequestManager: Sending GET {url}')
        print(data)
        async with self.session.get(self.BASEURL+url, data=data|self.__base_data) as res:
            if res.status != 200:
                print(f'[{get_nowtime_str()}] RequestManager: GET {url} failed (HTTP {res.status})')
                print(await res.text())
                return HttpError('GET', url, res)
            if not (resdata := await res.json(
                    content_type=None, encoding='utf-8', loads=lambda dt: json.loads(dt, parse_float=d)))['status']:
                print(f'[{get_nowtime_str()}] RequestManager: GET {url} failed (Errorcode {resdata["code"]})')
                print(resdata)
                return FixcaError('GET', url, resdata)
            return resdata['output']
    
    async def recent_record(self, name):
        return await self._post('recentRecord', data={
            'name': name,
        })
    
    async def create_playID(self, uuid, mapid):
        return await self._post('createPlayId', data={
            'uuid': uuid,
            'mapid': mapid,
        })

    async def get_user_byuuid(self, uuid):
        return await self._post('userInfo', data={
            'uuid': uuid,
        })

    async def get_user_bydiscord(self, d_id):
        return await self._post('userInfo', data={
            'discordid': d_id,
        })

    async def upload_elo(self, match: 'MatchScrim', force: bool = False):
        if match is None:
            raise ValueError("match is None")
        if not match.match_end and not force:
            raise Exception("Not allowed to change elo before finishing match.")
        puid, ouid = match.uuid.values()
        prating, orating = match.elo_manager.get_ratings()
        if match.scrim.setscore["RED"] >= match.winfor:
            wu, lu = puid, ouid
            wr, lr = prating, orating
        else:
            wu, lu = ouid, puid
            wr, lr = orating, prating
        return await self._post('changeElo', data={
            'draw': match.scrim.setscore["RED"] == match.scrim.setscore["BLUE"],
            'uuid1': wu,
            'uuid2': lu,
            'elo1': wr,
            'elo2': lr,
        })

    async def get_mappool(self, uuid: str):
        res = await self._post('getMappool', data={
            'uuid': uuid,
        })
        return res["maps"]

    async def create_match(self, player_uuid: str, opponent_uuid: str):
        return await self._post('createMatch', data={
            'uuid1': player_uuid,
            'uuid2': opponent_uuid,
        })

    async def end_match(self, match_id: str, aborted: bool):
        return await self._post('endMatch', data={
            'matchId': match_id,
            'aborted': aborted
        })

    async def upload_record(self, match: 'MatchScrim'):
        # TODO: not finished (None)
        winnerteam = match.scrim.winning_log[-1]
        if len(winnerteam) > 1:
            draw = 0
        elif winnerteam[0] == "BLUE":
            draw = 1
        else:
            draw = -1
        return await self._post('addRound', data={
            'draw': draw,
            'startedTime': match.scrim.round_start_time,
            'matchId': match.match_id,
            'mapid': match.scrim.getmapid()[0],
            'mapset': FixcaMapMode[match.scrim.getmode()].value,
            'redPlayID': match.playID[match.player.id]['playId'],
            'bluePlayID': match.playID[match.opponent.id]['playId'],
        })

    async def expire_playid(self, playid):
        return await self._post('expirePlayId', data={
            'playId': playid
        })

