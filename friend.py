from friend_import import *
from timer import Timer
from scrim import Scrim
from match import Match_Scrim
from matchmaker import MatchMaker
from verify import Verify

class MyCog(commands.Cog):
    def __init__(self, bot: 'MyBot'):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"[{time.strftime('%Y-%m-%d %a %X', time.localtime(time.time()))}]")
        print("BOT NAME :", self.bot.user.name)
        print("BOT ID   :", self.bot.user.id)
        game = discord.Game("m;help")
        await self.bot.change_presence(status=discord.Status.online, activity=game)
        print("==========BOT START==========")
        self.bot.match_category_channel = await self.bot.fetch_channel(824985957165957151)

    @commands.Cog.listener()
    async def on_message(self, message):
        ch = message.channel
        p = message.author
        if p == self.bot.user:
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
        pm = self.bot.matches.get(p)
        if message.content == 'rdy' and pm is not None and ch == pm.channel:
            await pm.switch_ready(p)

    @commands.Cog.listener()
    async def on_command_exception(self, ctx, exception):
        exceptiontxt = get_traceback_str(exception)
        print('================ ERROR ================')
        print(exceptiontxt)
        print('=======================================')
        await ctx.send(f'Error Occurred :\n```{exceptiontxt}```')

    @commands.command(name="help")
    async def _help(self, ctx):
        await ctx.send(embed=helptxt)

    @commands.command()
    async def ping(self, ctx):
        msgtime = ctx.message.created_at
        nowtime = datetime.datetime.utcnow()
        print(msgtime)
        print(nowtime)
        await ctx.send(f"Pong! `{(nowtime - msgtime).total_seconds() * 1000 :.4f}ms`")

    @commands.command()
    async def roll(self, ctx, *dices: str):
        sendtxt = []
        for _d in dices:
            x = dice(_d)
            if not x:
                continue
            sendtxt.append(f"{_d}: **{' / '.join(x)}**")
        await ctx.send(embed=discord.Embed(title="Dice result", description='\n'.join(sendtxt)))

    @commands.command()
    async def sheetslink(self, ctx):
        await ctx.send("https://docs.google.com/spreadsheets/d/1SA2u-KgTsHcXcsGEbrcfqWugY7sgHIYJpPa5fxNEJYc/edit#gid=0")

    @commands.command()
    @is_owner()
    async def say(self, ctx, *, txt: str):
        if txt:
            await ctx.send(txt)

    @commands.command()
    @is_owner()
    async def sayresult(self, ctx, *, com: str):
        res = eval(com)
        await ctx.send('Result : `' + str(res) + '`')

    @commands.command()
    @is_owner()
    async def run(self, ctx, *, com: str):
        exec(com)
        await ctx.send('Done')

    @commands.command()
    @is_owner()
    async def asyncsayresult(self, ctx, *, com: str):
        res = await eval(com)
        await ctx.send('Result : `' + str(res) + '`')

    @commands.command()
    @is_owner()
    async def asyncrun(self, ctx, *, com: str):
        exec(
            f'async def __ex(): ' +
            ''.join(f'\n    {_l}' for _l in com.split('\n')),
            {**globals(), **locals()}, locals()
        )
        await locals()['__ex']()
        await ctx.send('Done')

    @commands.command()
    async def make(self, ctx):
        s = self.bot.datas[ctx.guild.id][ctx.channel.id]
        if s['valid']:
            await ctx.send(embed=discord.Embed(
                title="There's already scrim running.",
                description=f"You can make scrim only one per channel.",
                color=discord.Colour.dark_red()
            ))
            return
        s['valid'] = 1
        s['scrim'] = Scrim(self.bot, ctx.channel)
        await ctx.send(embed=discord.Embed(
            title="A SCRIM IS MADE.",
            description=f"Guild : {ctx.guild}\nChannel : {ctx.channel}",
            color=discord.Colour.green()
        ))
        if self.bot.shutdown_datetime - datetime.datetime.now(tz=KST) <= datetime.timedelta(hours=1):
            await ctx.send(embed=discord.Embed(
                title=f"The bot is supposed to shutdown at {self.bot.shutdown_datetime.strftime('%H:%M')} KST.",
                description="If the bot shutdowns during the match, "
                            "all datas of the match will be disappeared.",
                color=discord.Colour.dark_red()
            ))

    @commands.command(aliases=['t'])
    async def teamadd(self, ctx, *, name):
        s = self.bot.datas[ctx.guild.id][ctx.channel.id]
        if s['valid']:
            await s['scrim'].maketeam(name)

    @commands.command(aliases=['tr'])
    async def teamremove(self, ctx, *, name):
        s = self.bot.datas[ctx.guild.id][ctx.channel.id]
        if s['valid']:
            await s['scrim'].removeteam(name)

    @commands.command(name="in")
    async def _in(self, ctx, *, name):
        s = self.bot.datas[ctx.guild.id][ctx.channel.id]
        if s['valid']:
            await s['scrim'].addplayer(name, ctx.author)

    @commands.command()
    async def out(self, ctx):
        s = self.bot.datas[ctx.guild.id][ctx.channel.id]
        if s['valid']:
            await s['scrim'].removeplayer(ctx.author)

    @commands.command(aliases=['score', 'sc'])
    async def _score(self, ctx, sc: int, a: float = 0.0, m: int = 0, gr: str = None):
        s = self.bot.datas[ctx.guild.id][ctx.channel.id]
        if s['valid']:
            await s['scrim'].addscore(ctx.author, sc, a, m, gr)

    @commands.command(aliases=['scr'])
    async def scoreremove(self, ctx):
        s = self.bot.datas[ctx.guild.id][ctx.channel.id]
        if s['valid']:
            await s['scrim'].removescore(ctx.author)

    @commands.command()
    async def submit(self, ctx, calcmode: Optional[str] = None):
        s = self.bot.datas[ctx.guild.id][ctx.channel.id]
        if s['valid']:
            await s['scrim'].submit(calcmode)

    @commands.command()
    async def start(self, ctx):
        s = self.bot.datas[ctx.guild.id][ctx.channel.id]
        if s['valid']:
            await s['scrim'].do_match_start()

    @commands.command()
    async def abort(self, ctx):
        s = self.bot.datas[ctx.guild.id][ctx.channel.id]
        if s['valid']:
            if not s['scrim'].match_task.done():
                s['scrim'].match_task.cancel()

    @commands.command()
    async def end(self, ctx):
        s = self.bot.datas[ctx.guild.id][ctx.channel.id]
        if s['valid']:
            await s['scrim'].end()
            del self.bot.datas[ctx.guild.id][ctx.channel.id]

    @commands.command()
    async def verify(self, ctx, uid: Optional[int] = None):
        mid = ctx.author.id
        if self.bot.uids[mid] > 0:
            await ctx.send(embed=discord.Embed(
                title=f'You already verified with UID {self.bot.uids[mid]}.',
                color=discord.Colour.orange()
            ))
        else:
            if v := self.bot.verifies.get(mid):
                verified = await v.do_verify()
                if verified:
                    self.bot.ratings[v.uid] = get_initial_elo(await self.bot.get_rank(v.uid))
                    if BOT_DEBUG:
                        async with self.bot.session.post(
                                "http://ranked-osudroid.kro.kr/userAdd",
                                body={
                                    'key': fixca_key,
                                    'discord_id': str(ctx.author.id),
                                    'elo': str(self.bot.ratings[v.uid]),
                                    'uid': str(v.uid)
                                }
                        ) as useradd_res:
                            if useradd_res.status != 200:
                                await ctx.send(embed=discord.Embed(
                                    title=f'POST failed. ({useradd_res.status})\n',
                                    description=f'Try again.',
                                    color=discord.Colour.dark_red()
                                ))
                                del self.bot.ratings[v.uid]
                                return
                            if (useradd_res_json := await useradd_res.json(encoding='utf-8'))['status'] == 'failed':
                                await ctx.send(embed=discord.Embed(
                                    title=f'POST failed. (FIXCUCKED)\n',
                                    description=f'```{useradd_res_json["error"]}```\n\nTry again.',
                                    color=discord.Colour.dark_red()
                                ))
                                del self.bot.ratings[v.uid]
                                return
                    await ctx.send(embed=discord.Embed(
                        title=f'Player {ctx.author.name} binded to UID {v.uid}.\n',
                        description=f'Your ELO value set to {self.bot.ratings[v.uid]}',
                        color=discord.Colour(0xfefefe)
                    ))
                    del self.bot.verifies[mid]
                else:
                    await ctx.send(embed=discord.Embed(
                        title=f'Failed to bind.\n',
                        description=f'Try again.',
                        color=discord.Colour.dark_red()
                    ))
            else:
                if uid is None:
                    await ctx.send(embed=discord.Embed(
                        title=f'You should enter UID you want to bind with.',
                        color=discord.Colour.orange()
                    ))
                    return
                self.bot.verifies[mid] = Verify(self.bot, ctx.channel, ctx.author, uid)
                await ctx.send(embed=discord.Embed(
                    title="For verifying...",
                    description=f'Please play this map in 5 minutes.\n'
                                f'http://ranked-osudroid.kro.kr/verification\n'
                                f'And chat `m;verify` again.',
                    color=discord.Colour.orange()
                ))

    @commands.command(name="map")
    async def _map(self, ctx, *, name: str):
        s = self.bot.datas[ctx.guild.id][ctx.channel.id]
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

    @commands.command(aliases=['mm'])
    async def mapmode(self, ctx, mode: str):
        s = self.bot.datas[ctx.guild.id][ctx.channel.id]
        if s['valid']:
            resultmessage = await ctx.send(embed=discord.Embed(
                title="Calculating...",
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

    @commands.command(aliases=['mt'])
    async def maptime(self, ctx, _time: int):
        s = self.bot.datas[ctx.guild.id][ctx.channel.id]
        if s['valid']:
            resultmessage = await ctx.send(embed=discord.Embed(
                title="Calculating...",
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

    @commands.command(aliases=['ms'])
    async def mapscore(self, ctx, sc_or_auto: Union[int, str], *, path: Optional[str] = None):
        s = self.bot.datas[ctx.guild.id][ctx.channel.id]
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

    @commands.command(aliases=['l'])
    async def onlineload(self, ctx, checkbit: Optional[int] = None):
        s = self.bot.datas[ctx.guild.id][ctx.channel.id]
        if s['valid']:
            await s['scrim'].onlineload(checkbit)

    @commands.command()
    async def form(self, ctx, *, f_: str):
        s = self.bot.datas[ctx.guild.id][ctx.channel.id]
        if s['valid']:
            await s['scrim'].setform(f_)

    @commands.command(aliases=['mr'])
    async def mapmoderule(
            self,
            ctx,
            nm: Optional[str],
            hd: Optional[str],
            hr: Optional[str],
            dt: Optional[str],
            fm: Optional[str],
            tb: Optional[str]
    ):
        s = self.bot.datas[ctx.guild.id][ctx.channel.id]
        if s['valid']:
            resultmessage = await ctx.send(embed=discord.Embed(
                title="Calculating...",
                color=discord.Colour.orange()
            ))

            def temp(x: Optional[str]):
                return set(map(int, x.split(',')))

            scrim = s['scrim']
            scrim.setmoderule(temp(nm), temp(hd), temp(hr), temp(dt), temp(fm), temp(tb))
            desc = '\n'.join(f"Allowed modes for {i} = `{', '.join(inttomode(j) for j in scrim.availablemode[i])}`"
                             for i in modes)
            await resultmessage.edit(embed=discord.Embed(
                title=f"Map mode rules Modified!",
                description=desc,
                color=discord.Colour.blue()
            ))

    @commands.command(aliases=['mh'])
    async def maphash(self, ctx, h: str):
        s = self.bot.datas[ctx.guild.id][ctx.channel.id]
        if s['valid']:
            resultmessage = await ctx.send(embed=discord.Embed(
                title="Calculating...",
                color=discord.Colour.orange()
            ))
            scrim = s['scrim']
            scrim.setmaphash(h)
            await resultmessage.edit(embed=discord.Embed(
                title=f"Map infos Modified!",
                description=f"Map Info : `{scrim.getmapfull()}`\n"
                            f"Map Number : {scrim.getnumber()} / Map Mode : {scrim.getmode()}\n"
                            f"Map SS Score : {scrim.getautoscore()} / Map Length : {scrim.getmaptime()} sec.\n"
                            f"Map Hash : {scrim.getmaphash()}",
                color=discord.Colour.blue()
            ))

    @commands.command()
    async def timer(self, ctx, action: Union[float, str], name: Optional[str] = None):
        if action == 'now':
            if self.bot.timers.get(name) is None:
                await ctx.send(embed=discord.Embed(
                    title=f"No timer named `{name}`!",
                    color=discord.Colour.dark_red()
                ))
            else:
                await self.bot.timers[name].edit()
        elif action == 'cancel':
            if self.bot.timers.get(name) is None:
                await ctx.send(embed=discord.Embed(
                    title=f"No timer named `{name}`!",
                    color=discord.Colour.dark_red()
                ))
            else:
                await self.bot.timers[name].cancel()
        else:
            if name is None:
                name = str(self.bot.timer_count)
                self.bot.timer_count += 1
            if self.bot.timers.get(name) is not None and not self.bot.timers[name].done:
                await ctx.send(embed=discord.Embed(
                    title=f"There's already running timer named `{name}`!",
                    color=discord.Colour.dark_red()
                ))
                return
            try:
                Timer(self.bot, ctx.channel, name, float(action))
            except ValueError:
                await ctx.send(embed=discord.Embed(
                    title=f"You should enter number for time limit!",
                    color=discord.Colour.dark_red()
                ))

    @commands.command()
    async def calc(self, ctx, kind: str, maxscore: d, score: d, acc: d, miss: d):
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

    @commands.command()
    async def now(self, ctx):
        s = self.bot.datas[ctx.guild.id][ctx.channel.id]
        if s['valid']:
            scrim = s['scrim']
            e = discord.Embed(title="Now scrim info", color=discord.Colour.orange())
            for t in scrim.team:
                e.add_field(
                    name="Team " + t,
                    value='\n'.join([(await self.bot.getusername(x)) for x in scrim.team[t]])
                )
            await ctx.send(embed=e)

    @commands.command(aliases=['pfme'])
    async def profileme(self, ctx, uid: Optional[int] = None):
        e = discord.Embed(
            title=f"{ctx.author.name}'s profile",
            color=discord.Colour(0xdb6ee1)
        )
        if uid is None:
            uid = self.bot.uids[ctx.author.id]
        if uid == 0:
            await ctx.send(embed=discord.Embed(
                title=f"You should bind your UID first. Use `m;verify`",
                color=discord.Colour.dark_red()
            ))
            return
        e.add_field(
            name="UID",
            value=str(uid)
        )
        if self.bot.ratings.get(uid) is None:
            self.bot.ratings[uid] = get_initial_elo(await self.bot.get_rank(uid))
        e.add_field(
            name="Elo",
            value=str(self.bot.ratings[uid].to_integral(rounding=decimal.ROUND_FLOOR))
        )
        e.add_field(
            name="Tier",
            value=get_elo_rank(self.bot.ratings[uid])
        )
        await ctx.send(embed=e)

    @commands.command(aliases=['rs'])
    async def recentme(self, ctx, uid: Optional[int] = None):
        if uid is None:
            uid = self.bot.uids.get(ctx.author.id)
        if uid == 0:
            await ctx.send(embed=discord.Embed(
                title=f"You should bind your UID first. Use `m;verify`",
                color=discord.Colour.dark_red()
            ))
            return
        recent_play_info = await self.bot.getrecent(uid)
        rd = dict()
        rd['artist'], rd['title'], rd['author'], rd['diff'] = recent_play_info[0]
        e = discord.Embed(
            title=f"{ctx.author.name}'(s) recent play info",
            color=discord.Colour(0x78a94c)
        )
        e.add_field(
            name="Map",
            value=f"`{makefull(**rd)}`",
            inline=False
        )
        e.add_field(
            name="Played Time",
            value=recent_play_info[1][0],
            inline=False
        )
        e.add_field(
            name="Score / Accuracy / Miss",
            value=f"{recent_play_info[1][1]} / {recent_play_info[1][3]}% / {recent_play_info[2][0]} :x:",
            inline=False
        )
        e.add_field(
            name="Mod",
            value=inttomode(modetointfunc(recent_play_info[1][2].split(', '))),
        )
        e.add_field(
            name="Combo",
            value=f"{recent_play_info[1][4]}x"
        )
        rk = rankFilenameR.match(recent_play_info[3])
        if rk is not None:
            rk = rk.group(1)
        e.add_field(
            name="Rank",
            value=RANK_EMOJI[rk]
        )
        e.add_field(
            name="Hash",
            value=recent_play_info[2][1],
            inline=False
        )
        await ctx.send(embed=e)

    @commands.command(aliases=['q'])
    async def queue(self, ctx):
        if self.bot.matches.get(ctx.author):
            await ctx.send(embed=discord.Embed(
                title=f"You can't queue while playing match.",
                color=discord.Colour.dark_red()
            ))
            return
        elif self.bot.uids[ctx.author.id] == 0:
            await ctx.send(embed=discord.Embed(
                title=f"You should bind your UID first. Use `m;verify`",
                color=discord.Colour.dark_red()
            ))
            return
        elif self.bot.shutdown_datetime - datetime.datetime.now(tz=KST) <= datetime.timedelta(minutes=30):
            await ctx.send(embed=discord.Embed(
                title=f"The bot is supposed to shutdown at {self.bot.shutdown_datetime.strftime('%H:%M')} KST.",
                description=f"You can join the queue until 30 minutes before shutdown "
                            f"({(self.bot.shutdown_datetime - datetime.timedelta(minutes=30)).strftime('%H:%M')} KST).",
                color=discord.Colour.dark_red()
            ))
            return
        self.bot.matchmaker.add_player(ctx.author)
        await ctx.send(embed=discord.Embed(
            title=f"{ctx.author.name} queued.",
            description=f"(If you already in queue, this will be ignored.)\n"
                        f"Now the number of players in queue : {len(self.bot.matchmaker.pool)}",
            color=discord.Colour(0x78f7fb)
        ))

    @commands.command(aliases=['uq'])
    async def unqueue(self, ctx):
        self.bot.matchmaker.remove_player(ctx.author)
        await ctx.send(embed=discord.Embed(
            title=f"{ctx.author.name} unqueued.",
            description=f"**This request could be ignored.**\n"
                        f"Now the number of players in queue : {len(self.bot.matchmaker.pool)}",
            color=discord.Colour(0x78f7fb)
        ))

class MyBot(commands.Bot):
    def __init__(self, ses, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.member_names: Dict[int, str] = dict()
        self.datas: dd[Dict[int, dd[Dict[int, Dict[str, Union[int, 'Scrim']]], Callable[[], Dict]]]] = \
            dd(lambda: dd(lambda: {'valid': False, 'scrim': None}))

        self.session: Optional[aiohttp.ClientSession] = ses
        self.osuapi: Optional[OsuApi] = osuapi.OsuApi(api_key, connector=AHConnector())

        self.uids: dd[int, int] = dd(int)
        self.ratings: dd[int, d] = dd(d)
        with open('uids.txt', 'r') as uidf:
            while data := uidf.readline():
                discordid, userid = data.split(' ')
                self.uids[int(discordid)] = int(userid)
        with open('ratings.txt', 'r') as ratf:
            while data := ratf.readline():
                userid, r = data.split(' ')
                self.ratings[int(userid)] = getd(r)

        self.verifies: Dict[int, Verify] = dict()

        self.timers: dd[str, Optional['Timer']] = dd(lambda: None)
        self.timer_count = 0

        self.matches: Dict[discord.Member, 'Match_Scrim'] = dict()
        self.match_category_channel: Optional[discord.CategoryChannel] = None
        self.matchmaker = MatchMaker(self)

        self.shutdown_datetime = get_shutdown_datetime()

    async def getusername(self, x: int) -> str:
        if self.member_names.get(x) is None:
            user = self.get_user(x)
            if user is None:
                user = await self.fetch_user(x)
            self.member_names[x] = user.name
        return self.member_names[x]

    async def getrecent(self, _id: int) -> Optional[Tuple[Sequence[AnyStr], Sequence[AnyStr], Sequence[AnyStr], str]]:
        url = url_base + str(_id)
        html = await self.session.get(url)
        bs = BeautifulSoup(await html.text(), "html.parser")
        recent = bs.select_one("#activity > ul > li:nth-child(1)")
        recent_mapinfo = recent.select("a.clear > strong.block")[0].text
        recent_playinfo = recent.select("a.clear > small")[0].text
        recent_miss = recent.select("#statics")[0].text
        rank_img_filename = recent.select("a.thumb-sm.pull-left.m-r-sm > img")[0]['src']
        rmimatch = mapr.match(recent_mapinfo)
        if rmimatch is None:
            return None
        return (rmimatch.groups(),
                playr.match(recent_playinfo).groups(),
                missr.match(recent_miss).groups(),
                rank_img_filename)

    async def get_rank(self, _id: int):
        url = url_base + str(_id)
        html = await self.session.get(url)
        bs = BeautifulSoup(await html.text(), "html.parser")
        rank = bs.select_one("#content > section > section > section > aside.aside-lg.bg-light.lter.b-r > "
                             "section > section > div > div.panel.wrapper > div > div:nth-child(1) > a > span").text
        return int(rank)


async def _main():
    app = MyBot(ses=aiohttp.ClientSession(), command_prefix='m;', help_command=None, intents=intents)
    app.add_cog(MyCog(app))
    got_login = await osu_login(app.session)
    if got_login:
        turnoff = False
        try:
            res = await app.osuapi.get_user("peppy")
            assert res[0].user_id == 2
        except HTTPError:
            print("Invalid osu!API key")
            turnoff = True
        except AssertionError:
            print("Something went wrong")
            turnoff = True

        assert turnoff is False
        bot_task = asyncio.create_task(app.start(token))
        try:
            await auto_off(app.shutdown_datetime)
        except asyncio.CancelledError:
            print('_main() : Cancelled')
            raise
        except Exception as _ex:
            raise
        finally:
            with open('uids.txt', 'w') as f__:
                for u in app.uids:
                    f__.write(f"{u} {app.uids[u]}\n")
            with open('ratings.txt', 'w') as f__:
                for u in app.ratings:
                    f__.write(f"{u} {app.ratings[u]}\n")
            app.osuapi.close()
            await app.change_presence(status=discord.Status.offline)
            await app.loop.shutdown_asyncgens()
            app.loop.close()
            await app.close()
            if not bot_task.done():
                bot_task.cancel()
            await app.session.close()
            app.matchmaker.close()
            print('_main() : finally done')

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    main_run = loop.create_task(_main())
    try:
        loop.run_until_complete(main_run)
    except KeyboardInterrupt:
        print('Ctrl+C')
    except BaseException as ex:
        print(get_traceback_str(ex))
    finally:
        main_run.cancel()
        loop.run_until_complete(loop.shutdown_asyncgens())
        print('Shutdown asyncgens done / close after 3 sec.')
        loop.run_until_complete(asyncio.sleep(3))
        loop.close()
        print('loop closed')
