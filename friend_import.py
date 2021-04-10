import asyncio, aiohttp, aiofiles, asyncpool, logging, yarl, \
    datetime, decimal, discord, gspread, random, re, time, \
    traceback, scoreCalc, os, json, osuapi, zipfile, pydrive, shutil, bisect, hashlib
from typing import *
from collections import defaultdict as dd
from collections import deque

from osuapi import OsuApi, AHConnector, HTTPError

from bs4 import BeautifulSoup
from discord.ext import commands, tasks
from google.oauth2.service_account import Credentials

from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive

from help_texts import helptxt

BOT_DEBUG = False

scopes = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive',
]
jsonfile = 'friend-266503-91ab7f0dce62.json'
credentials = Credentials.from_service_account_file(jsonfile, scopes=scopes)
gs = gspread.authorize(credentials)
gs.login()
spreadsheet = "https://docs.google.com/spreadsheets/d/1SA2u-KgTsHcXcsGEbrcfqWugY7sgHIYJpPa5fxNEJYc/edit#gid=0"
doc = gs.open_by_url(spreadsheet)

worksheet = doc.worksheet('data')

gauth = GoogleAuth()
drive_cred = 'credentials.json'
gauth.LoadCredentialsFile(drive_cred)
if gauth.credentials is None:
    gauth.LocalWebserverAuth()
elif gauth.access_token_expired:
    gauth.Refresh()
else:
    gauth.Authorize()
gauth.SaveCredentialsFile(drive_cred)
drive = GoogleDrive(gauth)

drive_folder = drive.ListFile(
    {'q': "title='od' and mimeType='application/vnd.google-apps.folder' and trashed=false"}
).GetList()[0]

intents = discord.Intents.default()
intents.members = True
intents.reactions = True

d = decimal.Decimal

with open("key.txt", 'r') as f:
    token = f.read().strip()

with open("osu_login.json", 'r') as f:
    BASE_LOGIN_DATA = json.load(f)

with open("osu_api_key.txt", 'r') as f:
    api_key = f.read().strip()

with open("fixca_api_key.txt", 'r') as f:
    fixca_key = f.read().strip()

with open("oma_pools.json", 'r', encoding='utf-8-sig') as f:
    maidbot_pools = json.load(f, parse_float=d)

def get_traceback_str(exception):
    return ''.join(traceback.format_exception(type(exception), exception, exception.__traceback__)).strip()

url_base = "http://ops.dgsrz.com/profile.php?uid="
mapr = re.compile(r"(.*?) [-] ([^\[]*) [(](.*?)[)] [\[](.*)[]]")
playr = re.compile(r"(.*) / (.*) / (.*) / (.*)x / (.*)%")
missr = re.compile(r"[{]\"miss\":(\d+), \"hash\":(.*)[}]")

OSU_HOME = "https://osu.ppy.sh/home"
OSU_SESSION = "https://osu.ppy.sh/session"
OSU_BEATMAP_BASEURL = "https://osu.ppy.sh/beatmapsets/"

CHIMU = "https://api.chimu.moe/v1/download/"
chimu_params = {'n': '1'}

BEATCONNECT = "https://beatconnect.io/b/"

downloadpath = os.path.join('songs', '%s.zip')

prohibitted = re.compile(r"[\\/:*?\"<>|]")
multi_spaces_remover = re.compile(r"[ ]+")

parse_fixca = re.compile(r"Various Artists - Ranked Osu!droid Match #\d+ \(Various Mappers\) "
                         r"\[\[(.*?)] (.*) - (.*)\((.*)\)][.]osu")

KST = datetime.timezone(datetime.timedelta(hours=9))
shutdown_time = datetime.time(4, 0, tzinfo=KST)

def get_shutdown_datetime():
    shutdown_datetime = datetime.datetime.now(tz=KST)
    if shutdown_datetime.timetz() > shutdown_time:
        shutdown_datetime += datetime.timedelta(days=1)
    shutdown_datetime = shutdown_datetime.replace(
        hour=shutdown_time.hour,
        minute=shutdown_time.minute,
        second=shutdown_time.second,
        microsecond=shutdown_time.microsecond
    )
    return shutdown_datetime

def getd(n: Union[int, float, str]):
    return d(str(n))

def halfup(n: d):
    return n.quantize(getd('1.'), rounding=decimal.ROUND_HALF_UP)

def neroscorev2(maxscore: d, score: d, acc: d, miss: d):
    s = 600000 * score / maxscore
    a = 400000 * (acc / 100) ** 4
    return halfup((s + a) * (1 - getd(0.003) * miss))

def jetonetv2(maxscore: d, score: d, acc: d, miss: d):
    s = 500000 * score / maxscore
    a = 500000 * (max(acc - 80, getd('0')) / 20) ** 2
    return halfup(s + a)

def osuv2(maxscore: d, score: d, acc: d, miss: d):
    s = 700000 * score / maxscore
    a = 300000 * (acc / 100) ** 10
    return halfup(s + a)

def v1(maxscore: d, score: d, acc: d, miss: d):
    return score

v2dict = {
    None    : v1,
    'nero2' : neroscorev2,
    'jet2'  : jetonetv2,
    'osu2'  : osuv2,
}

blank = '\u200b'

rkind = ['number', 'artist', 'author', 'title', 'diff']
rmeta = r'\$()*+.?[^{|'

analyze = re.compile(r"(?P<artist>.*) [-] (?P<title>.*) [(](?P<author>.*)[)] \[(?P<diff>.*)]")

def makefull(**kwargs: str):
    return f"{kwargs['artist']} - {kwargs['title']} ({kwargs['author']}) [{kwargs['diff']}]"

def dice(s: str):
    s = s.partition('d')
    if s[1] == '':
        return None
    return tuple(str(random.randint(1, int(s[2]))) for _ in range(int(s[0])))

def is_owner():
    async def predicate(ctx):
        return ctx.author.id == 327835849142173696
    return commands.check(predicate)

visibleinfo = ['artist', 'title', 'author', 'diff']
modes = ['NM', 'HD', 'HR', 'DT', 'FM', 'TB']
moder = re.compile(r"(NM|HD|HR|DT|FM|TB)")
modetoint = {
    'None': 0,
    'Hidden': 1,
    'HardRock': 2,
    'DoubleTime': 4,
    'NoFail': 8,
    'HalfTime': 16,
    'NightCore': 32,
    'Easy': 64,
    'Precise': 128
}
modeabbrev = {
    'Easy': 'EZ',
    'NoFail': 'NF',
    'HalfTime': 'HF',
    'HardRock': 'HR',
    'Hidden': 'HD',
    'DoubleTime': 'DT',
    'NightCore': 'NC',
    'Precise': 'PR'
}
infotoint = {
    'artist': 1,
    'title': 2,
    'author': 4,
    'diff': 8,
    'mode': 16
}

def modetointfunc(_modes: Iterable[str]) -> int:
    r = 0
    for md in _modes:
        if modetoint.get(md):
            r |= modetoint[md]
    return r

def inttomode(i: Optional[int], sep: str = '') -> str:
    if i:
        r = []
        for md in modeabbrev.keys():
            if i & modetoint[md]:
                r.append(modeabbrev[md])
        return sep.join(r)
    elif i is None:
        return 'N/A'
    else:
        return 'NM'

async def osu_login(session):
    async with session.get(OSU_HOME) as page:
        if page.status != 200:
            print(f'홈페이지 접속 실패 ({page.status})')
            print(page.raw_headers)
            await session.close()
            return False

        csrf = session.cookie_jar.filter_cookies(yarl.URL(OSU_HOME)).get('XSRF-TOKEN').value
        login_info = {**BASE_LOGIN_DATA, **{'_token': csrf}}

        async with session.post(OSU_SESSION, data=login_info, headers={'referer': OSU_HOME}) as req:
            if req.status != 200:
                print(f'로그인 실패 ({req.status})')
                await session.close()
                return False
            print('로그인 성공')
    return True

class BotOff(Exception):
    def __init__(self):
        super().__init__("Shutdown is coming!")

async def auto_off(shutdown_datetime):
    try:
        life_time = (shutdown_datetime - datetime.datetime.now(KST)).total_seconds()
        print(f'[@] Shutdown after {life_time} second(s).')
        await asyncio.sleep(life_time)
        raise BotOff()
    except asyncio.CancelledError:
        return
    except BotOff:
        raise

RANK_EMOJI = {
    'A': "<:rankingA:829276952649138186>",
    'B': "<:rankingB:829276952728174612>",
    'C': "<:rankingC:829276952229052488>",
    'D': "<:rankingD:829276952778113044>",
    'S': "<:rankingS:829276952748883998>",
    'SH': "<:rankingSH:829276952622923786>",
    'X': "<:rankingX:829276952841158656>",
    'XH': "<:rankingXH:829276952430772255>",
    None: "<:questionmark:665176979414188052>"
}

rankFilenameR = re.compile('assets/images/ranking-(.+)-small[.]png')

ELO_RANK_NAMES = ['Bronze', 'Silver', 'Gold', 'Platinum', 'Diamond', 'Master']
ELO_RANK_SCORE_BOUNDARY = [1500, 2000, 2500, 3000, 3500]
ELO_INITIAL_RANK_BOUNDARY = [0, 100, 300, 700, 1500, 6500]
ELO_INITIAL_RANK_RATE = [d('2'), d('1'), d('.5'), d('.25'), d('.04')]

def get_elo_rank(elov: Union[d, int]):
    return ELO_RANK_NAMES[bisect.bisect(ELO_RANK_SCORE_BOUNDARY, elov)]

def get_initial_elo(rank: Union[d, int]):
    idx = bisect.bisect_left(ELO_INITIAL_RANK_BOUNDARY, rank) - 1
    if idx == 5:
        return d('1000')
    else:
        rate = ELO_INITIAL_RANK_RATE[idx]
        return d('2000') - d('200') * idx - rate * (rank - ELO_INITIAL_RANK_BOUNDARY[idx])

ELO_K = 50
ELO_STDV = 2500

ELO_RANK_ENTRY_COST = [-10, -5, 0, 5, 10, 15]

def get_elo_rank_entry_cost(elov: Union[d, int]):
    return ELO_RANK_ENTRY_COST[bisect.bisect(ELO_RANK_SCORE_BOUNDARY, elov)]

ELO_MID_RATING = d('1500')

def elo_convert(x):
    return (x - 1000) * d('2.1') + 1200

def elo_convert_rev(x):
    return (x - 1200) / d('2.1') + 1000

