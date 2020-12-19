import asyncio, discord, time, gspread, re, datetime, random, requests, \
    os, traceback, scoreCalc, decimal
from oauth2client.service_account import ServiceAccountCredentials as SAC
from collections import defaultdict
from bs4 import BeautifulSoup
from discord.ext import commands
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

getd = lambda n: decimal.Decimal(str(n))
halfup = lambda d: d.quantize(decimal.Decimal('1.'), rounding=decimal.ROUND_HALF_UP)
neroscoreV2 = lambda maxscore, score, acc, miss: halfup((getd(score) / getd(maxscore) * 600000
                                                         + (getd(acc) ** 4) / 250)
                                                        * (1 - getd(0.003) * getd(miss)))
jetonetV2 = lambda maxscore, score, acc, miss: halfup(getd(score) / getd(maxscore) * 500000
                                                      + ((max(getd(acc) - 80, 0)) / 20) ** 2 * 500000)
osuV2 = lambda maxscore, score, acc, miss: halfup(getd(score) / getd(maxscore) * 700000
                                                  + (getd(acc) / 100) ** 10 * 300000)

kind = ['number', 'artist', 'author', 'title', 'diff']
rmeta = r'\$(*+.?[^{|'

analyze = re.compile(r"(.*) [-] (.*) [(](.*)[)] [\[](.*)[]]")

####################################################################################################################

def makefull(**kwargs):
    return f"{kwargs['artist']} - {kwargs['title']} ({kwargs['author']}) [{kwargs['diff']}]"

def dice(s: str):
    s = s.partition('d')
    if s[1] == '': return None
    return tuple(str(random.randint(1, int(s[2]))) for _ in range(int(s[0])))

def getrecent(id: int):
    url = url_base + str(id)
    html = requests.get(url)
    bs = BeautifulSoup(html.text, "html.parser")
    recent = bs.select_one("#activity > ul > li:nth-child(1)")
    recentMapinfo = recent.select("a.clear > strong.block")[0].text
    recentPlayinfo = recent.select("a.clear > small")[0].text
    recentMiss = recent.select("#statics")[0].text
    return (mapr.match(recentMapinfo).groups(), playr.match(recentPlayinfo).groups(), missr.match(recentMiss).groups())\

def is_owner():
    async def predicate(ctx):
        return ctx.author.id == 327835849142173696
    return commands.check(predicate)

####################################################################################################################

# scrim classes

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
    print(f"[{time.strftime('%Y-%m-%d %a %X', time.localtime(time.time()))} ({ping}ms)] [{message.guild.name};{ch.name}] <{p.name};{p.id}> {message.content}")
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

# scrim commands

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