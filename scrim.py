from friend_import import *
from timer import Timer

if TYPE_CHECKING:
    from friend import MyBot

class Scrim:
    def __init__(self,
                 bot: 'MyBot',
                 channel: discord.TextChannel):
        self.bot = bot
        self.loop = self.bot.loop
        self.channel: discord.TextChannel = channel
        self.start_time = datetime.datetime.utcnow().strftime('%Y%m%d%H%M%S%f')

        self.round_start_time = None

        self.match_task: Optional[asyncio.Task] = None

        self.team: Dict[str, Set[int]] = dict()
        # teamname : {member1_id, member2_id, ...}
        self.players: Set[int] = set()
        # {member1_id, member2_id, ...}
        self.findteam: Dict[int, str] = dict()
        # member_id : teamname
        self.setscore: Dict[str, int] = dict()
        # teamname : int
        self.score: Dict[int, Tuple[Tuple[d, d, d], Optional[str], Optional[int]]] = dict()
        # member_id : ((score, acc, miss), grade, mode)

        self.map_artist: Optional[str] = None
        self.map_author: Optional[str] = None
        self.map_title: Optional[str] = None
        self.map_diff: Optional[str] = None
        self.map_time: Optional[d, int] = None

        self.map_number: Optional[str] = None
        self.map_mode: Optional[str] = None
        self.map_auto_score: Optional[int, dd] = None
        self.form: Optional[List[Union[re.Pattern, List[str]]]] = None

        self.map_hash: Optional[str] = None

        self.availablemode: Dict[str, Iterable[int]] = {
            'NM': {0, 2, },
            'HD': {16, 18, },
            'HR': {8, 10, },
            'DT': {32, 34, 48, 50},
            'FM': {1, 3, 8, 10, 16, 17, 18, 19, 24, 26},
            'TB': {0, 1, 2, 3, 8, 10, 16, 17, 18, 19, 24, 26}
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
            self.score[mid] = ((getd(0), getd(0), getd(0)), None, None)
            if do_print:
                await self.channel.send(embed=discord.Embed(
                    title=f"Player {member.name} participates into Team {name}!",
                    description=f"Now player list of Team {name}:\n"
                                f"{chr(10).join([(await self.bot.getusername(pl)) for pl in self.team[name]])}",
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
                                f"{chr(10).join([(await self.bot.getusername(pl)) for pl in self.team[temp]])}",
                    color=discord.Colour.blue()
                ))

    async def addscore(self, member: Optional[discord.Member], score: int, acc: float, miss: int,
                       grade: str = None, mode: Union[int, str] = 0):
        if not member:
            return
        if type(mode) == str:
            mode = modetointfunc(re.findall(r'.{1,2}', mode, re.DOTALL))
        mid = member.id
        if mid not in self.players:
            await self.channel.send(embed=discord.Embed(
                title=f"Player {member.name} is participating in NO team!",
                description=f"You participate first."
            ))
        else:
            self.score[mid] = ((getd(score), getd(acc), getd(miss)), grade, mode)
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
            self.score[mid] = ((getd(0), getd(0), getd(0)), None, None)
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
            calculatedscores[p] = calcf(self.map_auto_score, *self.score[p][0])
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
                    [f"{await self.bot.getusername(p)} - {RANK_EMOJI[self.score[p][1]]} "
                     f"({inttomode(self.score[p][2])}) : "
                     f"{self.score[p][0][0]} / {self.score[p][0][1]}% / {self.score[p][0][2]} :x: "
                     f"= {calculatedscores[p]}"
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
                logtxt.append(f"Player {await self.bot.getusername(p)} = {calculatedscores[p]} "
                              f"({' / '.join(str(x) for x in self.score[p][0])} - {self.score[p][1]} - "
                              f"{inttomode(self.score[p][2])})")
        self.log.append('\n'.join(logtxt))
        r = dict()
        r['score'] = dict()
        r['v2score'] = dict()
        r['start_time'] = self.round_start_time
        r['map'] = self.getmapfull()
        r['number'] = self.getnumber()
        r['mode'] = self.getmode()
        for p in self.score:
            r['score'][p] = self.score[p]
            r['v2score'][p] = calculatedscores[p]
        self.resetmap()
        return r

    def resetmap(self):
        self.map_artist = None
        self.map_author = None
        self.map_title = None
        self.map_diff = None
        self.map_number = None
        self.map_mode = None
        self.map_auto_score = None
        self.map_time = None
        self.map_hash = None
        for p in self.score:
            self.score[p] = ((getd(0), getd(0), getd(0)), None, None)
        self.round_start_time = None

    def setartist(self, artist: str):
        self.map_artist = artist

    def getartist(self) -> str:
        return self.map_artist if self.map_artist is not None else ''

    def settitle(self, title: str):
        self.map_title = title

    def gettitle(self) -> str:
        return self.map_title if self.map_title is not None else ''

    def setauthor(self, author: str):
        self.map_author = author

    def getauthor(self) -> str:
        return self.map_author if self.map_author is not None else ''

    def setdiff(self, diff: str):
        self.map_diff = diff

    def getdiff(self) -> str:
        return self.map_diff if self.map_diff is not None else ''

    def setnumber(self, number: str):
        self.map_number = number

    def getnumber(self) -> str:
        return self.map_number if self.map_number is not None else '-'

    def setmode(self, mode: str):
        self.map_mode = mode

    def getmode(self) -> str:
        return self.map_mode if self.map_mode is not None else '-'

    def setautoscore(self, score: Union[int, d]):
        self.map_auto_score = score

    def getautoscore(self) -> Union[int, d]:
        return self.map_auto_score if self.map_auto_score is not None else -1

    def setmaptime(self, t: Union[int, d]):
        self.map_time = t

    def getmaptime(self) -> Union[int, d]:
        return self.map_time if self.map_time is not None else -1

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

    def setmaphash(self, h: str):
        self.map_hash = h

    def getmaphash(self) -> str:
        return self.map_hash if self.map_hash is not None else 'Undefined'

    async def setform(self, formstr: str, do_print: bool = True):
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
            if a == 'title':
                formstr = formstr.replace(a, f'(?P<{a}>.*)')
            else:
                formstr = formstr.replace(a, f'(?P<{a}>.*?)')
        self.form = [re.compile(formstr), args]
        if do_print:
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
        await self.channel.send(embed=discord.Embed(title="Not allowed now", color=discord.Colour.dark_red()))
        return
        desc = '====== < Process LOG > ======'
        resultmessage: discord.Message = await self.channel.send(embed=discord.Embed(
            title="Processing...",
            color=discord.Colour.red()
        ))
        for team in self.team:
            for player in self.team[team]:
                desc += '\n'
                await resultmessage.edit(embed=discord.Embed(
                    title="Processing...",
                    description=desc,
                    color=discord.Colour.orange()
                ))
                if self.bot.uids.get(player) is None:
                    desc += f"Failed : " \
                            f"{await self.bot.getusername(player)}'s UID is not found."
                    continue
                player_recent_info = await self.bot.getrecent(self.bot.uids[player])
                if player_recent_info is None:
                    desc += f"Failed : " \
                            f"{await self.bot.getusername(player)}'s recent play info can't be parsed."
                    continue
                p = dict()
                p['artist'], p['title'], p['author'], p['diff'] = player_recent_info[0]
                p['score'] = int(player_recent_info[1][1].replace(',', ''))
                p['acc'] = float(player_recent_info[1][4])
                p['miss'] = int(float(player_recent_info[2][0]))
                p['hash'] = player_recent_info[2][1].strip()
                p['rank'] = rankFilenameR.match(player_recent_info[3])
                if p['rank'] is not None:
                    p['rank'] = p['rank'].group(1)
                p['modes'] = set(player_recent_info[1][2].split(', '))
                flag = False
                if self.map_hash is None:
                    if self.form is not None:
                        checkbit = 0
                        m = self.form[0].match(p['diff'])
                        if m is None:
                            desc += f"Failed : " \
                                    f"In {await self.bot.getusername(player)}'s recent play info, " \
                                    f"its difficulty name does NOT fit to the format.\n" \
                                    f"(Its difficulty : `{p['diff']}`)"
                            continue
                        for k in self.form[1]:
                            if k == 'number':
                                mnum = self.map_number.split(';')[-1]
                                pnum = m.group(k)
                                if mnum != pnum:
                                    flag = True
                                    desc += f"Failed : " \
                                            f"In {await self.bot.getusername(player)}'s recent play info, " \
                                            f"its number is wrong.\n(Its number : `{pnum}`)"
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
                                        f"In {await self.bot.getusername(player)}'s recent play info, " \
                                        f"its {k} is wrong.\n" \
                                        f"(Now {k} : `{nowk_edited}` {'(`'+nowk+'`) ' if nowk!=nowk_edited else ''}/ " \
                                        f"Its {k} : `{p[k]}`)"
                    if flag:
                        continue
                else:
                    if p['hash'] != self.map_hash:
                        desc += f"Failed : " \
                                f"In {await self.bot.getusername(player)}'s recent play info, " \
                                f"its hash is wrong.\n" \
                                f"(Now hash : `{self.map_hash}` / Its hash : `{p['hash']}`)"
                        continue
                pmodeint = modetointfunc(p['modes'])
                if self.map_mode is not None:
                    if pmodeint not in self.availablemode[self.map_mode]:
                        desc += f"Failed : " \
                                f"In {await self.bot.getusername(player)}'s recent play info, " \
                                f"its mode is NOT allowed in now map mode. " \
                                f"(Now mode numbers allowed to use : `{self.availablemode[self.map_mode]}` / " \
                                f"Its mode number : `{pmodeint}`)"
                        continue
                p['modes'] = pmodeint
                self.score[player] = ((getd(p['score']), getd(p['acc']), getd(p['miss'])), p['rank'], p['modes'])
                desc += f"Success : " \
                        f"Player {await self.bot.getusername(player)}'s score = " \
                        f"{self.score[player][0][0]}, {self.score[player][0][1]}%, {self.score[player][0][2]}xMISS / " \
                        f"{inttomode(self.score[player][2])} / {self.score[player][1]} rank"
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
            value=blank + '\n'.join(f"{t} : {self.setscore[t]}" for t in self.setscore)
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
        await self.channel.send(embed=discord.Embed(title="Not allowed now", color=discord.Colour.dark_red()))
        return
        if self.match_task is None or self.match_task.done():
            self.match_task = self.loop.create_task(self.match_start())
        else:
            await self.channel.send(embed=discord.Embed(
                title="Match is already processing!",
                description="Try again after the match ends.",
                color=discord.Colour.dark_red()
            ))

    async def match_start(self):
        await self.channel.send(embed=discord.Embed(title="Not allowed now", color=discord.Colour.dark_red()))
        return
        try:
            if self.map_time is None:
                await self.channel.send(embed=discord.Embed(
                    title="The length of the map is not modified!",
                    description="Use `m;maptime` and try again.",
                    color=discord.Colour.dark_red()
                ))
                return
            try:
                self.round_start_time = int(time.time())
                await self.channel.send(embed=discord.Embed(
                    title="MATCH START!",
                    description=f"Map Info : `{self.getmapfull()}`\n"
                                f"Map Number : {self.getnumber()} / Map Mode : {self.getmode()}\n"
                                f"Map SS Score : {self.getautoscore()} / Map Length : {self.getmaplength()} sec\n"
                                f"Allowed modes : "
                                f"`{', '.join(map(inttomode, self.availablemode[self.getmode()]))}`",
                    color=discord.Colour.from_rgb(255, 255, 0)
                ))
                a = self.map_time
                extra_rate = d('1')
                if self.getmode() == 'DT':
                    extra_rate = d('1') / d('1.5')
                self.timer = Timer(self.bot, self.channel, f"{self.start_time}_{self.getnumber()}",
                                   int(self.getmaplength() * extra_rate))
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
                r = await self.submit('nero2')
                return r
            except asyncio.CancelledError:
                await self.channel.send(embed=discord.Embed(
                    title="Match Aborted!",
                    color=discord.Colour.dark_red()
                ))
                raise
            except GeneratorExit:
                return
        except BaseException as ex_:
            print(get_traceback_str(ex_))
            raise ex_
