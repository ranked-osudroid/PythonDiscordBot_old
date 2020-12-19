import asyncio
import datetime
import decimal
import discord
import gspread
import random
import re
import requests
import time
import traceback
from typing import *
from collections import defaultdict

from bs4 import BeautifulSoup
from discord.ext import commands
from oauth2client.service_account import ServiceAccountCredentials as SAC

from help_texts import *

####################################################################################################################

scope = [
    'https://spreadsheets.google.com/feeds',
    'https://www.googleapis.com/auth/drive',
]
jsonfile = 'friend-266503-91ab7f0dce62.json'
credentials = SAC.from_json_keyfile_name(jsonfile, scope)
gs = gspread.authorize(credentials)
gs.login()
spreadsheet = "https://docs.google.com/spreadsheets/d/1SA2u-KgTsHcXcsGEbrcfqWugY7sgHIYJpPa5fxNEJYc/edit#gid=0"
doc = gs.open_by_url(spreadsheet)

worksheet = doc.worksheet('data')

app = commands.Bot(command_prefix='m;', help_command=None)

with open("key.txt", 'r') as f:
    token = f.read()

####################################################################################################################

url_base = "http://ops.dgsrz.com/profile.php?uid="
mapr = re.compile(r"(.*) [-] (.*) [(](.*)[)] [\[](.*)[]]")
playr = re.compile(r"(.*) / (.*) / (.*) / (.*)x / (.*)%")
missr = re.compile(r"[{]\"miss\":(\d+), \"hash\":.*[}]")

d = decimal.Decimal

def getd(n: Union[int, float, str]):
    return d(str(n))

def halfup(n: d):
    return n.quantize(getd('1.'), rounding=decimal.ROUND_HALF_UP)

def neroscorev2(maxscore: int, score: int, acc: float, miss: int):
    s = 600000 * getd(score) / getd(maxscore)
    a = 400000 * (getd(acc) / 100) ** 4
    return halfup((s + a) * (1 - getd(0.003) * getd(miss)))

def jetonetv2(maxscore: int, score: int, acc: float, miss: int):
    s = 500000 * getd(score) / getd(maxscore)
    a = 500000 * (max(getd(acc) - 80, getd('0')) / 20) ** 2
    return halfup(s + a)

def osuv2(maxscore: int, score: int, acc: float, miss: int):
    s = 700000 * getd(score) / getd(maxscore)
    a = 300000 * (getd(acc) / 100) ** 10
    return halfup(s + a)

kind = ['number', 'artist', 'author', 'title', 'diff']
rmeta = r'\$(*+.?[^{|'

analyze = re.compile(r"(.*) [-] (.*) [(](.*)[)] [\[](.*)[]]")


####################################################################################################################


def makefull(**kwargs: str):
    return f"{kwargs['artist']} - {kwargs['title']} ({kwargs['author']}) [{kwargs['diff']}]"


def dice(s: str):
    s = s.partition('d')
    if s[1] == '':
        return None
    return tuple(str(random.randint(1, int(s[2]))) for _ in range(int(s[0])))


def getrecent(_id: int):
    url = url_base + str(_id)
    html = requests.get(url)
    bs = BeautifulSoup(html.text, "html.parser")
    recent = bs.select_one("#activity > ul > li:nth-child(1)")
    recent_mapinfo = recent.select("a.clear > strong.block")[0].text
    recent_playinfo = recent.select("a.clear > small")[0].text
    recent_miss = recent.select("#statics")[0].text
    return (mapr.match(recent_mapinfo).groups(),
            playr.match(recent_playinfo).groups(),
            missr.match(recent_miss).groups())


def is_owner():
    async def predicate(ctx):
        return ctx.author.id == 327835849142173696
    return commands.check(predicate)


####################################################################################################################


def getuser(x):
    if not member_ids[x]:
        member_ids[x] = app.get_user(x)
    return member_ids[x]


class Scrim:
    def __init__(self, ctx: discord.ext.commands.Context):
        self.loop = asyncio.get_event_loop()
        self.guild = ctx.guild
        self.channel = ctx.channel

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

        self.mapartist: str = ''
        self.mapauthor: str = ''
        self.maptitle: str = ''
        self.mapdiff: str = ''
        self.mapnumber: str = ''

        self.form: List[re.Pattern, List[str]] = None

        self.loop.run_until_complete(
            self.channel.send(embed=discord.Embed(
                title="스크림이 만들어졌습니다! | A scrim is made",
                description=f"서버/Guild : {self.guild}\n채널/Channel : {self.channel}",
                color=discord.Colour.blue()
            ))
        )

    async def maketeam(self, name: str):
        if self.team.get(name):
            await self.channel.send(embed=discord.Embed(
                title=f"\"{name}\" 팀은 이미 존재합니다!",
                description=f"현재 팀 리스트:\n{chr(10).join(self.team.keys())}",
                color=discord.Colour.blue()
            ))
        else:
            self.team[name] = set()
            self.setscore[name] = 0
            await self.channel.send(embed=discord.Embed(
                title=f"\"{name}\" 팀을 추가했습니다!",
                description=f"현재 팀 리스트:\n{chr(10).join(self.team.keys())}",
                color=discord.Colour.blue()
            ))

    async def removeteam(self, name: str):
        if not self.team.get(name):
            await self.channel.send(embed=discord.Embed(
                title=f"\"{name}\"이란 팀은 존재하지 않습니다!",
                description=f"현재 팀 리스트:\n{chr(10).join(self.team.keys())}",
                color=discord.Colour.blue()
            ))
        else:
            for p in self.team[name]:
                del self.findteam[p]
            del self.team[name], self.setscore[name]
            await self.channel.send(embed=discord.Embed(
                title=f"\"{name}\" 팀이 해산되었습니다!",
                description=f"현재 팀 리스트:\n{chr(10).join(self.team.keys())}",
                color=discord.Colour.blue()
            ))

    async def addplayer(self, name: str, member: Optional[discord.Member]):
        if not member:
            return
        mid = member.id
        temp = self.findteam.get(mid)
        if temp:
            await self.channel.send(embed=discord.Embed(
                title=f"플레이어 \"{member.display_name}\"은 이미 \"{temp}\" 팀에 들어가 있습니다!",
                description=f"`m;out`으로 현재 팀에서 나온 다음에 명령어를 다시 입력해주세요."
            ))
        else:
            self.findteam[mid] = name
            self.team[name].add(mid)
            self.players.add(mid)
            self.score[mid] = (getd(0), getd(0), getd(0))
            await self.channel.send(embed=discord.Embed(
                title=f"플레이어 \"{member.display_name}\"가 \"{name}\"팀에 참가합니다!",
                description=f"현재 \"{name}\"팀 플레이어 리스트:\n"
                            f"{chr(10).join(getuser(pl).display_name for pl in self.team[name])}",
                color=discord.Colour.blue()
            ))

    async def removeplayer(self, member: Optional[discord.Member]):
        if not member:
            return
        mid = member.id
        temp = self.findteam.get(mid)
        if mid not in self.players:
            await self.channel.send(embed=discord.Embed(
                title=f"플레이어 \"{member.display_name}\"은 어느 팀에도 속해있지 않습니다!",
                description=f"일단 참가하고나서 해주시죠."
            ))
        else:
            del self.findteam[mid], self.score[mid]
            self.team[temp].remove(mid)
            self.players.remove(mid)
            await self.channel.send(embed=discord.Embed(
                title=f"플레이어 \"{member.display_name}\"가 \"{temp}\"팀을 떠납니다!",
                description=f"현재 \"{temp}\"팀 플레이어 리스트:\n"
                            f"{chr(10).join(getuser(pl).display_name for pl in self.team[temp])}",
                color=discord.Colour.blue()
            ))

    async def addscore(self, member: Optional[discord.Member], score: int, acc: float, miss: int):
        if not member:
            return
        mid = member.id
        if mid not in self.players:
            await self.channel.send(embed=discord.Embed(
                title=f"플레이어 \"{member.display_name}\"은 어느 팀에도 속해있지 않습니다!",
                description=f"일단 참가하고나서 해주시죠."
            ))
        else:
            self.score[mid] = (getd(score), getd(acc), getd(miss))
            await self.channel.send(embed=discord.Embed(
                title=f"플레이어 {member.display_name}의 점수를 추가(또는 수정)했습니다!",
                description=f"\"{self.findteam[mid]}\"팀에 {score}, {acc}%, {miss}xMISS",
                color=discord.Colour.blue()
            ))

    async def removescore(self, member: Optional[discord.Member]):
        if not member:
            return
        mid = member.id
        if mid not in self.players:
            await self.channel.send(embed=discord.Embed(
                title=f"플레이어 \"{member.display_name}\"은 어느 팀에도 속해있지 않습니다!",
                description=f"일단 참가하고나서 해주시죠."
            ))
        else:
            self.score[mid] = (getd(0), getd(0), getd(0))
            await self.channel.send(embed=discord.Embed(
                title=f"플레이어 {member.display_name}의 점수를 삭제했습니다!",
                color=discord.Colour.blue()
            ))


member_ids: defaultdict[int, discord.Member] = defaultdict(None)
datas: defaultdict[int, defaultdict[int, Dict[str, Union[int, Scrim]]]] = \
    defaultdict(lambda: defaultdict(lambda: {'valid': False, 'scrim': None}))
uids: defaultdict[int, int] = defaultdict(int)


####################################################################################################################


helptxt = discord.Embed(title=helptxt_title, description=helptxt_desc, color=discord.Colour(0xfefefe))
helptxt.add_field(name=helptxt_forscrim_name, value=helptxt_forscrim_desc)
helptxt.add_field(name=helptxt_other_name, value=helptxt_other_desc)


@app.event
async def on_ready():
    print(f"[{time.strftime('%Y-%m-%d %a %X', time.localtime(time.time()))}]")
    print("BOT NAME :", app.user.name)
    print("BOT ID   :", app.user.id)
    game = discord.Game("REMODELLING")
    await app.change_presence(status=discord.Status.online, activity=game)
    print("==========BOT START==========")


@app.event
async def on_message(message):
    ch = message.channel
    p = message.author
    if p == app.user:
        return
    print(
        f"[{time.strftime('%Y-%m-%d %a %X', time.localtime(time.time()))} ({ping}ms)] "
        f"[{message.guild.name};{ch.name}] <{p.name};{p.id}> {message.content}")
    if credentials.access_token_expired:
        gs.login()
    await app.process_commands(message)


@app.event
async def on_command_error(ctx, error):
    errortxt = ''.join(traceback.format_exception(type(error), error, error.__traceback__))
    print('================ ERROR ================')
    print('```' + errortxt.strip() + '```')
    print('=======================================')
    await ctx.send(errortxt)


@app.command(name="help")
async def _help(ctx):
    await ctx.send(embed=helptxt)


@app.command()
async def ping(ctx):
    msgtime = ctx.message.created_at
    nowtime = datetime.datetime.utcnow()
    await ctx.send(f"Pong! ({(nowtime - msgtime).total_seconds() * 1000 :.4f}ms)")


@app.command()
async def roll(ctx, *dices: str):
    sendtxt = []
    for d in dices:
        x = dice(d)
        if not x:
            continue
        sendtxt.append(f"{d}: **{' / '.join(x)}**")
    await ctx.send(embed=discord.Embed(title="Dice Roll Result", description='\n'.join(sendtxt)))


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
    r = eval(com)
    await ctx.send('RESULT : ' + str(r))


@app.command()
@is_owner()
async def run(ctx, *, com: str):
    exec(com)
    await ctx.send('DONE')


####################################################################################################################


@app.command()
async def make(ctx):
    s = datas[ctx.guild.id][ctx.channel.id]
    if s['valid']:
        await ctx.send("이미 스크림이 존재합니다.")
        return
    s['valid'] = 1
    s['scrim'] = Scrim(ctx)


@app.command(aliases=["teamadd", 't'])
async def teamadd(ctx, *, name):
    s = datas[ctx.guild.id][ctx.channel.id]
    if s['valid']:
        await s['scrim'].maketeam(name)


@app.command(aliases=["teamremove", 'tr'])
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


@app.command(aliases=["score", 'sc'])
async def score(ctx, sc: int, a: float = 0.0, m: int = 0):
    s = datas[ctx.guild.id][ctx.channel.id]
    if s['valid']:
        await s['scrim'].addscore(ctx.author, sc, a, m)


@app.command(aliases=["scoreremove", 'scr'])
async def scoreremove(ctx):
    s = datas[ctx.guild.id][ctx.channel.id]
    if s['valid']:
        await s['scrim'].removescore(ctx.author)


@app.command()
async def bind(ctx, number: int):
    mid = ctx.author.id
    uids[mid] = number
    await ctx.send(embed=discord.Embed(
        title=f'DONE: {ctx.author.name} binded to {number}',
        color=discord.Colour(0xfefefe)
    ))

####################################################################################################################

loop = asyncio.get_event_loop()
try:
    loop.run_until_complete(app.start(token))
except KeyboardInterrupt:
    print("\nForce stop")
except BaseException as ex:
    print(repr(ex))
    print(ex)
finally:
    loop.run_until_complete(app.close())
    loop.run_until_complete(loop.shutdown_asyncgens())
    loop.close()
