import asyncio, aiohttp, aiofiles, asyncpool, logging, yarl, \
    datetime, decimal, discord, gspread, random, re, time, \
    traceback, scoreCalc, os, elo_rating, json, osuapi, zipfile, pydrive, shutil
from typing import *
from collections import defaultdict as dd
from collections import deque

from osuapi import OsuApi, AHConnector, HTTPError

from bs4 import BeautifulSoup
from discord.ext import commands
from google.oauth2.service_account import Credentials

from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive

from help_texts import *

####################################################################################################################

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
app = commands.Bot(command_prefix='m;', help_command=None, intents=intents)

d = decimal.Decimal

ses: Optional[aiohttp.ClientSession] = None
api: Optional[OsuApi] = None

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

####################################################################################################################

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


####################################################################################################################


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


####################################################################################################################

class Timer:
    def __init__(self, ch: discord.TextChannel, name: str, seconds: Union[float, d], async_callback=None, args=None):
        timers[name] = self
        self.channel: discord.TextChannel = ch
        self.name: str = name
        self.seconds: float = seconds
        self.start_time: datetime.datetime = datetime.datetime.utcnow()
        self.loop = asyncio.get_event_loop()
        self.message: Optional[discord.Message] = None
        self.done = False
        self.callback = async_callback
        self.args = args

        self.task: asyncio.Task = loop.create_task(self.run())

    async def run(self):
        try:
            self.message = await self.channel.send(embed=discord.Embed(
                title="Timer start!",
                description=f"Timer Name : `{self.name}`\n"
                            f"Time Limit : {self.seconds}",
                color=discord.Colour.dark_orange()
            ))
            await asyncio.sleep(self.seconds)
            await self.timeover()
        except asyncio.CancelledError:
            await self.cancel()
        except BaseException as ex_:
            print(get_traceback_str(ex_))
            raise ex_

    async def edit(self):
        if self.task.done():
            return
        await self.message.edit(embed=discord.Embed(
                title="TIMER RUNNING...",
                description=f"Timer Name : `{self.name}`\n"
                            f"Time Limit : {self.seconds}\n"
                            f"Time Left : {self.left_sec()}",
                color=discord.Colour.dark_orange()
            ))

    async def timeover(self):
        await self.message.edit(embed=discord.Embed(
            title="TIME OVER!",
            description=f"Timer Name : `{self.name}`\n"
                        f"Time Limit : {self.seconds}",
            color=discord.Colour.dark_grey()
        ))
        await self.call_back()

    async def cancel(self):
        if self.task.done() or self.task.cancelled():
            return
        self.task.cancel()
        await self.message.edit(embed=discord.Embed(
            title="TIMER STOPPED!",
            description=f"Timer Name : `{self.name}`\n"
                        f"Time Limit : {self.seconds}\n"
                        f"Time Left : {self.left_sec()}",
            color=discord.Colour.dark_red()
        ))
        await self.call_back()

    async def call_back(self):
        self.done = True
        del timers[self.name]
        if self.callback is None:
            return
        if self.args:
            await self.callback(self.task.cancelled(), *self.args)
        else:
            await self.callback(self.task.cancelled())

    def left_sec(self) -> float:
        return self.seconds - ((datetime.datetime.utcnow() - self.start_time).total_seconds())


####################################################################################################################


async def getusername(x: int) -> str:
    if member_names.get(x) is None:
        user = app.get_user(x)
        if user is None:
            user = await app.fetch_user(x)
        member_names[x] = user.name
    return member_names[x]


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

class Scrim:
    def __init__(self, channel: discord.TextChannel):
        self.loop = asyncio.get_event_loop()
        self.channel: discord.TextChannel = channel
        self.start_time = datetime.datetime.utcnow().strftime('%Y%m%d%H%M%S%f')

        self.match_task: Optional[asyncio.Task] = None

        self.team: Dict[str, Set[int]] = dict()
        # teamname : {member1_id, member2_id, ...}
        self.players: Set[int] = set()
        # {member1_id, member2_id, ...}
        self.findteam: Dict[int, str] = dict()
        # member_id : teamname
        self.setscore: Dict[str, int] = dict()
        # teamname : int
        self.score: Dict[int, Tuple[d, d, d]] = dict()
        # member_id : (score, acc, miss)

        self.map_artist: Optional[str] = None
        self.map_author: Optional[str] = None
        self.map_title: Optional[str] = None
        self.map_diff: Optional[str] = None
        self.map_time: Optional[d, int] = None

        self.map_number: Optional[str] = None
        self.map_mode: Optional[str] = None
        self.map_auto_score: Optional[int, dd] = None
        self.form: Optional[List[Union[re.Pattern, List[str]]]] = None

        self.availablemode: Dict[str, Iterable[int]] = {
            'NM': {0, 8},
            'HR': {2, 10},
            'HD': {1, 9},
            'DT': {4, 5, 12, 13},
            'FM': {0, 1, 2, 3, 8, 9, 10, 11},
            'TB': {0, 1, 2, 3, 8, 9, 10, 11},
        }

        self.setfuncs: Dict[str, Callable[[str], NoReturn]] = {
            'artist': self.setartist,
            'title' : self.settitle,
            'author': self.setauthor,
            'diff'  : self.setdiff,
            'number': self.setnumber,
            'mode'  : self.setmode,
            'autosc': self.setautoscore,
        }

        self.getfuncs: Dict[str, Callable[[], str]] = {
            'artist': self.getartist,
            'title' : self.gettitle,
            'author': self.getauthor,
            'diff'  : self.getdiff,
            'number': self.getnumber,
            'mode'  : self.getmode,
            'autosc': self.getautoscore,
        }

        self.log: List[str] = []
        self.timer: Optional[Timer] = None

    async def maketeam(self, name: str, do_print: bool = True):
        if self.team.get(name) is not None:
            await self.channel.send(embed=discord.Embed(
                title=f"Team {name} already exists!",
                description=f"Now team list:\n{chr(10).join(self.team.keys())}",
                color=discord.Colour.dark_blue()
            ))
        else:
            self.team[name] = set()
            self.setscore[name] = 0
            if do_print:
                await self.channel.send(embed=discord.Embed(
                    title=f"Added Team {name}.",
                    description=f"Now team list:\n{chr(10).join(self.team.keys())}",
                    color=discord.Colour.blue()
                ))

    async def removeteam(self, name: str, do_print: bool = True):
        if self.team.get(name) is None:
            await self.channel.send(embed=discord.Embed(
                title=f"There's no Team {name}.",
                description=f"Now team list:\n{chr(10).join(self.team.keys())}",
                color=discord.Colour.dark_blue()
            ))
        else:
            for p in self.team[name]:
                del self.findteam[p]
            del self.team[name], self.setscore[name]
            if do_print:
                await self.channel.send(embed=discord.Embed(
                    title=f"Removed Team {name}.",
                    description=f"Now team list:\n{chr(10).join(self.team.keys())}",
                    color=discord.Colour.blue()
                ))

    async def addplayer(self, name: str, member: Optional[discord.Member], do_print: bool = True):
        if not member:
            return
        mid = member.id
        temp = self.findteam.get(mid)
        if temp:
            await self.channel.send(embed=discord.Embed(
                title=f"Player {member.name} is already in Team {temp}!",
                description=f"Please leave your team first (`m;out`) and try again."
            ))
        elif self.team.get(name) is None:
            await self.channel.send(embed=discord.Embed(
                title=f"There's no Team {name}.",
                description=f"Now team list:\n{chr(10).join(self.team.keys())}",
                color=discord.Colour.dark_blue()
            ))
        else:
            self.findteam[mid] = name
            self.team[name].add(mid)
            self.players.add(mid)
            self.score[mid] = (getd(0), getd(0), getd(0))
            if do_print:
                await self.channel.send(embed=discord.Embed(
                    title=f"Player {member.name} participates into Team {name}!",
                    description=f"Now player list of Team {name}:\n"
                                f"{chr(10).join([(await getusername(pl)) for pl in self.team[name]])}",
                    color=discord.Colour.blue()
                ))

    async def removeplayer(self, member: Optional[discord.Member], do_print: bool = True):
        if not member:
            return
        mid = member.id
        temp = self.findteam.get(mid)
        if mid not in self.players:
            await self.channel.send(embed=discord.Embed(
                title=f"Player {member.name} is participating in NO team!",
                description=f"You participate first."
            ))
        else:
            del self.findteam[mid], self.score[mid]
            self.team[temp].remove(mid)
            self.players.remove(mid)
            if do_print:
                await self.channel.send(embed=discord.Embed(
                    title=f"Player {member.name} is leaving Team {temp}.",
                    description=f"Now player list of Team {temp}:\n"
                                f"{chr(10).join([(await getusername(pl)) for pl in self.team[temp]])}",
                    color=discord.Colour.blue()
                ))

    async def addscore(self, member: Optional[discord.Member], score: int, acc: float, miss: int):
        if not member:
            return
        mid = member.id
        if mid not in self.players:
            await self.channel.send(embed=discord.Embed(
                title=f"Player {member.name} is participating in NO team!",
                description=f"You participate first."
            ))
        else:
            self.score[mid] = (getd(score), getd(acc), getd(miss))
            await self.channel.send(embed=discord.Embed(
                title=f"Player {member.name}'(s) score is modified.",
                description=f"Team {self.findteam[mid]} <== {score}, {acc}%, {miss}xMISS",
                color=discord.Colour.blue()
            ))

    async def removescore(self, member: Optional[discord.Member]):
        if not member:
            return
        mid = member.id
        if mid not in self.players:
            await self.channel.send(embed=discord.Embed(
                title=f"Player {member.name} is participating in NO team!",
                description=f"You participate first."
            ))
        else:
            self.score[mid] = (getd(0), getd(0), getd(0))
            await self.channel.send(embed=discord.Embed(
                title=f"Player {member.name}'(s) score is deleted.",
                color=discord.Colour.blue()
            ))

    async def submit(self, calcmode: Optional[str]):
        if v2dict.get(calcmode) is None:
            await self.channel.send(embed=discord.Embed(
                title="Unknown Calculate Mode!",
                description="It should be (Empty), `nero2`, `jet2`, or `osu2`"
            ))
            return
        elif calcmode and (self.getautoscore() == -1):
            await self.channel.send(embed=discord.Embed(
                title="Autoplay score is needed to calculate V2-kind score!",
                description="Modify it by using `m;mapscore`."
            ))
            return
        calcf = v2dict[calcmode]
        resultmessage = await self.channel.send(embed=discord.Embed(
            title="Calculating...",
            color=discord.Colour.orange()
        ))
        calculatedscores = dict()
        for p in self.score:
            calculatedscores[p] = calcf(self.map_auto_score, *self.score[p])
        teamscore = dict()
        for t in self.team:
            teamscore[t] = 0
            for p in self.team[t]:
                teamscore[t] += calculatedscores[p]
        winnerteam = list(filter(
            lambda x: teamscore[x] == max(teamscore.values()),
            teamscore.keys()
        ))
        for w in winnerteam:
            self.setscore[w] += 1
        desc = ', '.join('"'+t+'"' for t in winnerteam)
        sendtxt = discord.Embed(
            title="========= ! ROUND END ! =========",
            description=f"__**Team {desc} get(s) a point!**__",
            color=discord.Colour.red()
        )
        sendtxt.add_field(
            name="Map Info",
            value='`'+self.getmapfull()+'`',
            inline=False
        )
        sendtxt.add_field(
            name="Map Number",
            value=self.getnumber(),
            inline=False
        )
        sendtxt.add_field(
            name=blank,
            value='='*20+'\n'+blank,
            inline=False
        )
        for t in teamscore:
            sendtxt.add_field(
                name=f"*Team {t} total score : {teamscore[t]}*",
                value='\n'.join(
                    [f"{await getusername(p)} : {' / '.join(str(x) for x in self.score[p])} = {calculatedscores[p]}"
                     for p in self.team[t]])+'\n',
                inline=False
            )
        sendtxt.add_field(
            name=blank,
            value='='*20+'\n'+blank,
            inline=False
        )
        sendtxt.add_field(
            name="__Now team score:__",
            value='\n'.join([f"**{t} : {self.setscore[t]}**" for t in teamscore]),
            inline=False
        )
        await resultmessage.edit(embed=sendtxt)
        logtxt = [f'Map         : {self.getmapfull()}', f'MapNick     : {self.map_number}',
                  f'CalcFormula : {calcmode if calcmode else "V1"}', f'Winner Team : {desc}']
        for t in self.team:
            logtxt.append(f'\nTeam {t} = {teamscore[t]}')
            for p in self.team[t]:
                logtxt.append(f"Player {await getusername(p)} = {calculatedscores[p]} "
                              f"({' / '.join(str(x) for x in self.score[p])})")
        self.log.append('\n'.join(logtxt))
        self.resetmap()

    def resetmap(self):
        self.map_artist = None
        self.map_author = None
        self.map_title = None
        self.map_diff = None
        self.map_number = None
        self.map_mode = None
        self.map_auto_score = None
        self.map_time = None
        for p in self.score:
            self.score[p] = (getd(0), getd(0), getd(0))

    def setartist(self, artist: str):
        self.map_artist = artist

    def getartist(self) -> str:
        return self.map_artist if self.map_artist else ''

    def settitle(self, title: str):
        self.map_title = title

    def gettitle(self) -> str:
        return self.map_title if self.map_title else ''

    def setauthor(self, author: str):
        self.map_author = author

    def getauthor(self) -> str:
        return self.map_author if self.map_author else ''

    def setdiff(self, diff: str):
        self.map_diff = diff

    def getdiff(self) -> str:
        return self.map_diff if self.map_diff else ''

    def setnumber(self, number: str):
        self.map_number = number

    def getnumber(self) -> str:
        return self.map_number if self.map_number else '-'

    def setmode(self, mode: str):
        self.map_mode = mode

    def getmode(self) -> str:
        return self.map_mode if self.map_mode else '-'

    def setautoscore(self, score: Union[int, d]):
        self.map_auto_score = score

    def getautoscore(self) -> Union[int, d]:
        return self.map_auto_score if self.map_auto_score else -1

    def setmaptime(self, t: Union[int, d]):
        self.map_time = t

    def getmaptime(self) -> Union[int, d]:
        return self.map_time if self.map_time else -1

    def setmapinfo(self, infostr: str):
        m = analyze.match(infostr)
        if m is None:
            return True
        for k in visibleinfo:
            if m.group(k) != '':
                self.setfuncs[k](m.group(k))

    def getmapinfo(self) -> Dict[str, str]:
        res = dict()
        for k in visibleinfo:
            res[k] = self.getfuncs[k]()
        return res

    def getmapfull(self):
        return makefull(**self.getmapinfo())

    async def setform(self, formstr: str):
        args = list()
        for k in rkind:
            findks = re.findall(k, formstr)
            if len(findks) > 1:
                await self.channel.send(embed=discord.Embed(
                    title="Each words should be entered only ONCE.",
                    color=discord.Colour.dark_red()
                ))
                return
            elif len(findks):
                args.append(k)
        for c in rmeta:
            formstr = formstr.replace(c, '\\' + c)
        for a in args:
            formstr = formstr.replace(a, f'(?P<{a}>.*?)')
        self.form = [re.compile(formstr), args]
        await self.channel.send(embed=discord.Embed(
            title="Form set!",
            description=f"RegEx pattern : `{self.form[0].pattern}`",
            color=discord.Colour.blue()
        ))

    def setmoderule(
            self,
            nm: Optional[Iterable[int]],
            hd: Optional[Iterable[int]],
            hr: Optional[Iterable[int]],
            dt: Optional[Iterable[int]],
            fm: Optional[Iterable[int]],
            tb: Optional[Iterable[int]]
    ):
        if nm:
            self.availablemode['NM'] = nm
        if hd:
            self.availablemode['HD'] = hd
        if hr:
            self.availablemode['HR'] = hr
        if dt:
            self.availablemode['DT'] = dt
        if fm:
            self.availablemode['FM'] = fm
        if tb:
            self.availablemode['TB'] = tb

    async def onlineload(self, checkbit: Optional[int] = None):
        desc = '====== < Process LOG > ======'
        resultmessage: discord.Message = await self.channel.send(embed=discord.Embed(
            title="Processing...",
            description=desc,
            color=discord.Colour.orange()
        ))
        for team in self.team:
            for player in self.team[team]:
                desc += '\n'
                await resultmessage.edit(embed=discord.Embed(
                    title="Processing...",
                    description=desc,
                    color=discord.Colour.orange()
                ))
                if uids.get(player) is None:
                    desc += f"Failed : " \
                            f"{await getusername(player)}'s UID is not found."
                    continue
                player_recent_info = await getrecent(uids[player])
                if player_recent_info is None:
                    desc += f"Failed : " \
                            f"{await getusername(player)}'s recent play info can't be parsed."
                    continue
                p = dict()
                p['artist'], p['title'], p['author'], p['diff'] = player_recent_info[0]
                p['score'] = int(player_recent_info[1][1].replace(',', ''))
                p['acc'] = float(player_recent_info[1][4])
                p['miss'] = int(float(player_recent_info[2][0]))
                p['modes'] = set(player_recent_info[1][2].split(', '))
                flag = False
                if self.form is not None:
                    checkbit = 0
                    m = self.form[0].match(p['diff'])
                    if m is None:
                        desc += f"Failed : " \
                                f"In {await getusername(player)}'s recent play info, " \
                                f"its difficulty name does NOT fit to the format. " \
                                f"(Its difficulty : {p['diff']})"
                        continue
                    for k in self.form[1]:
                        if k == 'number':
                            mnum = self.map_number.split(';')[-1]
                            pnum = m.group(k)
                            if mnum != pnum:
                                flag = True
                                desc += f"Failed : " \
                                        f"In {await getusername(player)}'s recent play info, " \
                                        f"its number is wrong. (Its number : {pnum})"
                                break
                            continue
                        p[k] = m.group(k)
                        checkbit |= infotoint[k]
                if checkbit is None:
                    checkbit = 31
                for k in ['artist', 'title', 'author', 'diff']:
                    if flag:
                        break
                    if checkbit & infotoint[k]:
                        nowk = self.getfuncs[k]()
                        nowk_edited = prohibitted.sub('', nowk).replace('\'', ' ').replace('_', ' ')
                        nowk_edited = multi_spaces_remover.sub(' ', nowk_edited)
                        if nowk_edited != p[k]:
                            flag = True
                            desc += f"Failed : " \
                                    f"In {await getusername(player)}'s recent play info, " \
                                    f"its {k} is wrong." \
                                    f"(Now {k} : {nowk_edited} {'(`'+nowk+'`) ' if nowk!=nowk_edited else ''}/ " \
                                    f"Its {k} : {p[k]})"
                if flag:
                    continue
                if self.map_mode is not None:
                    pmodeint = 0
                    for md in p['modes']:
                        if modetoint.get(md):
                            pmodeint |= modetoint[md]
                    if pmodeint not in self.availablemode[self.map_mode]:
                        desc += f"Failed : " \
                                f"In {await getusername(player)}'s recent play info, " \
                                f"its mode is NOT allowed in now map mode. " \
                                f"(Now mode numbers allowed to use : {self.availablemode[self.map_mode]} / " \
                                f"Its mode number : {pmodeint})"
                        continue
                self.score[player] = (getd(p['score']), getd(p['acc']), getd(p['miss']))
                desc += f"Success : " \
                        f"Player {await getusername(player)}'s score = " \
                        f"{self.score[player][0]}, {self.score[player][1]}%, {self.score[player][2]}xMISS"
        await resultmessage.edit(embed=discord.Embed(
            title="Calculation finished!",
            description=desc,
            color=discord.Colour.green()
        ))

    async def end(self):
        winnerteam = list(filter(
            lambda x: self.setscore[x] == max(self.setscore.values()),
            self.setscore.keys()
        ))
        sendtxt = discord.Embed(
            title="========= ! MATCH END ! =========",
            description="Team " + ', '.join(f"\"{w}\"" for w in winnerteam) + " WON!",
            color=discord.Colour.magenta()
        )
        sendtxt.add_field(
            name=blank,
            value='='*20+'\n'+blank,
            inline=False
        )
        sendtxt.add_field(
            name="THE RESULT:",
            value='\n'.join(f"{t} : {self.setscore[t]}" for t in self.setscore)
        )
        sendtxt.add_field(
            name=blank,
            value='='*20+'\n'+blank,
            inline=False
        )
        sendtxt.add_field(
            name="GGWP! Thank you for the match!",
            value='The match will be reset.\n'
                  'You can download this file and see the match logs.',
            inline=False
        )
        filename = f'scrim{self.start_time}.log'
        with open(filename, 'w') as _f:
            _f.write('\n\n====================\n\n'.join(self.log))
        with open(filename, 'rb') as _f:
            await self.channel.send(embed=sendtxt, file=discord.File(_f, filename))
        os.remove(filename)
        return winnerteam

    async def do_match_start(self):
        if self.match_task is None or self.match_task.done():
            self.match_task = asyncio.create_task(self.match_start())
        else:
            await self.channel.send(embed=discord.Embed(
                title="Match is already processing!",
                description="Try again after the match ends.",
                color=discord.Colour.dark_red()
            ))

    async def match_start(self):
        try:
            if self.map_time is None:
                await self.channel.send(embed=discord.Embed(
                    title="The length of the map is not modified!",
                    description="Use `m;maptime` and try again.",
                    color=discord.Colour.dark_red()
                ))
                return
            try:
                await self.channel.send(embed=discord.Embed(
                    title="MATCH START!",
                    description=f"Map Info : `{self.getmapfull()}`\n"
                                f"Map Number : {self.getnumber()} / Map Mode : {self.getmode()}\n"
                                f"Map SS Score : {self.getautoscore()} / Map Length : {self.getmaptime()} sec.",
                    color=discord.Colour.from_rgb(255, 255, 0)
                ))
                a = self.map_time
                extra_rate = d('1')
                if self.getmode() == 'DT':
                    extra_rate = d('1') / d('1.5')
                self.timer = Timer(self.channel, f"{self.start_time}_{self.getnumber()}",
                                   int(self.getmaptime() * extra_rate))
                await self.timer.task
                timermessage = await self.channel.send(embed=discord.Embed(
                    title=f"MAP TIME OVER!",
                    color=discord.Colour.from_rgb(128, 128, 255)
                ))
                for i in range(30, -1, -1):
                    await timermessage.edit(embed=discord.Embed(
                        title=f"MAP TIME OVER!",
                        description=f"There's additional {i} second(s) left.",
                        color=discord.Colour.from_rgb(128, 128, 255)
                    ))
                    await asyncio.sleep(1)
                await self.channel.send(embed=discord.Embed(
                    title=f"MAP EXTRA TIME OVER!",
                    description="Online loading...",
                    color=discord.Colour.from_rgb(128, 128, 255)
                ))
                await self.onlineload()
                await self.submit('nero2')
            except asyncio.CancelledError:
                await self.channel.send(embed=discord.Embed(
                    title="Match Aborted!",
                    color=discord.Colour.dark_red()
                ))
                return
        except BaseException as ex_:
            print(get_traceback_str(ex_))
            raise ex_


member_names: Dict[int, str] = dict()
datas: dd[Dict[int, dd[Dict[int, Dict[str, Union[int, Scrim]]], Callable[[], Dict]]]] = \
    dd(lambda: dd(lambda: {'valid': False, 'scrim': None}))
uids: dd[int, int] = dd(int)
ratings: dd[int, d] = dd(d)
timers: dd[str, Optional[Timer]] = dd(lambda: None)
timer_count = 0

with open('uids.txt', 'r') as f:
    while data := f.readline():
        discordid, userid = data.split(' ')
        uids[int(discordid)] = int(userid)

with open('ratings.txt', 'r') as f:
    while data := f.readline():
        userid, r = data.split(' ')
        ratings[int(userid)] = getd(r)

####################################################################################################################

class Match:
    def __init__(self, player: discord.Member, opponent: discord.Member, bo: int = 7):
        self.made_time = datetime.datetime.utcnow().strftime("%y%m%d%H%M%S%f")
        self.channel: Optional[discord.TextChannel] = None
        self.player = player
        self.opponent = opponent

        self.mappoolmaker: Optional[MappoolMaker] = None
        self.map_order: List[str] = []
        self.map_tb: Optional[str] = None

        self.scrim: Optional[Scrim] = None
        self.timer: Optional[Timer] = None
        self.diff_form: str = '[number] artist - title [diff]'

        self.round = -1
        # -2 = 매치 생성 전
        # -1 = 플레이어 참가 대기
        # 0 = 맵풀 다운로드 대기
        # n = n라운드 준비 대기
        self.bo = bo
        self.winfor = (bo / d('2')).to_integral(rounding=decimal.ROUND_HALF_UP)
        self.abort = False

        self.player_ELO = ratings[uids[self.player.id]]
        self.opponent_ELO = ratings[uids[self.opponent.id]]
        self.elo_manager = elo_rating.EloRating(self.player_ELO, self.opponent_ELO)

        self.player_ready: bool = False
        self.opponent_ready: bool = False

        self.match_task: Optional[asyncio.Task] = None

    def get_debug_txt(self):
        if self.match_task.exception() is not None:
            return get_traceback_str(self.match_task.exception())

    async def switch_ready(self, subj):
        r_ = None
        if self.channel is None:
            return
        if self.player == subj:
            if self.player_ready:
                self.player_ready = r_ = False
            else:
                self.player_ready = r_ = True
        elif self.opponent == subj:
            if self.opponent_ready:
                self.opponent_ready = r_ = False
            else:
                self.opponent_ready = r_ = True
        else:
            return
        if r_:
            await self.channel.send(embed=discord.Embed(
                title=f"{subj} ready!",
                color=discord.Colour.green()
            ))
        else:
            await self.channel.send(embed=discord.Embed(
                title=f"{subj} unready!",
                color=discord.Colour.green()
            ))

    def is_all_ready(self):
        return self.player_ready and self.opponent_ready

    def reset_ready(self):
        self.player_ready = False
        self.opponent_ready = False

    async def go_next_status(self, timer_cancelled):
        if self.round == -1:
            if timer_cancelled:
                self.round = 0
                await self.channel.send(embed=discord.Embed(
                    title="ALL READY!",
                    description="Making match & mappool...",
                    color=discord.Colour.dark_red()
                ))

                await self.scrim.maketeam(self.player.display_name, False)
                await self.scrim.maketeam(self.opponent.display_name, False)
                await self.scrim.addplayer(self.player.display_name, self.player, False)
                await self.scrim.addplayer(self.opponent.display_name, self.opponent, False)
            else:
                await self.channel.send(embed=discord.Embed(
                    title="The Opponent didn't participate.",
                    description="Match aborted.",
                    color=discord.Colour.dark_red()
                ))
                self.abort = True
        elif self.round == 0:
            if timer_cancelled:
                self.round = 1
                await self.channel.send(embed=discord.Embed(
                    title="ALL READY!",
                    description="Preparing the round...",
                    color=discord.Colour.dark_red()
                ))
                await self.scrim.setform(self.diff_form)
            else:
                await self.channel.send(embed=discord.Embed(
                    title="The Opponent didn't ready.",
                    description="Match aborted.",
                    color=discord.Colour.dark_red()
                ))
                self.abort = True
        else:
            if timer_cancelled:
                message = await self.channel.send(embed=discord.Embed(
                    title="ALL READY!",
                    description=f"Round #{self.round} starts in 10...",
                    color=discord.Colour.purple()
                ))
                for i in range(9, -1, -1):
                    await message.edit(embed=discord.Embed(
                        title="ALL READY!",
                        description=f"Round #{self.round} starts in **{i}**...",
                        color=discord.Colour.purple()
                    ))
                    await asyncio.sleep(1)
            else:
                message = await self.channel.send(embed=discord.Embed(
                    title="READY TIME OVER!",
                    description=f"Force Round #{self.round} to start in 10...",
                    color=discord.Colour.purple()
                ))
                for i in range(9, -1, -1):
                    await message.edit(embed=discord.Embed(
                        title="준비 시간이 끝났습니다!",
                        description=f"**Force** Round #{self.round} to start in **{i}**...",
                        color=discord.Colour.purple()
                    ))
                    await asyncio.sleep(1)
            self.round += 1
            await self.scrim.do_match_start()

    async def do_progress(self):
        if self.abort:
            return
        elif self.round == -1:
            self.channel = await match_category_channel.create_text_channel(f"Match_{self.made_time}")
            self.scrim = Scrim(self.channel)
            await self.channel.send(
                f"{self.player.mention} {self.opponent.mention}",
                embed=discord.Embed(
                    title="Match initiated!",
                    description="Chat `rdy` to participate in 2 minutes!"
                )
            )
            self.timer = Timer(self.channel, f"Match_{self.made_time}_invite", 120, self.go_next_status)
        elif self.round == 0:
            select_pool_mmr_range = sum(self.elo_manager.get_ratings()) / d('2')
            print('Before select_pool_mmr_range :', select_pool_mmr_range)
            # 1000 ~ 2000 => 1200 ~ 3300
            select_pool_mmr_range = (select_pool_mmr_range - 1000) * d('2.1') + 1200
            print('After  select_pool_mmr_range :', select_pool_mmr_range)
            pool_pools = list(filter(
                lambda po: abs(select_pool_mmr_range - po['averageMMR']) <= d('50'),
                maidbot_pools
            ))
            selected_pool = random.choice(pool_pools)
            print('Selected pool :', selected_pool['name'])
            await self.channel.send(embed=discord.Embed(
                title="Mappool is selected!",
                description=f"Mappool Name : `{selected_pool['name']}`\n"
                            f"Mappool MMR (modified) : {(selected_pool['averageMMR'] - 1200) / d('2.1') + 1000}\n"
                            f"Mappool UUID : `{selected_pool['uuid']}`",
                color=discord.Colour(0x0ef37c)
            ))

            statusmessage = await self.channel.send(embed=discord.Embed(
                title="This message is for showing mappool making process.",
                description="If you see this message for more than 5 seconds, call the bot developer.",
                color=discord.Colour.orange()
            ))
            self.mappoolmaker = MappoolMaker(statusmessage, ses, self.made_time)

            # 테스트 데이터 : 디코8토너 쿼터파이널
            # self.mappoolmaker.maps = {
            #     'NM1': (714329, 1509639), 'NM2': (755844, 1590814), 'NM3': (145215, 424925), 'NM4': (671199, 1419243),
            #     'HR1': (41874, 132043), 'HR2': (136065, 363010), 'HR3': (90385, 245284),
            #     'HD1': (708305, 1497483), 'HD2': (931886, 1945754), 'HD3': (739053, 1559618),
            #     'DT1': (223092, 521280), 'DT2': (26226, 88633), 'DT3': (190754, 454158),
            #     'FM1': (302535, 678106), 'FM2': (870225, 1818604), 'FM3': (830444, 1768797),
            #     'TB': (1009680, 2248906)
            # }

            mappool_link = await self.mappoolmaker.execute_osz_from_fixca(selected_pool['uuid'])
            if mappool_link[0] is False:
                print(mappool_link[1])
                await self.channel.send(embed=discord.Embed(
                    title="Error occurred",
                    description=mappool_link[1] + '\nRetry soon by downloading each beatmaps...'
                ))
                for bm in selected_pool['maps']:
                    self.mappoolmaker.add_map(bm['sheetId'], bm['mapSetId'], bm['mapId'])
                mappool_link = await self.mappoolmaker.execute_osz()
                if mappool_link[0] is False:
                    print(mappool_link[1])
                    await self.channel.send(embed=discord.Embed(
                        title="Error occurred",
                        description=mappool_link[1]
                    ))
                    return
            else:
                self.diff_form = '[number] artist - title(diff)'
            mappool_link = mappool_link[1]

            maps = dict([(i, []) for i in modes])
            for k in self.mappoolmaker.beatmap_objects.keys():
                m = moder.match(k)
                if m:
                    maps[m.group(1)] = k
            for mm in maps:
                random.shuffle(maps[mm])
            mode_order = ['NM', 'HD', 'HR', 'DT']
            random.shuffle(mode_order)
            for mm in mode_order:
                self.map_order.append(maps[mm].pop())
            self.map_order.append(maps['FM'].pop())
            self.map_order.append(maps['NM'].pop())
            self.map_tb = maps['TB'].pop()

            await self.channel.send(f"{self.player.mention} {self.opponent.mention}", embed=discord.Embed(
                title="Mappool is made!",
                description=f"Please download from here : {mappool_link}\n"
                            f"If any error occured during the process, "
                            f"abort this match and call the bot developer.\n"
                            f"If you finished downloading and got ready, chat `rdy`.\n"
                            f"You have 5 minutes to download the mappool.",
                color=discord.Colour.blue()
            ))
            self.timer = Timer(self.channel, f"Match_{self.made_time}_download", 300, self.go_next_status)
        elif self.round == len(self.map_order) or self.round > self.bo or \
                self.winfor in set(self.scrim.setscore.values()):
            winner = await self.scrim.end()
            score_diff = \
                self.scrim.setscore[self.player.display_name] - self.scrim.setscore[self.opponent.display_name]
            self.elo_manager.update(score_diff / d('8') + d('.5'), True)
            ratings[uids[self.player.id]], ratings[uids[self.opponent.id]] = self.elo_manager.get_ratings()
            shutil.rmtree(self.mappoolmaker.save_folder_path)
            self.abort = True
        else:
            if self.round == self.bo and self.map_tb is not None:
                now_mapnum = self.map_tb
            else:
                now_mapnum = self.map_order[self.round - 1]
            now_beatmap: osuapi.osu.Beatmap = self.mappoolmaker.beatmap_objects[now_mapnum]
            self.scrim.setnumber(now_mapnum)
            self.scrim.setartist(now_beatmap.artist)
            self.scrim.setauthor(now_beatmap.creator)
            self.scrim.settitle(now_beatmap.title)
            self.scrim.setdiff(now_beatmap.version)
            self.scrim.setmaptime(now_beatmap.total_length)
            self.scrim.setmode(now_mapnum[:2])
            scorecalc = scoreCalc.scoreCalc(os.path.join(
                self.mappoolmaker.save_folder_path, self.mappoolmaker.osufile_path[now_mapnum]))
            self.scrim.setautoscore(scorecalc.getAutoScore()[1])
            await self.channel.send(embed=discord.Embed(
                title=f"Map infos Modified!",
                description=f"Map Info : `{self.scrim.getmapfull()}`\n"
                            f"Map Number : {self.scrim.getnumber()} / Map Mode : {self.scrim.getmode()}\n"
                            f"Map SS Score : {self.scrim.getautoscore()} / Map Length : {self.scrim.getmaptime()} sec.",
                color=discord.Colour.blue()
            ))
            await self.channel.send(embed=discord.Embed(
                title=f"Round #{self.round} ready!",
                description="Chat `rdy` in 2 minutes.",
                color=discord.Colour.orange()
            ))
            self.timer = Timer(self.channel, f"Match_{self.made_time}_{self.round}", 120, self.go_next_status)

    async def match_start(self):
        try:
            while not self.abort:
                await self.do_progress()
                while True:
                    if self.abort:
                        await self.channel.send(embed=discord.Embed(
                            title="Match successfully finished"
                        ))
                        break
                    if self.is_all_ready():
                        await self.timer.cancel()
                        self.reset_ready()
                        # if self.scrim is not None and not self.scrim.match_task.done():
                        if self.round > 1:
                            await self.scrim.match_task
                        break
                    await asyncio.sleep(1)
        except BaseException as ex_:
            if self.mappoolmaker.drive_file is not None:
                self.mappoolmaker.drive_file.Delete()
            del matches[self.player], matches[self.opponent]
            print(get_traceback_str(ex_))
            raise ex_

    async def do_match_start(self):
        if self.match_task is None or self.match_task.done():
            self.match_task = asyncio.create_task(self.match_start())
        else:
            await self.channel.send(embed=discord.Embed(
                title="Match is already processing!",
                description="Try again after the match ends.",
                color=discord.Colour.dark_red()
            ))

matches: Dict[discord.Member, Match] = dict()
# discord.Member : Match

####################################################################################################################

class MappoolMaker:
    def __init__(self, message, session, name):
        self.maps: Dict[str, Tuple[int, int]] = dict()  # MODE: (MAPSET ID, MAPDIFF ID)
        self.osufile_path: Dict[str, str] = dict()
        self.beatmap_objects: Dict[str, osuapi.osu.Beatmap] = dict()
        self.queue = asyncio.Queue()
        self.session: Optional[aiohttp.ClientSession] = session
        self.message: Optional[discord.Message] = message
        self.drive_file: Optional[pydrive.drive.GoogleDriveFile] = None

        self.match_made_time = name
        self.pool_name = f"Match_{name}"
        self.save_folder_path = os.path.join('songs', self.pool_name)

    def add_map(self, mode: str, mapid: int, diffid: int):
        self.maps[mode] = (mapid, diffid)

    def remove_map(self, mode: str):
        del self.maps[mode]

    async def downloadBeatmap(self, number: int):
        async with self.session.get(CHIMU + str(number), params=chimu_params) as res_chimu:
            if res_chimu.status == 200:
                async with aiofiles.open(downloadpath % number, 'wb') as f_:
                    await f_.write(await res_chimu.read())
                print(f'{number}번 비트맵셋 다운로드 완료 (chimu.moe)')
            else:
                print(f'{number}번 비트맵셋 다운로드 실패 (chimu.moe) ({res_chimu.status})')
                async with self.session.get(BEATCONNECT + str(number)) as res_beat:
                    if res_beat.status == 200:
                        async with aiofiles.open(downloadpath % number, 'wb') as f_:
                            await f_.write(await res_beat.read())
                        print(f'{number}번 비트맵셋 다운로드 완료 (beatconnect.io)')
                    else:
                        print(f'{number}번 비트맵셋 다운로드 실패 (beatconnect.io) ({res_beat.status})')
                        downloadurl = OSU_BEATMAP_BASEURL + str(number)
                        async with self.session.get(downloadurl + '/download', headers={"referer": downloadurl}) as res:
                            if res.status < 400:
                                async with aiofiles.open(downloadpath % number, 'wb') as f_:
                                    await f_.write(await res.read())
                                print(f'{number}번 비트맵셋 다운로드 완료 (osu.ppy.sh)')
                            else:
                                print(f'{number}번 비트맵셋 다운로드 실패 (osu.ppy.sh) ({res.status})')
                                await self.queue.put((number, False))
                                return
        await self.queue.put((number, True))

    async def show_result(self):
        desc = ''
        has_exception = dd(int)
        success = 0
        await self.message.edit(embed=discord.Embed(
            title="Mappool Downloading",
            color=discord.Colour.orange()
        ))
        try:
            while True:
                v = await self.queue.get()
                if v is None:
                    await self.message.edit(embed=discord.Embed(
                        title="Mappool Download Finished",
                        description=desc,
                        color=discord.Colour.orange()
                    ))
                    break
                if v[1]:
                    success += 1
                    desc += f"Success to download mapId {v[0]} ({success}/{len(self.maps)})\n"
                else:
                    has_exception[v[0]] += 1
                    if has_exception[v[0]] == 3:
                        desc += f"Failed to download mapId{v[0]}\n"
                await self.message.edit(embed=discord.Embed(
                    title="Mappool Downloading",
                    description=desc,
                    color=discord.Colour.orange()
                ))
            return has_exception
        except BaseException as ex_:
            print(get_traceback_str(ex_))
            raise ex_

    async def execute_osz(self) -> Tuple[bool, str]:
        if self.session.closed:
            return False, 'Session is closed'
        t = asyncio.create_task(self.show_result())
        async with asyncpool.AsyncPool(loop, num_workers=4, name="DownloaderPool",
                                       logger=logging.getLogger("DownloaderPool"),
                                       worker_co=self.downloadBeatmap, max_task_time=300,
                                       log_every_n=10) as pool:
            for x in self.maps:
                mapid = self.maps[x][0]
                await pool.push(mapid)

        await self.queue.put(None)
        await t

        if 3 in set(t.result().values()):
            return False, 'Map download failed'

        try:
            os.mkdir(self.save_folder_path)
        except FileExistsError:
            pass

        await self.message.edit(embed=discord.Embed(
            title="Extracting `.osz` file and modifying `.osu` files...",
            color=discord.Colour.green()
        ))

        for x in self.maps:
            beatmap_info: osuapi.osu.Beatmap = (await api.get_beatmaps(beatmap_id=self.maps[x][1]))[0]
            self.beatmap_objects[x] = beatmap_info

            zipfile_path = downloadpath % beatmap_info.beatmapset_id
            zf = zipfile.ZipFile(zipfile_path)
            target_name = f"{beatmap_info.artist} - {beatmap_info.title} " \
                          f"({beatmap_info.creator}) [{beatmap_info.version}].osu"
            rename_file_name = f"V.A. - {self.pool_name} ({beatmap_info.creator}) " \
                               f"[[{x}] {beatmap_info.artist} - {beatmap_info.title} [{beatmap_info.version}]].osu"
            rename_file_name = prohibitted.sub('', rename_file_name)
            try:
                target_name_search = prohibitted.sub('', target_name.lower())
                zipfile_list = zf.namelist()
                extracted_path = None
                osufile_name = None
                for zfn in zipfile_list:
                    if zfn.lower() == target_name_search:
                        osufile_name = zfn
                        extracted_path = zf.extract(zfn, self.save_folder_path)
                        break
                assert extracted_path is not None
            except AssertionError:
                print(f"파일이 없음 : {target_name}")
                continue

            texts = ''
            async with aiofiles.open(extracted_path, 'r', encoding='utf-8') as osufile:
                texts = await osufile.readlines()
                for i in range(len(texts)):
                    text = texts[i].rstrip()
                    if m := re.match(r'AudioFilename:\s?(.*)', text):
                        audio_path = m.group(1)
                        audio_extracted = zf.extract(audio_path, self.save_folder_path)
                        after_filename = f"{x}.mp3"
                        os.rename(audio_extracted, audio_extracted.replace(audio_path, after_filename))
                        texts[i] = texts[i].replace(audio_path, after_filename)
                    elif m := re.match(r'\d+,\d+,\"(.*?)\".*', text):
                        background_path = m.group(1)
                        extension = background_path.split('.')[-1]
                        bg_extracted = zf.extract(background_path, self.save_folder_path)
                        after_filename = f"{x}.{extension}"
                        os.rename(bg_extracted, bg_extracted.replace(background_path, after_filename))
                        texts[i] = texts[i].replace(background_path, after_filename)
                    elif m := re.match(r'Title(Unicode)?[:](.*)', text):
                        orig_title = m.group(2)
                        texts[i] = texts[i].replace(orig_title, f'Mappool for {self.pool_name}')
                    elif m := re.match(r'Artist(Unicode)?[:](.*)', text):
                        orig_artist = m.group(2)
                        texts[i] = texts[i].replace(orig_artist, f'V.A.')
                    elif m := re.match(r'Version[:](.*)', text):
                        orig_diffname = m.group(1)
                        texts[i] = texts[i].replace(
                            orig_diffname,
                            f"[{x}] {beatmap_info.artist} - {beatmap_info.title} [{beatmap_info.version}]"
                        )

            async with aiofiles.open(extracted_path, 'w', encoding='utf-8') as osufile:
                await osufile.writelines(texts)

            os.rename(extracted_path, extracted_path.replace(osufile_name, rename_file_name))
            self.osufile_path[x] = rename_file_name
            zf.close()
            os.remove(zipfile_path)

        await self.message.edit(embed=discord.Embed(
            title="Compressing Mappool to `.osz`...",
            color=discord.Colour.orange()
        ))

        result_zipfile = f"{self.pool_name}.osz"
        with zipfile.ZipFile(result_zipfile, 'w') as zf:
            for fn in os.listdir(self.save_folder_path):
                zf.write(os.path.join(self.save_folder_path, fn), fn)

        self.drive_file = drive.CreateFile({'title': result_zipfile, 'parents': [{'id': drive_folder['id']}]})
        self.drive_file.SetContentFile(result_zipfile)
        await self.message.edit(embed=discord.Embed(
            title="Uploading Mappool file to Google Drive...",
            description="It takes quite a while. (About 3~5 min.)",
            color=discord.Colour.greyple()
        ))
        try:
            await loop.run_in_executor(None, self.drive_file.Upload)
        finally:
            self.drive_file.content.close()
        if self.drive_file.uploaded:
            await self.message.edit(embed=discord.Embed(
                title="Upload Complete!",
                color=discord.Colour.green()
            ))
            self.drive_file.InsertPermission({
                'type': 'anyone',
                'role': 'reader',
                'withLink': True
            })
            os.remove(result_zipfile)
            return True, self.drive_file['alternateLink']
        else:
            await self.message.edit(embed=discord.Embed(
                title="업로드 실패!",
                color=discord.Colour.dark_red()
            ))
            return False, 'Failed'

    async def execute_osz_from_fixca(self, uuid: str):
        if self.session is None:
            return False, 'Session is closed'
        headers = {
            "key": fixca_key,  # INPUT KEY HERE
            "uuid": uuid,
            "matchid": self.match_made_time
        }
        desc = ['Searching Mappool...']
        e = discord.Embed(
            title="Creating Mappool...",
            color=discord.Colour(0xf5e1bf)
        )
        e.description = '\n'.join(desc)
        e.set_footer(text="라카#4749 provided his mappool download server and assisted to making mappool. "
                          "Thanks to supporting!")
        await self.message.edit(embed=e)

        target_beatmap_info = list(filter(lambda po: po['uuid'] == uuid, maidbot_pools))
        if len(target_beatmap_info) == 0:
            return False, 'Not pool found'
        target_beatmap_info = target_beatmap_info[0]
        for mn in target_beatmap_info['maps']:
            self.beatmap_objects[mn['sheetId']] = (await api.get_beatmaps(beatmap_id=mn['mapId']))[0]

        desc[-1] += ' done'
        desc.append('Getting download link of mappool...')
        e.description = '\n'.join(desc)
        await self.message.edit(embed=e)

        async with self.session.post("http://ranked-osudroid.kro.kr/createPack", data=headers) as resp:
            if resp.status != 200:
                return False, f'Get info failed : {resp.status}'
            res_data = await resp.json(encoding='utf-8')
            if res_data['status'] == 'failed':
                return False, 'Get info failed : FIXCUCKED'
            download_link = res_data['downlink']

        desc[-1] += ' done'
        desc.append('Downloading mappool for setting...')
        e.description = '\n'.join(desc)
        await self.message.edit(embed=e)

        async with self.session.get(download_link) as resp:
            if resp.status != 200:
                return False, f'Download failed : {resp.status}'
            osz_file = self.save_folder_path + '.osz'
            async with aiofiles.open(osz_file, 'wb') as df:
                await df.write(await resp.content.read())
            zf = zipfile.ZipFile(osz_file)
            zf.extractall(self.save_folder_path)
            for fn in os.listdir(self.save_folder_path):
                if fn.endswith(".osu"):
                    m = parse_fixca.match(fn)
                    if m is None:
                        return False, f'Matching failed : {fn}'
                    mapnum = m.group(1)
                    self.osufile_path[mapnum] = fn
            zf.close()
            os.remove(osz_file)

        desc[-1] += ' done'
        e.description = '\n'.join(desc)
        await self.message.edit(embed=e)

        return True, download_link

####################################################################################################################

class WaitingPlayer:
    def __init__(self, discord_member: discord.Member):
        self.player = discord_member
        self.player_rating = ratings[uids[discord_member.id]]
        self.target_rating_low = self.player_rating
        self.target_rating_high = self.player_rating
        self.dr = 10
        self.task = asyncio.create_task(self.expanding())

    def __repr__(self):
        return self.player.display_name

    async def expanding(self):
        try:
            while True:
                await asyncio.sleep(1)
                self.target_rating_low -= self.dr
                self.target_rating_high += self.dr
        except asyncio.CancelledError:
            return
        except BaseException as ex_:
            print(get_traceback_str(ex_))
            raise ex_

class MatchMaker:
    def __init__(self):
        self.pool: deque[WaitingPlayer] = deque()
        self.players_in_pool: set[int] = set()
        self.task = asyncio.create_task(self.check_match())
        self.querys = deque()

    def add_player(self, player: discord.Member):
        self.querys.append((1, player))

    def remove_player(self, player: discord.Member):
        self.querys.append((2, player))

    async def check_match(self):
        try:
            while True:
                i = 0
                while i < len(self.pool):
                    p = self.pool.popleft()
                    opponents = set(filter(lambda o: p.target_rating_low <= o.player_rating <= p.target_rating_high,
                                           self.pool))
                    if len(opponents) > 0:
                        opponent = min(opponents, key=lambda o: abs(o.player_rating - p.player_rating))
                        self.pool.remove(opponent)
                        matches[p.player] = matches[opponent.player] = m = Match(p.player, opponent.player)
                        await m.do_match_start()
                        self.players_in_pool.remove(p.player.id)
                        self.players_in_pool.remove(opponent.player.id)
                        p.task.cancel()
                        opponent.task.cancel()
                        i += 1
                    else:
                        self.pool.append(p)
                    i += 1
                while len(self.querys) > 0:
                    method, player = self.querys.popleft()
                    if method == 1:
                        if player.id not in self.players_in_pool:
                            self.pool.append(WaitingPlayer(player))
                            self.players_in_pool.add(player.id)
                    else:
                        if self.pool[-1].player == player:
                            self.pool.pop()
                        else:
                            for i in range(len(self.pool) - 1):
                                p = self.pool.popleft()
                                if p.player.id == player.id:
                                    self.pool.remove(p)
                                    self.players_in_pool.remove(p.player.id)
                await asyncio.sleep(2)
        except asyncio.CancelledError:
            pass

####################################################################################################################


helptxt = discord.Embed(title=helptxt_title, description=helptxt_desc, color=discord.Colour(0xfefefe))
helptxt.add_field(name=helptxt_forscrim_name, value=helptxt_forscrim_desc1, inline=False)
helptxt.add_field(name=blank, value=helptxt_forscrim_desc2, inline=False)
helptxt.add_field(name=blank, value=helptxt_forscrim_desc3, inline=False)
helptxt.add_field(name=blank, value=helptxt_forscrim_desc4, inline=False)
helptxt.add_field(name=helptxt_other_name, value=helptxt_other_desc, inline=False)


@app.event
async def on_ready():
    global match_category_channel
    print(f"[{time.strftime('%Y-%m-%d %a %X', time.localtime(time.time()))}]")
    print("BOT NAME :", app.user.name)
    print("BOT ID   :", app.user.id)
    game = discord.Game("m;help")
    await app.change_presence(status=discord.Status.online, activity=game)
    print("==========BOT START==========")
    match_category_channel = await app.fetch_channel(824985957165957151)


@app.event
async def on_message(message):
    ch = message.channel
    p = message.author
    if p == app.user:
        return
    if isinstance(message.channel, discord.channel.DMChannel):
        print(
            f"[{time.strftime('%Y-%m-%d %a %X', time.localtime(time.time()))}] "
            f"[DM] <{p.name};{p.id}> {message.content}"
        )
    else:
        print(
            f"[{time.strftime('%Y-%m-%d %a %X', time.localtime(time.time()))}] "
            f"[{message.guild.name};{ch.name}] <{p.name};{p.id}> {message.content}"
        )
    if credentials.expired:
        gs.login()
    pm = matches.get(p)
    if message.content == 'rdy' and pm is not None:
        pm: Match
        await pm.switch_ready(p)
    await app.process_commands(message)


@app.event
async def on_command_exception(ctx, exception):
    exceptiontxt = get_traceback_str(exception)
    print('================ ERROR ================')
    print(exceptiontxt)
    print('=======================================')
    await ctx.send(f'Error Occurred :\n```{exceptiontxt}```')


@app.command(name="help")
async def _help(ctx):
    await ctx.send(embed=helptxt)


@app.command()
async def ping(ctx):
    msgtime = ctx.message.created_at
    nowtime = datetime.datetime.utcnow()
    print(msgtime)
    print(nowtime)
    await ctx.send(f"Pong! `{(nowtime - msgtime).total_seconds() * 1000 :.4f}ms`")


@app.command()
async def roll(ctx, *dices: str):
    sendtxt = []
    for _d in dices:
        x = dice(_d)
        if not x:
            continue
        sendtxt.append(f"{_d}: **{' / '.join(x)}**")
    await ctx.send(embed=discord.Embed(title="Dice result", description='\n'.join(sendtxt)))


@app.command()
async def sheetslink(ctx):
    await ctx.send("https://docs.google.com/spreadsheets/d/1SA2u-KgTsHcXcsGEbrcfqWugY7sgHIYJpPa5fxNEJYc/edit#gid=0")


####################################################################################################################


@app.command()
@is_owner()
async def say(ctx, *, txt: str):
    if txt:
        await ctx.send(txt)


@app.command()
@is_owner()
async def sayresult(ctx, *, com: str):
    res = eval(com)
    await ctx.send('Result : `' + str(res) + '`')


@app.command()
@is_owner()
async def run(ctx, *, com: str):
    exec(com)
    await ctx.send('Done')

@app.command()
@is_owner()
async def asyncrun(ctx, *, com: str):
    exec(
        f'async def __ex(): ' +
        ''.join(f'\n    {_l}' for _l in com.split('\n')),
        {**globals(), **locals()}, locals()
    )
    await locals()['__ex']()
    await ctx.send('Done')


####################################################################################################################


@app.command()
async def make(ctx):
    s = datas[ctx.guild.id][ctx.channel.id]
    if s['valid']:
        await ctx.send(embed=discord.Embed(
            title="There's already scrim running.",
            description=f"You can make scrim only one per channel.",
            color=discord.Colour.dark_red()
        ))
        return
    s['valid'] = 1
    s['scrim'] = Scrim(ctx.channel)
    await ctx.send(embed=discord.Embed(
        title="A SCRIM IS MADE.",
        description=f"Guild : {ctx.guild}\nChannel : {ctx.channel}",
        color=discord.Colour.green()
    ))


@app.command(aliases=['t'])
async def teamadd(ctx, *, name):
    s = datas[ctx.guild.id][ctx.channel.id]
    if s['valid']:
        await s['scrim'].maketeam(name)


@app.command(aliases=['tr'])
async def teamremove(ctx, *, name):
    s = datas[ctx.guild.id][ctx.channel.id]
    if s['valid']:
        await s['scrim'].removeteam(name)


@app.command(name="in")
async def _in(ctx, *, name):
    s = datas[ctx.guild.id][ctx.channel.id]
    if s['valid']:
        await s['scrim'].addplayer(name, ctx.author)


@app.command()
async def out(ctx):
    s = datas[ctx.guild.id][ctx.channel.id]
    if s['valid']:
        await s['scrim'].removeplayer(ctx.author)


@app.command(aliases=['score', 'sc'])
async def _score(ctx, sc: int, a: float = 0.0, m: int = 0):
    s = datas[ctx.guild.id][ctx.channel.id]
    if s['valid']:
        await s['scrim'].addscore(ctx.author, sc, a, m)


@app.command(aliases=['scr'])
async def scoreremove(ctx):
    s = datas[ctx.guild.id][ctx.channel.id]
    if s['valid']:
        await s['scrim'].removescore(ctx.author)


@app.command()
async def submit(ctx, calcmode: Optional[str] = None):
    s = datas[ctx.guild.id][ctx.channel.id]
    if s['valid']:
        await s['scrim'].submit(calcmode)

@app.command()
async def start(ctx):
    s = datas[ctx.guild.id][ctx.channel.id]
    if s['valid']:
        await s['scrim'].do_match_start()

@app.command()
async def abort(ctx):
    s = datas[ctx.guild.id][ctx.channel.id]
    if s['valid']:
        if not s['scrim'].match_task.done():
            s['scrim'].match_task.cancel()

@app.command()
async def end(ctx):
    s = datas[ctx.guild.id][ctx.channel.id]
    if s['valid']:
        await s['scrim'].end()
        del datas[ctx.guild.id][ctx.channel.id]

@app.command()
async def bind(ctx, number: int):
    mid = ctx.author.id
    uids[mid] = number
    if ratings[number] == d():
        ratings[number] = elo_rating.ELO_MID_RATING - (await get_rank(number)) / d('100')
    await ctx.send(embed=discord.Embed(
        title=f'Player {ctx.author.name} binded to UID {number}.',
        color=discord.Colour(0xfefefe)
    ))


@app.command(name="map")
async def _map(ctx, *, name: str):
    s = datas[ctx.guild.id][ctx.channel.id]
    if s['valid']:
        resultmessage = await ctx.send(embed=discord.Embed(
            title="Calculating...",
            color=discord.Colour.orange()
        ))
        scrim = s['scrim']
        t = scrim.setmapinfo(name)
        if t:
            try:
                target = worksheet.find(name)
            except gspread.exceptions.CellNotFound:
                await resultmessage.edit(embed=discord.Embed(
                    title=f"{name} not found!",
                    description="Check typo(s), and if that name is on bot sheet.",
                    color=discord.Colour.dark_red()
                ))
                return
            except Exception as e:
                await resultmessage.eddit(embed=discord.Embed(
                    title="Error occurred!",
                    description=f"Error : `[{type(e)}] {e}`",
                    color=discord.Colour.dark_red()
                ))
                return
            values = worksheet.row_values(target.row)
            scrim.setfuncs['author'](values[0])
            scrim.setfuncs['artist'](values[1])
            scrim.setfuncs['title'](values[2])
            scrim.setfuncs['diff'](values[3])
            mapautosc = values[4]
            maptime_ = values[8]
            if mapautosc:
                scrim.setautoscore(int(mapautosc))
            if maptime_:
                scrim.setmaptime(int(maptime_))
            scrim.setnumber(name)
            scrim.setmode(re.findall('|'.join(modes), name.split(';')[-1])[0])
        await resultmessage.edit(embed=discord.Embed(
            title=f"Map infos Modified!",
            description=f"Map Info : `{scrim.getmapfull()}`\n"
                        f"Map Number : {scrim.getnumber()} / Map Mode : {scrim.getmode()}\n"
                        f"Map SS Score : {scrim.getautoscore()} / Map Length : {scrim.getmaptime()} sec.",
            color=discord.Colour.blue()
        ))


@app.command(aliases=['mm'])
async def mapmode(ctx, mode: str):
    s = datas[ctx.guild.id][ctx.channel.id]
    if s['valid']:
        resultmessage = await ctx.send(embed=discord.Embed(
            title="계산 중...",
            color=discord.Colour.orange()
        ))
        scrim = s['scrim']
        scrim.setmode(mode)
        await resultmessage.edit(embed=discord.Embed(
            title=f"Map infos Modified!",
            description=f"Map Info : `{scrim.getmapfull()}`\n"
                        f"Map Number : {scrim.getnumber()} / Map Mode : {scrim.getmode()}\n"
                        f"Map SS Score : {scrim.getautoscore()} / Map Length : {scrim.getmaptime()} sec.",
            color=discord.Colour.blue()
        ))

@app.command(aliases=['mt'])
async def maptime(ctx, _time: int):
    s = datas[ctx.guild.id][ctx.channel.id]
    if s['valid']:
        resultmessage = await ctx.send(embed=discord.Embed(
            title="계산 중...",
            color=discord.Colour.orange()
        ))
        scrim = s['scrim']
        scrim.setmaptime(_time)
        await resultmessage.edit(embed=discord.Embed(
            title=f"Map infos Modified!",
            description=f"Map Info : `{scrim.getmapfull()}`\n"
                        f"Map Number : {scrim.getnumber()} / Map Mode : {scrim.getmode()}\n"
                        f"Map SS Score : {scrim.getautoscore()} / Map Length : {scrim.getmaptime()} sec.",
            color=discord.Colour.blue()
        ))

@app.command(aliases=['ms'])
async def mapscore(ctx, sc_or_auto: Union[int, str], *, path: Optional[str] = None):
    s = datas[ctx.guild.id][ctx.channel.id]
    if s['valid']:
        resultmessage = await ctx.send(embed=discord.Embed(
            title="Processing...",
            color=discord.Colour.orange()
        ))
        scrim = s['scrim']
        if sc_or_auto == 'auto':
            s = scoreCalc.scoreCalc(path)
            scrim.setautoscore(s.getAutoScore()[1])
            s.close()
        else:
            scrim.setautoscore(sc_or_auto)
        await resultmessage.edit(embed=discord.Embed(
            title=f"Map infos Modified!",
            description=f"Map Info : `{scrim.getmapfull()}`\n"
                        f"Map Number : {scrim.getnumber()} / Map Mode : {scrim.getmode()}\n"
                        f"Map SS Score : {scrim.getautoscore()} / Map Length : {scrim.getmaptime()} sec.",
            color=discord.Colour.blue()
        ))


@app.command(aliases=['l'])
async def onlineload(ctx, checkbit: Optional[int] = None):
    s = datas[ctx.guild.id][ctx.channel.id]
    if s['valid']:
        await s['scrim'].onlineload(checkbit)


@app.command()
async def form(ctx, *, f_: str):
    s = datas[ctx.guild.id][ctx.channel.id]
    if s['valid']:
        await s['scrim'].setform(f_)


@app.command(aliases=['mr'])
async def mapmoderule(
        ctx, 
        nm: Optional[str], 
        hd: Optional[str], 
        hr: Optional[str], 
        dt: Optional[str], 
        fm: Optional[str], 
        tb: Optional[str]
):
    s = datas[ctx.guild.id][ctx.channel.id]
    if s['valid']:
        def temp(x: Optional[str]):
            return set(map(int, x.split(',')))
        s['scrim'].setmoderule(temp(nm), temp(hd), temp(hr), temp(dt), temp(fm), temp(tb))

@app.command()
async def timer(ctx, action: Union[float, str], name: Optional[str] = None):
    if action == 'now':
        if timers.get(name) is None:
            await ctx.send(embed=discord.Embed(
                title=f"No timer named {name}!",
                color=discord.Colour.dark_red()
            ))
        else:
            await timers[name].edit()
    elif action == 'cancel':
        if timers.get(name) is None:
            await ctx.send(embed=discord.Embed(
                title=f"No timer named {name}!",
                color=discord.Colour.dark_red()
            ))
        else:
            await timers[name].cancel()
    else:
        if name is None:
            global timer_count
            name = str(timer_count)
            timer_count += 1
        if timers.get(name) is not None and not timers[name].done:
            await ctx.send(embed=discord.Embed(
                title=f"There's already running timer named {name}!",
                color=discord.Colour.dark_red()
            ))
            return
        Timer(ctx.channel, name, action)

@app.command()
async def calc(ctx, kind: str, maxscore: d, score: d, acc: d, miss: d):
    if kind == "nero2":
        result = neroscorev2(maxscore, score, acc, miss)
    elif kind == "jet2":
        result = jetonetv2(maxscore, score, acc, miss)
    elif kind == "osu2":
        result = osuv2(maxscore, score, acc, miss)
    else:
        await ctx.send(embed=discord.Embed(
            title="Unknown Calculate Mode!",
            description="It should be (Empty), `nero2`, `jet2`, or `osu2`",
            color=discord.Colour.dark_red()
        ))
        return
    await ctx.send(embed=discord.Embed(
        title=f"Calculation result : ({kind})",
        description=f"maxscore = {maxscore}\n"
                    f"score = {score}\n"
                    f"acc = {acc}\n"
                    f"miss = {miss}\n\n"
                    f"calculated = **{result}**",
        color=discord.Colour.dark_blue()
    ))

@app.command()
async def now(ctx):
    s = datas[ctx.guild.id][ctx.channel.id]
    if s['valid']:
        scrim = s['scrim']
        e = discord.Embed(title="Now scrim info", color=discord.Colour.orange())
        for t in scrim.team:
            e.add_field(
                name="Team "+t,
                value='\n'.join([(await getusername(x)) for x in scrim.team[t]])
            )
        await ctx.send(embed=e)

####################################################################################################################

@app.command(aliases=['pfme'])
async def profileme(ctx):
    e = discord.Embed(
        title=f"{ctx.author.display_name}'s profile",
        color=discord.Colour(0xdb6ee1)
    )
    e.add_field(
        name="UID",
        value=str(uids[ctx.author.id])
    )
    e.add_field(
        name="Elo",
        value=str(ratings[uids[ctx.author.id]])
    )
    await ctx.send(embed=e)

@app.command(aliases=['q'])
async def queue(ctx):
    if matches.get(ctx.author):
        await ctx.send(embed=discord.Embed(
            title=f"You can't queue while playing match.",
            color=discord.Colour.dark_red()
        ))
        return
    elif uids[ctx.author.id] == 0:
        await ctx.send(embed=discord.Embed(
            title=f"You should bind your UID first. Use `m;bind`",
            color=discord.Colour.dark_red()
        ))
        return
    matchmaker.add_player(ctx.author)
    await ctx.send(embed=discord.Embed(
        title=f"{ctx.author.display_name} queued.",
        description=f"(If you already in queue, this will be ignored.)\n"
                    f"Now the number of players in queue : {len(matchmaker.pool)}",
        color=discord.Colour(0x78f7fb)
    ))

@app.command(aliases=['uq'])
async def unqueue(ctx):
    matchmaker.remove_player(ctx.author)
    await ctx.send(embed=discord.Embed(
        title=f"{ctx.author.display_name} unqueued.",
        description=f"**This request could be ignored.**\n"
                    f"Now the number of players in queue : {len(matchmaker.pool)}",
        color=discord.Colour(0x78f7fb)
    ))

####################################################################################################################

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

loop = asyncio.get_event_loop()
match_category_channel: Optional[discord.CategoryChannel] = None
matchmaker: Optional[MatchMaker] = None

async def _main():
    global ses, matchmaker, api
    ses = aiohttp.ClientSession(loop=loop)
    matchmaker = MatchMaker()
    got_login = await osu_login(ses)
    if got_login:
        print('OSU LOGIN SUCCESS')
        turnoff = False

        try:
            api = OsuApi(api_key, connector=AHConnector())
            res = await api.get_user("peppy")
            assert res[0].user_id == 2
        except HTTPError:
            print("Invalid osu!API key")
            turnoff = True
        except AssertionError:
            print("Something went wrong")
            turnoff = True

        try:
            assert turnoff is False
            await app.start(token)
        except BaseException as _ex:
            if isinstance(ex, (KeyboardInterrupt, asyncio.CancelledError)):
                print('Ctrl-C or Cancelled')
            else:
                traceback.print_exception(type(_ex), _ex, _ex.__traceback__)
        finally:
            with open('uids.txt', 'w') as f__:
                for u in uids:
                    f__.write(f"{u} {uids[u]}\n")
            with open('ratings.txt', 'w') as f__:
                for u in ratings:
                    f__.write(f"{u} {ratings[u]}\n")
            api.close()
            await app.logout()
            await app.close()
            print('Program Close')
    else:
        print('OSU LOGIN FAILED')
    await ses.close()

if __name__ == '__main__':
    running = loop.create_task(_main())
    try:
        loop.run_forever()
    except BaseException as ex:
        if isinstance(ex, (KeyboardInterrupt, asyncio.CancelledError)):
            print('Ctrl-C or Cancelled')
        else:
            traceback.print_exception(type(ex), ex, ex.__traceback__)
    finally:
        running.cancel()
        loop.run_until_complete(loop.shutdown_asyncgens())
        loop.run_until_complete(asyncio.sleep(1))
        loop.close()
