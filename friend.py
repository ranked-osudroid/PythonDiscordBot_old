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
import scoreCalc
from typing import *
from collections import defaultdict as dd

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
rmeta = r'\$(*+.?[^{|'

analyze = re.compile(r"(?P<artist>.*) [-] (?P<title>.*) [(](?P<author>.*)[)] \[(?P<diff>.*)]")


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


def getusername(x: int) -> str:
    if member_names.get(x) is None:
        member_names[x] = app.get_user(x).name
    return member_names[x]


visibleinfo = ['artist', 'title', 'author', 'diff']
modes = ['NM', 'HD', 'HR', 'DT', 'FM', 'TB']
modetoint = {
    'None': 0,
    'Hidden': 1,
    'HardRock': 2,
    'DoubleTime': 4,
    'NoFail': 8,
    'HalfTime': 16,
    'NightCore': 32,
    'Easy': 64
}
infotoint = {
    'artist': 1,
    'title': 2,
    'author': 4,
    'diff': 8,
    'mode': 16
}


class Scrim:
    def __init__(self, ctx: discord.ext.commands.Context):
        self.loop = asyncio.get_event_loop()
        self.guild: discord.Guild = ctx.guild
        self.channel: discord.TextChannel = ctx.channel

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

    async def maketeam(self, name: str):
        if self.team.get(name) is not None:
            await self.channel.send(embed=discord.Embed(
                title=f"\"{name}\" 팀은 이미 존재합니다!",
                description=f"현재 팀 리스트:\n{chr(10).join(self.team.keys())}",
                color=discord.Colour.dark_blue()
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
        if self.team.get(name) is None:
            await self.channel.send(embed=discord.Embed(
                title=f"\"{name}\"이란 팀은 존재하지 않습니다!",
                description=f"현재 팀 리스트:\n{chr(10).join(self.team.keys())}",
                color=discord.Colour.dark_blue()
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
                title=f"플레이어 \"{member.name}\"님은 이미 \"{temp}\" 팀에 들어가 있습니다!",
                description=f"`m;out`으로 현재 팀에서 나온 다음에 명령어를 다시 입력해주세요."
            ))
        elif self.team.get(name) is None:
            await self.channel.send(embed=discord.Embed(
                title=f"\"{name}\"이란 팀은 존재하지 않습니다!",
                description=f"현재 팀 리스트:\n{chr(10).join(self.team.keys())}",
                color=discord.Colour.dark_blue()
            ))
        else:
            self.findteam[mid] = name
            self.team[name].add(mid)
            self.players.add(mid)
            self.score[mid] = (getd(0), getd(0), getd(0))
            await self.channel.send(embed=discord.Embed(
                title=f"플레이어 \"{member.name}\"님이 \"{name}\"팀에 참가합니다!",
                description=f"현재 \"{name}\"팀 플레이어 리스트:\n"
                            f"{chr(10).join(getusername(pl) for pl in self.team[name])}",
                color=discord.Colour.blue()
            ))

    async def removeplayer(self, member: Optional[discord.Member]):
        if not member:
            return
        mid = member.id
        temp = self.findteam.get(mid)
        if mid not in self.players:
            await self.channel.send(embed=discord.Embed(
                title=f"플레이어 \"{member.name}\"님은 어느 팀에도 속해있지 않습니다!",
                description=f"일단 참가하고나서 해주시죠."
            ))
        else:
            del self.findteam[mid], self.score[mid]
            self.team[temp].remove(mid)
            self.players.remove(mid)
            await self.channel.send(embed=discord.Embed(
                title=f"플레이어 \"{member.name}\"님이 \"{temp}\"팀을 떠납니다!",
                description=f"현재 \"{temp}\"팀 플레이어 리스트:\n"
                            f"{chr(10).join(getusername(pl) for pl in self.team[temp])}",
                color=discord.Colour.blue()
            ))

    async def addscore(self, member: Optional[discord.Member], score: int, acc: float, miss: int):
        if not member:
            return
        mid = member.id
        if mid not in self.players:
            await self.channel.send(embed=discord.Embed(
                title=f"플레이어 \"{member.name}\"님은 어느 팀에도 속해있지 않습니다!",
                description=f"일단 참가하고나서 해주시죠."
            ))
        else:
            self.score[mid] = (getd(score), getd(acc), getd(miss))
            await self.channel.send(embed=discord.Embed(
                title=f"플레이어 \"{member.name}\"님의 점수를 추가(또는 수정)했습니다!",
                description=f"\"{self.findteam[mid]}\"팀 <== {score}, {acc}%, {miss}xMISS",
                color=discord.Colour.blue()
            ))

    async def removescore(self, member: Optional[discord.Member]):
        if not member:
            return
        mid = member.id
        if mid not in self.players:
            await self.channel.send(embed=discord.Embed(
                title=f"플레이어 \"{member.name}\"님은 어느 팀에도 속해있지 않습니다!",
                description=f"일단 참가하고나서 해주시죠."
            ))
        else:
            self.score[mid] = (getd(0), getd(0), getd(0))
            await self.channel.send(embed=discord.Embed(
                title=f"플레이어 \"{member.name}\"님의 점수를 삭제했습니다!",
                color=discord.Colour.blue()
            ))

    async def submit(self, calcmode: Optional[str]):
        if v2dict.get(calcmode) is None:
            await self.channel.send(embed=discord.Embed(
                title="존재하지 않는 계산 방식입니다!",
                description="(입력없음), nero2, jet2, osu2 중 하나여야 합니다."
            ))
            return
        elif calcmode and (self.getautoscore() == -1):
            await self.channel.send(embed=discord.Embed(
                title="v2를 계산하기 위해서는 오토점수가 필요합니다!",
                description="`m;mapscore`로 오토점수를 등록해주세요!"
            ))
            return
        calc = v2dict[calcmode]
        resultmessage = await self.channel.send(embed=discord.Embed(
            title="계산 중...",
            color=discord.Colour.orange()
        ))
        calculatedscores = dict()
        for p in self.score:
            calculatedscores[p] = calc(self.map_auto_score, *self.score[p])
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
            title="매치 종료!",
            description=f"__**팀 {desc} 승리!**__",
            color=discord.Colour.red()
        )
        sendtxt.add_field(
            name=blank,
            value='='*20+'\n'+blank,
            inline=False
        )
        for t in teamscore:
            sendtxt.add_field(
                name=f"*\"{t}\"팀 결과:*",
                value='\n'.join(f"{getusername(p)} : {calculatedscores[p]}" for p in self.team[t])+'\n'
            )
        sendtxt.add_field(
            name=blank,
            value='='*20+'\n'+blank,
            inline=False
        )
        sendtxt.add_field(
            name="__현재 점수:__",
            value='\n'.join(f"**{t} : {self.setscore[t]}**" for t in teamscore),
            inline=False
        )
        await resultmessage.edit(embed=sendtxt)
        self.resetmap()

    def resetmap(self):
        self.map_artist = None
        self.map_author = None
        self.map_title = None
        self.map_diff = None
        self.map_number = None
        self.map_mode = None
        self.map_auto_score = None

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

    def setautoscore(self, score: Union[int, dd]):
        self.map_auto_score = score

    def getautoscore(self) -> Union[int, dd]:
        return self.map_auto_score if self.map_auto_score else -1

    def setmapinfo(self, infostr: str):
        m = analyze.match(infostr)
        if m is None:
            return True
        for k in visibleinfo:
            if m.group(k) != '':
                self.setfuncs[k](m.group(k))

    def getmapinfo(self) -> Dict[str, str]:
        r = dict()
        for k in visibleinfo:
            r[k] = self.getfuncs[k]()
        return r

    def getmapfull(self):
        return makefull(**self.getmapinfo())

    async def setform(self, form: str):
        args = list()
        for k in rkind:
            findks = re.findall(k, form)
            if len(findks):
                args.append(k)
            elif len(findks) > 1:
                await self.channel.send(embed=discord.Embed(
                    title="각 단어는 하나씩만 들어가야 합니다!",
                    color=discord.Colour.dark_red()
                ))
                return
        for c in rmeta:
            form = form.replace(c, '\\'+c)
        for a in args:
            form = form.replace(a, f'(?P<{a}>.*?)')
        self.form = [re.compile(form), args]
        await self.channel.send(embed=discord.Embed(
            title="형식 지정 완료!",
            description=f"RegEx 패턴 : `{self.form[0].pattern}`",
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
        desc = '====== < 계산 로그 > ======'
        resultmessage: discord.Message = await self.channel.send(embed=discord.Embed(
            title="계산 중...",
            description=desc,
            color=discord.Colour.orange()
        ))
        for team in self.team:
            for player in self.team[team]:
                desc += '\n'
                await resultmessage.edit(embed=discord.Embed(
                    title="계산 중...",
                    description=desc,
                    color=discord.Colour.orange()
                ))
                if uids.get(player) is None:
                    desc += f"등록 실패 : " \
                            f"{getusername(player)}의 UID가 등록되어있지 않음"
                    continue
                player_recent_info = getrecent(uids[player])
                p = dict()
                p['artist'], p['title'], p['author'], p['diff'] = player_recent_info[0]
                p['score'] = int(player_recent_info[1][1].replace(',', ''))
                p['acc'] = float(player_recent_info[1][4])
                p['miss'] = int(float(player_recent_info[2][0]))
                p['modes'] = set(player_recent_info[1][2].split(','))
                flag = False
                if self.form is not None:
                    checkbit = 0
                    m = self.form[0].match(p['diff'])
                    if m is None:
                        desc += f"등록 실패 : " \
                                f"{getusername(player)}의 최근 플레이 난이도명이 저장된 형식에 맞지 않음 " \
                                f"(플레이어 난이도명 : {p['diff']}"
                        continue
                    for k in self.form[1]:
                        if k == 'number':
                            mnum = self.map_number.split(';')[-1]
                            pnum = m.group(k)
                            if mnum != pnum:
                                flag = True
                                desc += f"등록 실패 : " \
                                        f"{getusername(player)}의 맵 번호가 다름 " \
                                        f"(현재 맵 번호 : {mnum} / 플레이어 맵 번호 : {pnum})"
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
                        if nowk != p[k]:
                            flag = True
                            desc += f"등록 실패 : " \
                                    f"{getusername(player)}의 {k}가 다름 " \
                                    f"(현재 {k} : {nowk} / 플레이어 {k} : {p[k]})"
                if flag:
                    continue
                if self.map_mode is not None:
                    pmodeint = 0
                    for md in p['modes']:
                        pmodeint |= modetoint[md]
                    if pmodeint not in self.availablemode[self.map_mode]:
                        desc += f"등록 실패 : " \
                                f"{getusername(player)}의 모드가 조건에 맞지 않음 " \
                                f"(현재 가능한 모드 숫자 : {self.availablemode[self.map_mode]} / 플레이어 모드 숫자 : {pmodeint})"
                        continue
                self.score[player] = (getd(p['score']), getd(p['acc']), getd(p['miss']))
                desc += f"등록 완료! : " \
                        f"{getusername(player)}의 점수 " \
                        f"{self.score[player][0]}, {self.score[player][1]}%, {self.score[player][2]}xMISS"
        await resultmessage.edit(embed=discord.Embed(
            title="계산 완료!",
            description=desc,
            color=discord.Colour.green()
        ))

    async def end(self):
        winnerteam = list(filter(
            lambda x: self.setscore[x] == max(self.setscore.values()),
            self.setscore.keys()
        ))
        sendtxt = discord.Embed(
            title="===== !스크림 종료! =====",
            description="팀 " + ', '.join(f"\"{w}\"" for w in winnerteam) + " 최종 우승!",
            color=discord.Colour.magenta()
        )
        sendtxt.add_field(
            name=blank,
            value='='*20+'\n'+blank,
            inline=False
        )
        sendtxt.add_field(
            name="최종 결과:",
            value='\n'.join(f"{t} : {self.setscore[t]}" for t in self.setscore)
        )
        sendtxt.add_field(
            name=blank,
            value='='*20+'\n'+blank,
            inline=False
        )
        sendtxt.add_field(
            name="수고하셨습니다!",
            value='스크림 정보가 자동으로 초기화됩니다.',
            inline=False
        )
        await self.channel.send(embed=sendtxt)


member_names: Dict[int, str] = dict()
datas: dd[Dict[int, dd[Dict[int, Dict[str, Union[int, Scrim]]], Callable[[], Dict]]]] = \
    dd(lambda: dd(lambda: {'valid': False, 'scrim': None}))
uids: dd[int, int] = dd(int)


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
        f"[{time.strftime('%Y-%m-%d %a %X', time.localtime(time.time()))}] "
        f"[{message.guild.name};{ch.name}] <{p.name};{p.id}> {message.content}")
    if credentials.access_token_expired:
        gs.login()
    await app.process_commands(message)


@app.event
async def on_command_error(ctx, error):
    errortxt = ''.join(traceback.format_exception(type(error), error, error.__traceback__)).strip()
    print('================ ERROR ================')
    print(errortxt)
    print('=======================================')
    await ctx.send('```'+errortxt+'```')


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
    for _d in dices:
        x = dice(_d)
        if not x:
            continue
        sendtxt.append(f"{_d}: **{' / '.join(x)}**")
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
    await ctx.send('RESULT : `' + str(r) + '`')


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
    await ctx.send(embed=discord.Embed(
        title="스크림이 만들어졌습니다! | A scrim is made",
        description=f"서버/Guild : {ctx.guild}\n채널/Channel : {ctx.channel}",
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
async def end(ctx):
    s = datas[ctx.guild.id][ctx.channel.id]
    if s['valid']:
        await s['scrim'].end()
        del datas[ctx.guild.id][ctx.channel.id]


@app.command()
async def bind(ctx, number: int):
    mid = ctx.author.id
    uids[mid] = number
    await ctx.send(embed=discord.Embed(
        title=f'플레이어 \"{ctx.author.name}\"님을 UID {number}로 연결했습니다!',
        color=discord.Colour(0xfefefe)
    ))


@app.command(name="map")
async def _map(ctx, *, name: str):
    s = datas[ctx.guild.id][ctx.channel.id]
    if s['valid']:
        resultmessage = await ctx.send(embed=discord.Embed(
            title="계산 중...",
            color=discord.Colour.orange()
        ))
        scrim = s['scrim']
        t = scrim.setmapinfo(name)
        if t:
            try:
                target = worksheet.find(name)
            except gspread.exceptions.CellNotFound:
                await resultmessage.edit(embed=discord.Embed(
                    title=f"{name}을 찾지 못했습니다!",
                    description="오타가 있거나, 아직 봇 시트에 등록이 안 되어 있을 수 있습니다.",
                    color=discord.Colour.dark_red()
                ))
                return
            for i, k in enumerate(['author', 'artist', 'title', 'diff']):
                scrim.setfuncs[k](worksheet.cell(target.row, i+1).value)
            autosc = worksheet.cell(target.row, 5).value
            if autosc:
                scrim.setautoscore(int(autosc))
            scrim.setnumber(name)
            scrim.setmode(re.findall('|'.join(modes), name.split(';')[-1])[0])
        await resultmessage.edit(embed=discord.Embed(
            title=f"설정 완료!",
            description=f"맵 정보 : {scrim.getmapfull()}\n"
                        f"맵 번호 : {scrim.getnumber()} / 모드 : {scrim.getmode()}\n"
                        f"맵 SS 점수 : {scrim.getautoscore()}",
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
            title=f"설정 완료!",
            description=f"맵 정보 : {scrim.getmapfull()}\n"
                        f"맵 번호 : {scrim.getnumber()} / 모드 : {scrim.getmode()}\n"
                        f"맵 SS 점수 : {scrim.getautoscore()}",
            color=discord.Colour.blue()
        ))


@app.command(aliases=['ms'])
async def mapscore(ctx, sc_or_auto: Union[int, str], *, path: Optional[str] = None):
    s = datas[ctx.guild.id][ctx.channel.id]
    if s['valid']:
        resultmessage = await ctx.send(embed=discord.Embed(
            title="계산 중...",
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
            title=f"설정 완료!",
            description=f"맵 정보 : {scrim.getmapfull()}\n"
                        f"맵 번호 : {scrim.getnumber()} / 모드 : {scrim.getmode()}\n"
                        f"맵 SS 점수 : {scrim.getautoscore()}",
            color=discord.Colour.blue()
        ))


@app.command(aliases=['l'])
async def onlineload(ctx, checkbit: Optional[int] = None):
    s = datas[ctx.guild.id][ctx.channel.id]
    if s['valid']:
        await s['scrim'].onlineload(checkbit)


@app.command()
async def form(ctx, *, f: str):
    s = datas[ctx.guild.id][ctx.channel.id]
    if s['valid']:
        await s['scrim'].setform(f)


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
    loop.run_until_complete(app.logout())
    loop.run_until_complete(app.close())
    loop.run_until_complete(loop.shutdown_asyncgens())
    loop.run_until_complete(asyncio.sleep(0.5))
    loop.close()
    print('Program Close')
