import discord, importlib

import friend_import, help_texts, timer, scrim_new, match_new, matchmaker, verify, fixca
modules = [friend_import, help_texts, timer, scrim_new, match_new, matchmaker, verify, fixca]

from friend_import import *
helptxt_pages = help_texts.helptxt_pages
Timer = timer.Timer
Scrim = scrim_new.Scrim
Match = match_new.Match
MatchMaker = matchmaker.MatchMaker
RequestManager = fixca.RequestManager


class MyCog(commands.Cog):
    def __init__(self, bot: 'MyBot'):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"[{get_nowtime_str()}]")
        print(f"BOT NAME : {self.bot.user.name}")
        print(f"BOT ID   : {self.bot.user.id}")
        await self.bot.change_presence(status=discord.Status.online)
        print("==========BOT START==========")
        self.bot.match_place = await self.bot.fetch_channel(823413857036402741)
        self.bot.RANKED_OSUDROID_GUILD = self.bot.get_guild(RANKED_OSUDROID_GUILD_ID)
        if self.bot.activity_display_task is not None:
            self.bot.activity_display_task.cancel()

        async def work():
            while True:
                try:
                    if self.bot.status == (None, None):
                        await self.bot.change_presence(
                            activity=discord.Game(
                                f"{len(self.bot.matchmaker.players_in_pool)} queued | "
                                f"{len(self.bot.matches) // 2} matches"
                            )
                        )
                    await asyncio.sleep(5)
                except asyncio.CancelledError:
                    raise
                except ConnectionResetError:
                    pass
                except Exception as ex:
                    print(f"[{get_nowtime_str()}] MyBot.activity_display_task:\n{get_traceback_str(ex)}")
                    raise
        self.bot.activity_display_task = self.bot.loop.create_task(work())

    @commands.Cog.listener()
    async def on_message(self, message):
        ch = message.channel
        p = message.author
        if p == self.bot.user:
            return
        if isinstance(message.channel, discord.channel.DMChannel):
            print(
                f"[{message.created_at.strftime(TIMEFORMAT)[:-3]}] "
                f"(DM) <{p.name}> {message.content}"
            )
        else:
            print(
                f"[{message.created_at.strftime(TIMEFORMAT)[:-3]}] "
                f"({ch.name}) <{p.name}> {message.content}"
            )
        """
        if credentials.expired:
            gs.login()
        """
        pm = self.bot.matches.get(p)
        if message.content.strip().lower() == 'rdy' and pm is not None and ch == pm.channel:
            await pm.switch_ready(p)

    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context, exception):
        if isinstance(exception, commands.errors.CheckFailure):
            await ctx.send(embed=discord.Embed(
                title="**YOU DON'T HAVE PERMISSION TO USE THIS.**",
                color=discord.Colour.dark_gray()
            ))
            return
        elif isinstance(exception, commands.errors.CommandNotFound):
            """await ctx.send(embed=discord.Embed(
                title=exception.args[0],
                color=discord.Colour.dark_gray()
            ))"""
            return
        elif isinstance(exception, commands.errors.CommandInvokeError):
            exception = exception.original
        exceptiontxt = get_traceback_str(exception)
        print(f"[{get_nowtime_str()}] Mybot.on_command_error()")
        print('================ ERROR ================')
        print(exceptiontxt)
        # with open(f"errors/{time.time_ns()}.txt", 'w') as f:
        #     f.write(exceptiontxt)
        await ctx.send(
            embed=discord.Embed(
                title="Error occurred",
                description=f"{type(exception).__name__} : {exception}\nCheck the log."
            )
        )
        if isinstance(exception, self.bot.req.ERRORS):
            print('(i) Data :')
            print(exception.data)
        print('================ E N D ================')

    @commands.command(name="help")
    async def _help(self, ctx: commands.Context):
        if isinstance(ctx.channel, discord.channel.DMChannel):
            return
        help_msg: discord.Message = await ctx.send(embed=helptxt_pages[0])
        await help_msg.add_reaction('⏮')
        await help_msg.add_reaction('◀')
        await help_msg.add_reaction('▶')
        await help_msg.add_reaction('⏭')

        i = 0
        pageEND = len(helptxt_pages) - 1
        recent_react = None

        def check(react, usr):
            return usr != self.bot.user

        while True:
            if str(recent_react) == '⏮':
                i = 0
                await help_msg.edit(embed=helptxt_pages[i])
            elif str(recent_react) == '◀':
                if i > 0:
                    i -= 1
                    await help_msg.edit(embed=helptxt_pages[i])
            elif str(recent_react) == '▶':
                if i < pageEND:
                    i += 1
                    await help_msg.edit(embed=helptxt_pages[i])
            elif str(recent_react) == '⏭':
                i = pageEND
                await help_msg.edit(embed=helptxt_pages[i])

            try:
                recent_react, react_user = await self.bot.wait_for('reaction_add', timeout=30, check=check)
                await help_msg.remove_reaction(recent_react, react_user)
            except asyncio.CancelledError:
                raise
            except asyncio.TimeoutError:
                break

        await help_msg.clear_reactions()

    @commands.command()
    async def ping(self, ctx: commands.Context):
        msgtime = ctx.message.created_at
        nowtime = datetime.datetime.utcnow()
        print(msgtime)
        print(nowtime)
        await ctx.send(f"Pong! `{(nowtime - msgtime).total_seconds() * 1000 :.4f}ms`")

    @commands.command()
    async def roll(self, ctx: commands.Context, *dices: str):
        sendtxt = []
        for _d in dices:
            x = dice(_d)
            if not x:
                continue
            sendtxt.append(f"{_d}: **{' / '.join(x)}**")
        await ctx.send(embed=discord.Embed(title="Dice result", description='\n'.join(sendtxt)))

    @commands.command()
    async def sheetslink(self, ctx: commands.Context):
        await ctx.send("https://docs.google.com/spreadsheets/d/1SA2u-KgTsHcXcsGEbrcfqWugY7sgHIYJpPa5fxNEJYc/edit#gid=0")

    @commands.command()
    @is_owner()
    async def say(self, ctx: commands.Context, *, txt: str):
        if txt:
            await ctx.send(txt)

    @commands.command()
    @is_owner()
    async def sayresult(self, ctx: commands.Context, *, com: str):
        res = eval(com)
        await ctx.send('Result : `' + str(res) + '`')

    @commands.command()
    @is_owner()
    async def run(self, ctx: commands.Context, *, com: str):
        exec(com)
        await ctx.send('Done')

    @commands.command()
    @is_owner()
    async def asyncsayresult(self, ctx: commands.Context, *, com: str):
        res = await eval(com)
        await ctx.send('Result : `' + str(res) + '`')

    @commands.command()
    @is_owner()
    async def asyncrun(self, ctx: commands.Context, *, com: str):
        exec(
            f'async def __ex(): ' +
            ''.join(f'\n    {_l}' for _l in com.split('\n')),
            {**globals(), **locals()}, locals()
        )
        await locals()['__ex']()
        await ctx.send('Done')

    @commands.command()
    @is_owner()
    async def reload(self, ctx: commands.Context):
        global helptxt_pages, Timer, Scrim, Match, MatchMaker, RequestManager
        for module in modules:
            importlib.reload(module)
        helptxt_pages = help_texts.helptxt_pages
        Timer = timer.Timer
        Scrim = scrim_new.Scrim
        Match = match_new.Match
        MatchMaker = matchmaker.MatchMaker
        RequestManager = fixca.RequestManager
        await ctx.send('Reload success')

    @commands.command(name="continue")
    @is_owner()
    async def continue_(self, ctx: commands.Context):
        now_match = self.bot.matches[ctx.author]
        if now_match.match_task.done():
            await now_match.do_match_start()
        else:
            await ctx.send(embed=discord.Embed(
                title="Match is still processing!",
                description="Try again soon.",
                color=discord.Colour.dark_red()
            ))

    @commands.command()
    @is_owner()
    async def showerrormsg(self, ctx: commands.Context):
        now_match = self.bot.matches[ctx.author]
        if (txt := now_match.get_debug_txt()) is not None:
            await ctx.send(embed=discord.Embed(
                title="Error message",
                description=f"```{txt}```",
            ))
        else:
            await ctx.send(embed=discord.Embed(
                title="No error occured... now.",
                description=f"```{now_match.match_task}```",
            ))

    @commands.command(aliases=['status'])
    @is_owner()
    async def status_(self, ctx: commands.Context, status_option: Optional[int], *, status_message: Optional[str]):
        self.bot.status = (
            self.bot.status[0] if status_option is None else DISCORD_STATS[status_option],
            self.bot.status[1] if status_message is None else status_message
        )
        await self.bot.change_presence(
            status=self.bot.status[0],
            activity=discord.Game(self.bot.status[1])
        )
        await ctx.send(f"Applyed ({self.bot.status[0]}, {self.bot.status[1]})")


    @commands.command()
    async def make(self, ctx: commands.Context):
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
    async def teamadd(self, ctx: commands.Context, *, name):
        s = self.bot.datas[ctx.guild.id][ctx.channel.id]
        if s['valid']:
            await s['scrim'].maketeam(name)

    @commands.command(aliases=['tr'])
    async def teamremove(self, ctx: commands.Context, *, name):
        s = self.bot.datas[ctx.guild.id][ctx.channel.id]
        if s['valid']:
            await s['scrim'].removeteam(name)

    @commands.command(name="in")
    async def _in(self, ctx: commands.Context, *, name):
        s = self.bot.datas[ctx.guild.id][ctx.channel.id]
        if s['valid']:
            await s['scrim'].addplayer(name, ctx.author)

    @commands.command()
    async def out(self, ctx: commands.Context):
        s = self.bot.datas[ctx.guild.id][ctx.channel.id]
        if s['valid']:
            await s['scrim'].removeplayer(ctx.author)

    @commands.command(aliases=['score', 'sc'])
    async def _score(self, ctx: commands.Context, sc: int, a: float = 0.0, m: int = 0, gr: str = None):
        s = self.bot.datas[ctx.guild.id][ctx.channel.id]
        if s['valid']:
            await s['scrim'].addscore(ctx.author, sc, a, m, gr)

    @commands.command(aliases=['scr'])
    async def scoreremove(self, ctx: commands.Context):
        s = self.bot.datas[ctx.guild.id][ctx.channel.id]
        if s['valid']:
            await s['scrim'].removescore(ctx.author)

    @commands.command()
    async def submit(self, ctx: commands.Context, calcmode: Optional[str] = None):
        s = self.bot.datas[ctx.guild.id][ctx.channel.id]
        if s['valid']:
            await s['scrim'].submit(calcmode)

    @commands.command()
    async def start(self, ctx: commands.Context):
        s = self.bot.datas[ctx.guild.id][ctx.channel.id]
        if s['valid']:
            await s['scrim'].do_match_start()

    @commands.command()
    async def abort(self, ctx: commands.Context):
        s = self.bot.datas[ctx.guild.id][ctx.channel.id]
        if s['valid']:
            if not s['scrim'].match_task.done():
                s['scrim'].match_task.cancel()

    @commands.command()
    async def end(self, ctx: commands.Context):
        s = self.bot.datas[ctx.guild.id][ctx.channel.id]
        if s['valid']:
            await s['scrim'].end()
            del self.bot.datas[ctx.guild.id][ctx.channel.id]
    """
    @commands.command()
    async def verify(self, ctx: commands.Context, uid: Optional[int] = None):
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
                    add_data = {
                        'key': fixca_key,
                        'discord_id': str(ctx.author.id),
                        'elo': str(self.bot.ratings[v.uid]),
                        'uid': str(v.uid)
                    }
                    print(add_data)
                    if BOT_DEBUG:
                        async with self.bot.session.post("http://ranked-osudroid.kro.kr/userAdd", data=add_data) \
                                as useradd_res:
                            if useradd_res.status != 200:
                                await ctx.send(embed=discord.Embed(
                                    title=f'POST userAdd failed. ({useradd_res.status})',
                                    color=discord.Colour.dark_red()
                                ))
                                del self.bot.ratings[v.uid]
                                return
                            if (useradd_res_json := await useradd_res.json(encoding='utf-8'))['status'] == 'failed':
                                await ctx.send(embed=discord.Embed(
                                    title=f'POST userAdd failed. (FIXCUCKED)',
                                    color=discord.Colour.dark_red()
                                ))
                                print(f'userAdd error : \n{useradd_res_json["error"]}')
                                del self.bot.ratings[v.uid]
                                return
                    await ctx.send(embed=discord.Embed(
                        title=f'Player {ctx.author.display_name} binded to UID {v.uid}.',
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
    """
    
    @commands.command(name="map")
    async def _map(self, ctx: commands.Context, *, name: str):
        await ctx.send(embed=discord.Embed(title="Not allowed now", color=discord.Colour.dark_red()))
        return
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
                    scrim.setmaplength(int(maptime_))
                scrim.setnumber(name)
                scrim.setmode(re.findall('|'.join(modes), name.split(';')[-1])[0])
            await resultmessage.edit(embed=discord.Embed(
                title=f"Map infos Modified!",
                description=f"Map Info : `{scrim.getmapfull()}`\n"
                            f"Map Number : {scrim.getnumber()} / Map Mode : {scrim.getmode()}\n"
                            f"Map SS Score : {scrim.getautoscore()} / Map Length : {scrim.getmaplength()} sec.",
                color=discord.Colour.blue()
            ))

    @commands.command(aliases=['mm'])
    async def mapmode(self, ctx: commands.Context, mode: str):
        await ctx.send(embed=discord.Embed(title="Not allowed now", color=discord.Colour.dark_red()))
        return
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
                            f"Map SS Score : {scrim.getautoscore()} / Map Length : {scrim.getmaplength()} sec.",
                color=discord.Colour.blue()
            ))

    @commands.command(aliases=['mt'])
    async def maptime(self, ctx: commands.Context, _time: int):
        await ctx.send(embed=discord.Embed(title="Not allowed now", color=discord.Colour.dark_red()))
        return
        s = self.bot.datas[ctx.guild.id][ctx.channel.id]
        if s['valid']:
            resultmessage = await ctx.send(embed=discord.Embed(
                title="Calculating...",
                color=discord.Colour.orange()
            ))
            scrim = s['scrim']
            scrim.setmaplength(_time)
            await resultmessage.edit(embed=discord.Embed(
                title=f"Map infos Modified!",
                description=f"Map Info : `{scrim.getmapfull()}`\n"
                            f"Map Number : {scrim.getnumber()} / Map Mode : {scrim.getmode()}\n"
                            f"Map SS Score : {scrim.getautoscore()} / Map Length : {scrim.getmaplength()} sec.",
                color=discord.Colour.blue()
            ))

    @commands.command(aliases=['ms'])
    async def mapscore(self, ctx: commands.Context, sc_or_auto: Union[int, str], *, path: Optional[str] = None):
        await ctx.send(embed=discord.Embed(title="Not allowed now", color=discord.Colour.dark_red()))
        return
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
                            f"Map SS Score : {scrim.getautoscore()} / Map Length : {scrim.getmaplength()} sec.",
                color=discord.Colour.blue()
            ))

    @commands.command(aliases=['l'])
    async def onlineload(self, ctx: commands.Context, checkbit: Optional[int] = None):
        await ctx.send(embed=discord.Embed(title="Not allowed now", color=discord.Colour.dark_red()))
        return
        s = self.bot.datas[ctx.guild.id][ctx.channel.id]
        if s['valid']:
            await s['scrim'].onlineload(checkbit)

    @commands.command()
    async def form(self, ctx: commands.Context, *, f_: str):
        await ctx.send(embed=discord.Embed(title="Not allowed now", color=discord.Colour.dark_red()))
        return
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
    async def maphash(self, ctx: commands.Context, h: str):
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
                            f"Map SS Score : {scrim.getautoscore()} / Map Length : {scrim.getmaplength()} sec.\n"
                            f"Map Hash : `{scrim.getmaphash()}`",
                color=discord.Colour.blue()
            ))

    @commands.command()
    async def timer(self, ctx: commands.Context, action: Union[float, str], name: Optional[str] = None):
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
    async def calc(self, ctx: commands.Context, kind: str, maxscore: d, score: d, acc: d, miss: d):
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
    async def now(self, ctx: commands.Context):
        s = self.bot.datas[ctx.guild.id][ctx.channel.id]
        if s['valid']:
            scrim = s['scrim']
            e = discord.Embed(title="Now scrim info", color=discord.Colour.orange())
            for t in scrim.team:
                e.add_field(
                    name="Team " + t,
                    value='\n'.join([(await self.bot.get_discord_username(x)) for x in scrim.team[t]])
                )
            await ctx.send(embed=e)

    @commands.command(aliases=['pfme'])
    async def profileme(self, ctx: commands.Context, did: Optional[int] = None):
        if did is None:
            did = ctx.author.id
        name = await self.bot.get_discord_username(did)
        userinfo = await self.bot.get_user_info(did)
        if isinstance(userinfo, Exception):
            await ctx.send(embed=discord.Embed(
                title=f"{name} didn't registered!",
                color=discord.Colour.dark_red()
            ))
            return
        e = discord.Embed(
            title=f"Profile of {name}",
            color=discord.Colour(0xdb6ee1)
        )
        e.add_field(
            name="Username",
            value=userinfo['name']
        )
        e.add_field(
            name="O!UID (Original Osu!droid UID)",
            value=userinfo['o_uid']
        )
        e.add_field(
            name="UUID",
            value=userinfo['uuid'],
            inline=False
        )
        e.add_field(
            name="Created time stamp",
            value=datetime.datetime.utcfromtimestamp(userinfo['verified_time']).strftime("%Y-%m-%d %H:%M:%S"),
            inline=False
        )
        e.add_field(
            name="Elo",
            value=f"`{elo_show_form(self.bot.ratings[userinfo['uuid']])}`"
        )
        rankstr = get_elo_rank(self.bot.ratings[userinfo['uuid']])
        rankimgfile = discord.File(TIER_IMAGES[rankstr])
        e.add_field(
            name="Tier",
            value=rankstr
        )
        e.set_image(url=f"attachment://{rankimgfile.filename}")
        await ctx.send(file=rankimgfile, embed=e)

    @commands.command(aliases=['rs'])
    async def recentme(self, ctx: commands.Context, uid: Optional[int] = None):
        if uid is None:
            uid = ctx.author.id
        name = await self.bot.get_discord_username(uid)
        rp: Optional[dict, ValueError, fixca.HttpError, fixca.FixcaError] = await self.bot.get_recent(id_=uid)
        if isinstance(rp, self.bot.req.ERRORS):
            await ctx.send(embed=discord.Embed(
                title=f"Error occurred while loading {name}'s recent record.",
                description=f"{rp}\nCheck the log."
            ))
            return
        e = discord.Embed(
            title=f"{name}'(s) recent play info",
            color=discord.Colour(0x78a94c)
        )
        om: list[osuapi.osu.Beatmap] = await self.bot.osuapi.get_beatmaps(beatmap_hash=rp['mapHash'])
        if len(om) < 1:
            e.add_field(
                name="Map Info",
                value=f"Not available beatmap\n"
                      f"(map id = `{rp['mapId']}` / mapset id = `{rp['mapSetId']}` / map hash = `{rp['mapHash']}`)",
                inline=False
            )
        else:
            om: osuapi.osu.Beatmap = om[0]
            e.add_field(
                name="Map Info",
                value=f"`{makefull(artist=om.artist, title=om.title, author=om.creator, diff=om.version)}`\n"
                      f"(map hash = `{rp['mapHash']}`)\n\n"
                      f"Download link :\n"
                      f"Osu!\t: https://osu.ppy.sh/beatmapsets/{rp['mapSetId']}#osu/{rp['mapId']}\n"
                      f"Chimu\t: https://chimu.moe/en/d/{rp['mapSetId']}\n"
                      f"Beatconnect\t: ~~Not avaliable now~~",
                inline=False
            )
        e.add_field(
            name="Played Time (UTC)",
            value=datetime.datetime.utcfromtimestamp(rp['submitTime']).strftime("%Y-%m-%d %H:%M:%S"),
            inline=False
        )
        e.add_field(
            name="Score Info",
            value=f"{rp['score']:,d} / {rp['acc']}% / {rp['miss']} :x:\n"
                  f"{RANK_EMOJI[rp['rank']]} ({rp['300']} / {rp['100']} / {rp['50']})",
            inline=False
        )
        e.add_field(
            name="Mod",
            value=rp['modList'],
        )
        await ctx.send(embed=e)

    @commands.command(aliases=['q'])
    @is_queue_channel()
    async def queue(self, ctx: commands.Context):
        if self.bot.matches.get(ctx.author):
            await ctx.send(embed=discord.Embed(
                title=f"You can't queue while playing match.",
                color=discord.Colour.dark_red()
            ))
            return
        """elif self.bot.shutdown_datetime - datetime.datetime.now(tz=KST) <= datetime.timedelta(minutes=30):
            await ctx.send(embed=discord.Embed(
                title=f"The bot is supposed to shutdown at {self.bot.shutdown_datetime.strftime('%H:%M')} KST.",
                description=f"You can join the queue until 30 minutes before shutdown "
                            f"({(self.bot.shutdown_datetime - datetime.timedelta(minutes=30)).strftime('%H:%M')} KST).",
                color=discord.Colour.dark_red()
            ))
            return"""
        if 823415179177885706 not in {r.id for r in ctx.author.roles}:
            await ctx.send(embed=discord.Embed(
                title=f"You didn't registered!",
                color=discord.Colour.dark_red()
            ))
        """userinfo = await self.bot.get_user_info(ctx.author.id)
        if isinstance(userinfo, self.bot.req.ERRORS):
            if isinstance(userinfo, fixca.HttpError):
                print(userinfo.data)
                await ctx.send(embed=discord.Embed(
                    title=f"Error occurred",
                    description=f"{userinfo}\nCheck the log."
                ))
            elif userinfo.data['code'] == fixca.FixcaErrorCode.USER_NOT_EXIST:
                await ctx.send(embed=discord.Embed(
                    title=f"You didn't registered!",
                    color=discord.Colour.dark_red()
                ))
            else:
                await ctx.send(embed=discord.Embed(
                    title="Error occurred",
                    description=f"{userinfo}\nCheck the log."
                ))
            return"""
        self.bot.matchmaker.add_player(ctx.author)
        await ctx.send(embed=discord.Embed(
            title=f"{ctx.author.display_name} queued.",
            description=f"(If you already in queue, this will be ignored.)\n"
                        f"Now the number of players in queue (except you) : {len(self.bot.matchmaker.pool)}",
            color=discord.Colour(0x78f7fb)
        ))

    @commands.command(aliases=['uq'])
    @is_queue_channel()
    async def unqueue(self, ctx: commands.Context):
        self.bot.matchmaker.remove_player(ctx.author)
        await ctx.send(embed=discord.Embed(
            title=f"{ctx.author.display_name} unqueued.",
            description=f"**This request could be ignored.**\n"
                        f"Now the number of players in queue (including you) : {len(self.bot.matchmaker.pool)}",
            color=discord.Colour(0x78f7fb)
        ))

    @commands.command()
    @is_verified()
    async def duel(self, ctx: commands.Context):
        if self.bot.matches.get(ctx.author) is not None:
            await ctx.channel.send(embed=discord.Embed(
                title=f"{ctx.author.display_name}, you can't duel while joining your match."
            ))
            return
        if ctx.author.id in self.bot.matchmaker.players_in_pool:
            await ctx.channel.send(embed=discord.Embed(
                title=f"{ctx.author.display_name}, you can't duel while queueing."
            ))
            return
        if self.bot.duel.get(ctx.author) is None:
            opponent = None
            def check(msg):
                return msg.author == ctx.author and msg.channel == ctx.channel
            await ctx.send(f"**{ctx.author.mention}, ping your opponent in 30 seconds.**")
            try:
                while True:
                    response = await self.bot.wait_for('message', timeout=30, check=check)
                    mention = response.mentions
                    if len(mention) == 1:
                        opponent = mention[0]
                        if ctx.author != opponent:
                            break
            except asyncio.TimeoutError:
                await ctx.send(f"**{ctx.author.mention}, time over.**")
                return
            except asyncio.CancelledError:
                return
            assert opponent is not None
            if self.bot.duel.get(opponent) != ctx.author:
                self.bot.duel[ctx.author] = opponent
                await ctx.channel.send(
                    content=f"{opponent.mention}",
                    embed=discord.Embed(
                        title=f"{ctx.author.display_name} is challenging you to duel!",
                        description=f"If you want to accept the duel, use command `/duel` to {ctx.author.mention}!"
                    )
                )
            else:
                del self.bot.duel[opponent]
                self.bot.matches[ctx.author] = self.bot.matches[opponent] = m = Match(self.bot, ctx.author, opponent)
                await m.do_match_start()
        else:
            await ctx.channel.send(embed=discord.Embed(
                title=f"{ctx.author.display_name}, you already challenged another player to a duel."
            ))
    
    @commands.command(aliases=['cancel'])
    @is_verified()
    async def cancel_(self, ctx: commands.Context):
        if self.bot.duel.get(ctx.author) is None:
            return
        else:
            del self.bot.duel[ctx.author]
            await ctx.channel.send(embed=discord.Embed(
                title=f"{ctx.author.display_name}'(s) Duel cancelled"
            ))

    @commands.command()
    @is_verified()
    async def surrender(self, ctx: commands.Context):
        if (m := self.bot.matches.get(ctx.author)) is not None:
            await m.surrender(ctx)


class MyBot(commands.Bot):
    def __init__(self, ses, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.member_names: Dict[int, str] = dict()
        self.datas: dd[Dict[int, dd[Dict[int, Dict[str, Union[int, 'Scrim']]], Callable[[], Dict]]]] = \
            dd(lambda: dd(lambda: {'valid': False, 'scrim': None}))

        self.session: Optional[aiohttp.ClientSession] = ses
        self.req = RequestManager(self)
        self.osuapi = osuapi.OsuApi(api_key, connector=osuapi.AHConnector())

        self.uuid: dd[int, str] = dd(str)
        self.ratings: dd[str, d] = dd(lambda: d(1500))

        self.timers: dd[str, Optional['Timer']] = dd(lambda: None)
        self.timer_count = 0

        self.matches: Dict[discord.Member, 'Match'] = dict()
        self.duel: Dict[discord.Member, discord.Member] = dict()
        self.match_place: Optional[discord.CategoryChannel, discord.Guild] = None
        self.RANKED_OSUDROID_GUILD: Optional[discord.Guild] = None
        self.matchmaker = MatchMaker(self)

        self.finished_matches: List['Match'] = []

        self.status: Tuple[Optional[str], Optional[str]] = (None, None)

        self.shutdown_datetime = get_shutdown_datetime()

        def custon_exception_handler(loop_, context):
            loop_.default_exception_handler(context)
            exception = context.get('exception')
            if isinstance(exception, Exception):
                print(f'[{get_nowtime_str()}] In Mybot.loop:')
                print(get_traceback_str(exception))
                print('='*20)

        self.loop.set_exception_handler(custon_exception_handler)

        self.activity_display_task: Optional[asyncio.Task] = None

    async def get_discord_username(self, x: int) -> str:
        if self.member_names.get(x) is None:
            user = self.get_user(x)
            if user is None:
                user = await self.fetch_user(x)
            self.member_names[x] = user.name
        return self.member_names[x]
    """
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
    """
    async def get_recent(self, user_name=None, id_=None):
        if user_name is None and id_ is not None:
            if isinstance(id_, str):
                user_info = await self.req.get_user_byuuid(uuid=id_)
            elif isinstance(id_, int):
                user_info = await self.req.get_user_bydiscord(d_id=str(id_))
            else:
                return ValueError(f"Wrong type of argument : {id_} ({type(id_).__name__!r})")
            if isinstance(user_info, Exception):
                return user_info
            user_name = user_info['name']
        return await self.req.recent_record(user_name)
    
    async def get_user_info(self, id_=None):
        if isinstance(id_, str):
            res = await self.req.get_user_byuuid(id_)
            if not isinstance(res, Exception):
                self.uuid[res['discordId']] = res['uuid']
            return res
        elif isinstance(id_, int):
            res = await self.req.get_user_bydiscord(str(id_))
            if not isinstance(res, Exception):
                self.uuid[res['discordId']] = res['uuid']
            return res
        else:
            return ValueError(f"Wrong type of argument : {id_} ({type(id_).__name__!r})")


async def _main():
    PREFIX = '/'
    app = MyBot(ses=aiohttp.ClientSession(), command_prefix=PREFIX, help_command=None, intents=intents)
    app.add_cog(MyCog(app))

    bot_task = asyncio.create_task(app.start(token))
    try:
        await bot_task
    except asyncio.CancelledError:
        print('_main() : Cancelled')
        raise
    except Exception as _ex:
        raise
    finally:
        app.osuapi.close()
        await app.change_presence(status=discord.Status.offline)
        await app.loop.shutdown_asyncgens()
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
