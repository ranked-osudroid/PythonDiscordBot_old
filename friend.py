import asyncio, discord, time, gspread, re, datetime, random, requests, os, traceback, scoreCalc, decimal
from oauth2client.service_account import ServiceAccountCredentials as SAC
from collections import defaultdict
from bs4 import BeautifulSoup
from discord.ext import commands

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

app = commands.Bot(command_prefix='m;')

with open("key.txt", 'r') as f:
    token = f.read()

err = "WRONG COMMAND : "

url_base = "http://ops.dgsrz.com/profile.php?uid="
mapr = re.compile(r"(.*) [-] (.*) [(](.*)[)] [\[](.*)[]]")
playr = re.compile(r"(.*) / (.*) / (.*) / (.*)x / (.*)%")
missr = re.compile(r"[{]\"miss\":(\d+), \"hash\":.*[}]")

getd = lambda n: decimal.Decimal(str(n))
neroscoreV2 = lambda maxscore, score, acc, miss: round((getd(score) / getd(maxscore) * 600000
                                                        + (getd(acc) ** 4) / 250)
                                                       * (1 - getd(0.003) * getd(miss)))
jetonetV2 = lambda maxscore, score, acc, miss: round(getd(score) / getd(maxscore) * 500000
                                                     + ((max(getd(acc) - 80, 0)) / 20) ** 2 * 500000)
osuV2 = lambda maxscore, score, acc, miss: round(getd(score) / getd(maxscore) * 700000
                                                 + (getd(acc) / 100) ** 10 * 300000)

kind = ['number', 'artist', 'author', 'title', 'diff']
rmeta = r'\$(*+.?[^{|'

analyze = re.compile(r"(.*) [-] (.*) [(](.*)[)] [\[](.*)[]]")


def makefull(**kwargs):
    return f"{kwargs['artist']} - {kwargs['title']} ({kwargs['author']}) [{kwargs['diff']}]"


def dice(s):
    s = s.partition('d')
    if s[1] == '': return None
    return tuple(str(random.randint(1, int(s[2]))) for _ in range(int(s[0])))


def getrecent(id):
    url = url_base + str(id)
    html = requests.get(url)
    bs = BeautifulSoup(html.text, "html.parser")
    recent = bs.select_one("#activity > ul > li:nth-child(1)")
    recentMapinfo = recent.select("a.clear > strong.block")[0].text
    recentPlayinfo = recent.select("a.clear > small")[0].text
    recentMiss = recent.select("#statics")[0].text
    return (mapr.match(recentMapinfo).groups(), playr.match(recentPlayinfo).groups(), missr.match(recentMiss).groups())


class Timer:
    def __init__(self, ch, name, seconds):
        self.channel = ch
        self.name = name
        self.seconds = seconds
        self.nowloop = asyncio.get_event_loop()
        self.starttime = datetime.datetime.utcnow()
        self.task = self.nowloop.create_task(self.run())

    async def run(self):
        try:
            await asyncio.sleep(self.seconds)
            await self.callback()
        except asyncio.CancelledError:
            return

    async def callback(self):
        global timers
        await self.channel.send(f"Timer **{self.name}**: TIME OVER.")
        del timers[self.name]

    def left(self):
        return self.seconds - (datetime.datetime.utcnow() - self.starttime).total_seconds()


helptxt = discord.Embed(title="COMMANDS DESCRIPTHION",
                        description='**ver. 2.202012119**\n'
                                    '<neccesary parameter> (optional parameter) [multi-case parameter]',
                        color=discord.Colour(0xfefefe))



@app.event
async def on_ready():
    print(f"[{time.strftime('%Y-%m-%d %a %X', time.localtime(time.time()))}]")
    print("BOT NAME :", app.user.name)
    print("BOT ID   :", app.user.id)
    game = discord.Game("f:help")
    await app.change_presence(status=discord.Status.online, activity=game)
    print("==========BOT START==========")


@app.event
async def on_message(message):
    ch = message.channel
    msgtime = message.created_at
    nowtime = datetime.datetime.utcnow()
    ping = f"{(nowtime - msgtime).total_seconds() * 1000 :.4f}"
    if credentials.access_token_expired:
        gs.login()



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
    loop.run_until_complete(loop.shutdown_asyncgens())
    loop.close()