import fixca
from friend_import import *
from timer import Timer

if TYPE_CHECKING:
    from friend import MyBot
    from match_new import MatchScrim

class Scrim:
    def __init__(self,
                 bot: 'MyBot',
                 channel: discord.TextChannel,
                 match_: Optional['MatchScrim'] = None):
        self.bot = bot
        self.match = match_
        self.loop = self.bot.loop
        self.channel: discord.TextChannel = channel
        self.start_time = datetime.datetime.utcnow().strftime('%Y%m%d%H%M%S%f')
        if self.match:
            self.name = f"m{self.match.get_id()}"
        else :
            self.name = self.start_time

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
        self.score: Dict[int, Optional[dict]] = dict()
        
        self.map_artist: Optional[str] = None
        self.map_author: Optional[str] = None
        self.map_title: Optional[str] = None
        self.map_diff: Optional[str] = None
        self.map_length: Optional[d, int] = None
        self.map_number: Optional[str] = None
        self.map_mode: Optional[str] = None
        self.map_hash: Optional[str] = None
        self.map_auto_score: Optional[int, d] = None
        self.map_id: Optional[Tuple[int, int]] = None
        
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
            'id'    : self.setmapid,
        }

        self.getfuncs: Dict[str, Callable[[], str]] = {
            'artist': self.getartist,
            'title' : self.gettitle,
            'author': self.getauthor,
            'diff'  : self.getdiff,
            'number': self.getnumber,
            'mode'  : self.getmode,
            'autosc': self.getautoscore,
            'id'    : self.getmapid,
        }

        self.log: IO = open(f'logs/{self.bot.user.name}_scrim_{self.name}_{self.start_time}.log', 'w', encoding='utf-8')
        self.log.write(f"[{get_nowtime_str()}] Scrim initiated.\n"
                       f"Guild   : {self.channel.guild.name}\n"
                       f"Channel : {self.channel.name}\n"
                       f"Name    : {self.name}\n")
        self.timer: Optional[Timer] = None
        self.PRINT_ON: bool = True

    def __str__(self):
        return f"Scrim({self.name})"

    def __del__(self):
        if not self.log.closed:
            self.log.close()

    def get_player_team(self, member: discord.Member):
        mid = member.id
        if mid not in self.players:
            return
        return self.findteam[mid]

    def write_log(self, s: AnyStr):
        if self.log.closed:
            with open(self.log.name, 'a', encoding='utf-8') as f_:
                f_.write(s)
        else:
            self.log.write(s)

    async def maketeam(self, name: str, do_print: bool = None):
        if do_print is None:
            do_print = self.PRINT_ON
        if self.team.get(name) is not None and do_print:
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
            print(f"[{get_nowtime_str()}] {self}: Team \"{name}\" made.")
            self.log.write(f"[{get_nowtime_str()}] Team \"{name}\" made.\n")

    async def removeteam(self, name: str, do_print: bool = None):
        if do_print is None:
            do_print = self.PRINT_ON
        if self.team.get(name) is None and do_print:
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
            print(f"[{get_nowtime_str()}] {self}: Team \"{name}\" removed.")
            self.log.write(f"[{get_nowtime_str()}] Team \"{name}\" removed.\n")

    async def addplayer(self, name: str, member: Optional[discord.Member], do_print: bool=None):
        if do_print is None:
            do_print = self.PRINT_ON
        if not member:
            return
        mid = member.id
        temp = self.findteam.get(mid)
        if temp and do_print:
            await self.channel.send(embed=discord.Embed(
                title=f"Player {member.name} is already in Team {temp}!",
                description=f"Please leave your team first (`m;out`) and try again."
            ))
        elif self.team.get(name) is None and do_print:
            await self.channel.send(embed=discord.Embed(
                title=f"There's no Team {name}.",
                description=f"Now team list:\n{chr(10).join(self.team.keys())}",
                color=discord.Colour.dark_blue()
            ))
        else:
            self.findteam[mid] = name
            self.team[name].add(mid)
            self.players.add(mid)
            self.score[mid] = {'score': d(0), 'acc': d(0), 'miss': d(0), 'rank': None, 'mode': 0}
            if do_print:
                await self.channel.send(embed=discord.Embed(
                    title=f"Player {member.name} participates into Team {name}!",
                    description=f"Now player list of Team {name}:\n"
                                f"{chr(10).join([(await self.bot.get_discord_username(pl)) for pl in self.team[name]])}",
                    color=discord.Colour.blue()
                ))
            print(f"[{get_nowtime_str()}] {self}: Player \"{member.name}\" participated into Team {name}.")
            self.log.write(f"[{get_nowtime_str()}] Player \"{member.name}\" participated into Team {name}.\n")

    async def removeplayer(self, member: Optional[discord.Member], do_print: bool = None):
        if do_print is None:
            do_print = self.PRINT_ON
        if not member:
            return
        mid = member.id
        temp = self.findteam.get(mid)
        if mid not in self.players and do_print:
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
                                f"{chr(10).join([(await self.bot.get_discord_username(pl)) for pl in self.team[temp]])}",
                    color=discord.Colour.blue()
                ))
            print(f"[{get_nowtime_str()}] {self}: Player \"{member.name}\" left from Team {temp}.")
            self.log.write(f"[{get_nowtime_str()}] Player \"{member.name}\" left from Team {temp}.\n")

    async def addscore(self, 
                       member: Optional[discord.Member], 
                       score: int, acc: str, miss: int,
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
            self.score[mid] = {'score': getd(score), 'acc': acc, 'miss': getd(miss), 'rank': grade, 'mode': mode}
            await self.channel.send(embed=discord.Embed(
                title=f"Player {member.name}'(s) score is modified.",
                description=f"Team {self.findteam[mid]} <== {score}, {acc}%, {miss}xMISS",
                color=discord.Colour.blue()
            ))
            print(f"[{get_nowtime_str()}] {self}: Player \"{member.name}\" added score.")
            self.log.write(f"[{get_nowtime_str()}] Player \"{member.name}\" added score.\n"
                           f"Score : {self.score[mid]['score']:,d}\n"
                           f"Acc   : {self.score[mid]['acc']}%\n"
                           f"Miss  : {self.score[mid]['miss']}\n"
                           f"Rank  : {self.score[mid]['rank']}\n"
                           f"Mode  : {inttomode(self.score[mid]['mode'])}\n")

    async def removescore(self, member: Optional[discord.Member], do_print: bool = None):
        if do_print is None:
            do_print = self.PRINT_ON
        if not member:
            return
        mid = member.id
        if mid not in self.players and do_print:
            await self.channel.send(embed=discord.Embed(
                title=f"Player {member.name} is participating in NO team!",
                description=f"You participate first."
            ))
        else:
            self.score[mid] = {'score': getd(0), 'acc': "00.00", 'miss': getd(0), 'rank': None, 'mode': 0}
            await self.channel.send(embed=discord.Embed(
                title=f"Player {member.name}'(s) score is deleted.",
                color=discord.Colour.blue()
            ))
            print(f"[{get_nowtime_str()}] {self}: Player \"{member.name}\" removed score.")
            self.log.write(f"[{get_nowtime_str()}] Player \"{member.name}\" removed score.\n")
    
    async def submit(self, calcmode: Optional[str] = None):
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
        self.log.write(f"[{get_nowtime_str()}] Submit running... (calcmode : {calcmode})\n")
        calcf = v2dict[calcmode]
        resultmessage = await self.channel.send(embed=discord.Embed(
            title="Calculating...",
            color=discord.Colour.orange()
        ))
        calculatedscores = dict()
        for p in self.score:
            calculatedscores[p] = calcf(
                self.map_auto_score, 
                self.score[p]['score'],
                self.score[p]['acc'],
                self.score[p]['miss']
            )
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
        logtxt = [
            f'Map         : {self.getmapfull()}\n',
            f'Map mode    : {self.getnumber()}\n',
            f'CalcFormula : {calcmode if calcmode else "V1"}\n',
            f'Winner Team : {desc}\n\n'
        ]
        self.log.writelines(logtxt)
        for t in teamscore:
            self.log.write(f"Team {t} : {teamscore[t]}\n")
            temptxt = ""
            for p in self.team[t]:
                temptxt += f"{await self.bot.get_discord_username(p)} - {self.bot.RANK_EMOJI[self.score[p]['rank']]} " \
                           f"({inttomode(self.score[p]['mode'])}) : " \
                           f"{self.score[p]['score']} / {self.score[p]['acc']}% / {self.score[p]['miss']} :x:" + \
                           (f" = {calculatedscores[p]}" if calcmode is not None else "") + "\n"
            sendtxt.add_field(
                name=f"*Team {t} total score : {teamscore[t]}*",
                value=temptxt,
                inline=False
            )
            self.log.write(temptxt+'\n')
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
        self.log.write("Team score:\n")
        for t in teamscore:
            self.log.write(f"{t} : {self.setscore[t]}\n")
        await resultmessage.edit(embed=sendtxt)
        self.resetmap()
        print(f"[{get_nowtime_str()}] {self}.submit(): Submit progress finished.")
        self.log.write(f"[{get_nowtime_str()}] Submit finished.\n")
    
    async def submit_fixca(self):
        self.log.write(f"[{get_nowtime_str()}] Submit running... (calcmode : FIXCA)\n")
        resultmessage = await self.channel.send(embed=discord.Embed(
            title="Calculating...",
            color=discord.Colour.orange()
        ))
        teamscore = dict()
        for t in self.team:
            teamscore[t] = 0
            for p in self.team[t]:
                teamscore[t] += self.score[p]['score']
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
        logtxt = [
            f'Map         : {self.getmapfull()}\n',
            f'Map mode    : {self.getnumber()}\n',
            f'MapNick     : {self.map_number}\n',
            f'CalcFormula : FIXCA\n',
            f'Winner Team : {desc}\n\n'
        ]
        self.log.writelines(logtxt)
        for t in teamscore:
            self.log.write(f"Team {t} : {teamscore[t]}\n")
            temptxt = ""
            for p in self.team[t]:
                temptxt += f"{await self.bot.get_discord_username(p)} - {self.bot.RANK_EMOJI[self.score[p]['rank']]} " \
                           f"({inttomode(self.score[p]['mode'])}) : " \
                           f"{self.score[p]['score']} / {self.score[p]['acc']}% / {self.score[p]['miss']} :x:\n" \
                           f"({self.score[p].get('300')}, {self.score[p].get('100')}, {self.score[p].get('50')})" \
                           + "\n"
            sendtxt.add_field(
                name=f"*Team {t} total score : {teamscore[t]}*",
                value=temptxt,
                inline=False
            )
            self.log.write(temptxt+'\n')
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
        self.log.write("Team score:\n")
        for t in teamscore:
            self.log.write(f"{t} : {self.setscore[t]}\n")
        await resultmessage.edit(embed=sendtxt)
        self.resetmap()
        print(f"[{get_nowtime_str()}] {self}.submit_fixca(): Submit progress finished.")
        self.log.write(f"[{get_nowtime_str()}] Submit finished.\n")
        return teamscore
    
    def resetmap(self):
        self.map_artist = None
        self.map_author = None
        self.map_title = None
        self.map_diff = None
        self.map_number = None
        self.map_mode = None
        self.map_auto_score = None
        self.map_length = None
        self.map_hash = None
        for p in self.score:
            self.score[p] = {'score': d(0), 'acc': "00.00", 'miss': d(0), 'rank': None, 'mode': 0}
        self.round_start_time = None
        self.log.write(f"[{get_nowtime_str()}] Map reset.\n")
    
    def setartist(self, artist: str):
        self.map_artist = artist
        self.log.write(f"[{get_nowtime_str()}] Map modified: artist => {artist}\n")

    def getartist(self) -> str:
        return self.map_artist if self.map_artist is not None else ''

    def settitle(self, title: str):
        self.map_title = title
        self.log.write(f"[{get_nowtime_str()}] Map modified: title => {title}\n")

    def gettitle(self) -> str:
        return self.map_title if self.map_title is not None else ''

    def setauthor(self, author: str):
        self.map_author = author
        self.log.write(f"[{get_nowtime_str()}] Map modified: author => {author}\n")

    def getauthor(self) -> str:
        return self.map_author if self.map_author is not None else ''

    def setdiff(self, diff: str):
        self.map_diff = diff
        self.log.write(f"[{get_nowtime_str()}] Map modified: diff => {diff}\n")

    def getdiff(self) -> str:
        return self.map_diff if self.map_diff is not None else ''

    def setnumber(self, number: str):
        self.map_number = number
        self.log.write(f"[{get_nowtime_str()}] Map modified: number => {number}\n")

    def getnumber(self) -> str:
        return self.map_number if self.map_number is not None else '-'

    def setmode(self, mode: str):
        self.map_mode = mode
        self.log.write(f"[{get_nowtime_str()}] Map modified: mode => {mode}\n")

    def getmode(self) -> str:
        return self.map_mode if self.map_mode is not None else '-'

    def setautoscore(self, score: Union[int, d]):
        self.map_auto_score = score
        self.log.write(f"[{get_nowtime_str()}] Map modified: auto_score => {score}\n")

    def getautoscore(self) -> Union[int, d]:
        return self.map_auto_score if self.map_auto_score is not None else -1

    def setmaplength(self, t: Union[int, d]):
        self.map_length = t
        self.log.write(f"[{get_nowtime_str()}] Map modified: length => {t}\n")

    def getmaplength(self) -> Union[int, d]:
        return self.map_length if self.map_length is not None else -1

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
        self.log.write(f"[{get_nowtime_str()}] Map modified: hash => {h}\n")

    def getmaphash(self) -> str:
        return self.map_hash if self.map_hash is not None else 'Undefined'
    
    def setmapid(self, mapid, mapsetid):
        self.map_id = (mapid, mapsetid)
        self.log.write(f"[{get_nowtime_str()}] Map modified: ID => {mapid}, {mapsetid}\n")
    
    def getmapid(self):
        return self.map_id
    
    def setmoderule(
            self,
            nm: Optional[Iterable[int]],
            hd: Optional[Iterable[int]],
            hr: Optional[Iterable[int]],
            dt: Optional[Iterable[int]],
            fm: Optional[Iterable[int]],
            tb: Optional[Iterable[int]]
    ):
        if nm or hd or hr or dt or fm or tb:
            self.log.write(f"[{get_nowtime_str()}] Map modified: rule\n")
        if nm:
            self.availablemode['NM'] = nm
            self.log.write(f"NM : {nm}\n")
        if hd:
            self.availablemode['HD'] = hd
            self.log.write(f"HD : {hd}\n")
        if hr:
            self.availablemode['HR'] = hr
            self.log.write(f"HR : {hr}\n")
        if dt:
            self.availablemode['DT'] = dt
            self.log.write(f"DT : {dt}\n")
        if fm:
            self.availablemode['FM'] = fm
            self.log.write(f"FM : {fm}\n")
        if tb:
            self.availablemode['TB'] = tb
            self.log.write(f"TB : {tb}\n")

    async def onlineload(self):
        self.log.write(f"[{get_nowtime_str()}] Onlineload running...\n")
        desc = '====== < Process LOG > ======'
        resultmessage: discord.Message = await self.channel.send(embed=discord.Embed(
            title="Processing...",
            color=discord.Colour.red()
        ))
        for team in self.team:
            for player in self.team[team]:
                desc += '\n'
                playername = await self.bot.get_discord_username(player)
                await resultmessage.edit(embed=discord.Embed(
                    title="Processing...",
                    description=desc,
                    color=discord.Colour.orange()
                ))
                if self.match:
                    player_recent_info = await self.bot.get_recent(
                        id_=self.match.uuid[player])
                else:
                    uuid_ = await self.bot.get_user_info(player)
                    if isinstance(uuid_, self.bot.req.ERRORS):
                        print(f"[{get_nowtime_str()}] {self}.onlineload(): "
                              f"Failed to load data of {playername} ({uuid_})")
                        print(uuid_.data)
                        temptxt = f"Failed : " \
                                  f"Error occurred while getting {playername}'s info ({uuid_})"
                        desc += temptxt
                        self.log.write(temptxt+"\n")
                        continue
                    player_recent_info = await self.bot.get_recent(
                        id_=uuid_['uuid'])
                if isinstance(player_recent_info, self.bot.req.ERRORS):
                    print(f"[{get_nowtime_str()}] {self}.onlineload(): "
                          f"Failed to load data of {playername} ({player_recent_info})")
                    print(player_recent_info.data)
                    if player_recent_info.data['code'] == fixca.FixcaErrorCode.PLAYER_NO_RECORDS:
                        temptxt = f"Failed : " \
                                  f"{playername} didn't played the map"
                        desc += temptxt
                        self.log.write(temptxt+"\n")
                    else:
                        temptxt = f"Failed : " \
                                  f"Error occurred while getting {playername}'s recent record ({player_recent_info})"
                        desc += temptxt
                        self.log.write(temptxt+"\n")
                    continue
                if player_recent_info is None:
                    print(f"[{get_nowtime_str()}] {self}.onlineload(): "
                          f"Failed to load data of {playername} (parse error)")
                    temptxt = f"Failed : " \
                              f"{playername}'s recent play info can't be parsed."
                    desc += temptxt
                    self.log.write(temptxt+"\n")
                    continue
                if player_recent_info['mapHash'] != self.getmaphash():
                    print(f"[{get_nowtime_str()}] {self}.onlineload(): "
                          f"Failed to load data of {playername} (different hash)\n"
                          f"Player HASH : {player_recent_info['mapHash']}\n"
                          f"Map    HASH : {self.getmaphash()}")
                    temptxt = f"Failed : " \
                              f"In {playername}'s recently played info, its hash is different.\n" \
                              f"(Hash of the map : `{self.getmaphash()}` / " \
                              f"Your hash : `{player_recent_info['mapHash']}`)"
                    desc += temptxt
                    self.log.write(temptxt+"\n")
                    continue
                modeint = modetointfunc(re.findall(r'.{1,2}', player_recent_info['modList'], re.DOTALL))
                if self.map_mode is not None and \
                    modeint not in self.availablemode[self.map_mode]:
                    print(f"[{get_nowtime_str()}] {self}.onlineload(): "
                          f"Failed to load data of {playername} (not allowed mode)\n"
                          f"Player MODE : {modeint}\n"
                          f"Map    MODE : {self.availablemode[self.map_mode]}")
                    temptxt = f"Failed : " \
                              f"In {playername}'s recent play info, " \
                              f"its mode is NOT allowed in now map mode. " \
                              f"(Modes allowed to use in this round : `{self.availablemode[self.map_mode]}` / " \
                              f"Your mode : `{player_recent_info['modList']} = {modeint}`)"
                    desc += temptxt
                    self.log.write(temptxt+"\n")
                    continue
                self.score[player] = player_recent_info
                self.score[player]['score'] = d(self.score[player]['score'])
                if self.map_mode == 'FM' and (modeint == 0 or modeint == 128):
                    self.score[player]['score'] *= d('.8')
                self.score[player]['acc'] = d(self.score[player]['acc'][:-1])
                self.score[player]['miss'] = d(self.score[player]['miss'])
                self.score[player]['mode'] = modeint
                temptxt = f"Success : " \
                          f"Player {playername}'s score = " \
                          f"{self.score[player]['score']}, {self.score[player]['acc']}%, " \
                          f"{self.score[player]['miss']} MISS(es) / " \
                          f"{self.score[player]['modList']} / {self.score[player]['rank']} rank"
                desc += temptxt
                self.log.write(temptxt+"\n")
                print(f"[{get_nowtime_str()}] {self}.onlineload(): Success to load data of {playername}")
        await resultmessage.edit(embed=discord.Embed(
            title="Calculation finished!",
            description=desc,
            color=discord.Colour.green()
        ))
        print(f"[{get_nowtime_str()}] {self}.onlineload(): Progress finished.")
        self.log.write(f"[{get_nowtime_str()}] Onlineload finished.\n")

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
        self.log.write(f"[{get_nowtime_str()}] Scrim END\n"
                       f"Team score:\n")
        for t in self.setscore:
            self.log.write(f"{t} : {self.setscore[t]}\n")
        self.log.close()
        with open(self.log.name, 'rb') as fp_:
            await self.channel.send(
                embed=sendtxt,
                file=discord.File(fp_)
            )
        print(f"[{get_nowtime_str()}] {self}.end(): Scrim finished.")
        return winnerteam
        
    async def do_match_start(self):
        if self.match_task is None or self.match_task.done():
            self.match_task = self.loop.create_task(self.match_start())
        else:
            await self.channel.send(embed=discord.Embed(
                title="Match is already processing!",
                description="Try again after the match ends.",
                color=discord.Colour.dark_red()
            ))

    async def match_start(self):
        self.log.write(f"[{get_nowtime_str()}] match_start running...\n")
        try:
            if self.map_length is None:
                await self.channel.send(embed=discord.Embed(
                    title="The length of the map is not modified!",
                    description="Use `m;maptime` and try again.",
                    color=discord.Colour.dark_red()
                ))
                self.log.write(f"[{get_nowtime_str()}] match_start(): Map time not set.\n")
                return
            try:
                self.round_start_time = int(time.time())
                await self.channel.send(embed=discord.Embed(
                    title="MATCH START!",
                    description=f"Map Info : `{self.getmapfull()}`\n"
                                f"Map Number : {self.getnumber()} / Map Mode : {self.getmode()}\n"
                                f"Map Length : {self.getmaplength()} sec\n"
                                f"Allowed modes : "
                                f"`{', '.join(map(inttomode, self.availablemode[self.getmode()]))}`",
                    color=discord.Colour.from_rgb(255, 255, 0)
                ))
                extra_rate = d('1')
                if self.getmode() == 'DT':
                    extra_rate = d('1') / d('1.5')
                self.timer = Timer(self.bot, self.channel, f"{self.name}_{self.getnumber()}",
                                   int(self.getmaplength() * extra_rate))
                self.log.write(f"[{get_nowtime_str()}] match_start(): "
                               f"Waiting until map finish... ({self.timer.seconds} seconds)\n")
                await self.timer.task
                timermessage = await self.channel.send(embed=discord.Embed(
                    title=f"MAP TIME OVER!",
                    color=discord.Colour.from_rgb(128, 128, 255)
                ))
                self.log.write(f"[{get_nowtime_str()}] match_start(): "
                               f"Map finished. Waiting more 30 seconds...\n")
                for i in range(30, -1, -1):
                    await asyncio.gather(timermessage.edit(embed=discord.Embed(
                        title=f"MAP TIME OVER!",
                        description=f"There's additional {i} second(s) left.",
                        color=discord.Colour.from_rgb(128, 128, 255)
                    )), asyncio.sleep(1))
                await self.channel.send(embed=discord.Embed(
                    title=f"MAP EXTRA TIME OVER!",
                    description="Online loading...",
                    color=discord.Colour.from_rgb(128, 128, 255)
                ))
                self.log.write(f"[{get_nowtime_str()}] match_start(): "
                               f"ALL done, onlineload() calling...\n")
                await self.onlineload()
                self.log.write(f"[{get_nowtime_str()}] match_start(): "
                               f"onlineload() done, submit() calling...\n")
                if self.match is None:
                    await self.submit()
                else:
                    await self.submit_fixca()
                self.log.write(f"[{get_nowtime_str()}] match_start(): "
                               f"submit() done.\n")
            except asyncio.CancelledError:
                await self.channel.send(embed=discord.Embed(
                    title="Match Aborted!",
                    color=discord.Colour.dark_red()
                ))
                self.log.write(f"[{get_nowtime_str()}] match_start(): aborted.\n")
                raise
            except GeneratorExit:
                return
        except BaseException as ex_:
            print(f'[{get_nowtime_str()}] {self}.match_start() :')
            print(get_traceback_str(ex_))
            raise ex_
