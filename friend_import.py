import asyncio, aiohttp, aiofiles, asyncpool, logging, yarl, \
    datetime, decimal, discord, gspread, random, re, time, \
    traceback, scoreCalc, os, elo_rating, json, osuapi, zipfile, pydrive, shutil
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
missr = re.compile(r"[{]\"miss\":(\d+), \"hash\":.*[}]")

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

async def getrecent(_id: int) -> Optional[Tuple[Sequence[AnyStr], Sequence[AnyStr], Sequence[AnyStr]]]:
    url = url_base + str(_id)
    async with aiohttp.ClientSession() as s:
        html = await s.get(url)
    bs = BeautifulSoup(await html.text(), "html.parser")
    recent = bs.select_one("#activity > ul > li:nth-child(1)")
    recent_mapinfo = recent.select("a.clear > strong.block")[0].text
    recent_playinfo = recent.select("a.clear > small")[0].text
    recent_miss = recent.select("#statics")[0].text
    rmimatch = mapr.match(recent_mapinfo)
    if rmimatch is None:
        return None
    return (rmimatch.groups(),
            playr.match(recent_playinfo).groups(),
            missr.match(recent_miss).groups())

async def get_rank(_id: int):
    url = url_base + str(_id)
    async with aiohttp.ClientSession() as s:
        html = await s.get(url)
        bs = BeautifulSoup(await html.text(), "html.parser")
        rank = bs.select_one("#content > section > section > section > aside.aside-lg.bg-light.lter.b-r > "
                             "section > section > div > div.panel.wrapper > div > div:nth-child(1) > a > span").text
        return int(rank)

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
infotoint = {
    'artist': 1,
    'title': 2,
    'author': 4,
    'diff': 8,
    'mode': 16
}

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
