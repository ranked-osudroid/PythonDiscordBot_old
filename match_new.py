import fixca
from friend_import import *
from scrim_new import Scrim
from timer import Timer
from elo_rating import EloRating

if TYPE_CHECKING:
    from friend import MyBot

"""
oma_pools.json
each mappool has this dict
{
    "version": 6,
    "name": "Lobby 42: Random Team Tournament Grand Finals",
    "averageMMR": 2084.831101253304,
    "maps": [
      {
        "mapId": 1618099,
        "mod": "NOMOD",
        "mapName": "Shinra-bansho - Itazura Sensation",
        "difficultyName": "Shira's Lunatic",
        "length": 259,
        "starRating": 6.00795,
        "mapSetId": 745460,
        "maxCombo": 1381,
        "bpm": 192,
        "downloadAvailable": true,
        "mmr": 0,
        "skillset": "NOT_DEFINED",
        "sheetId": "NM1"
      },
      ...
    ],
    "ranked": true,
    "canBeRandomlySelected": true,
    "gamemode": "OSU",
    "uuid": "5ac418ae-0fee-3855-ab8d-8846d7776af2"
}
"""
    
class Match:
    __id = 0

    def __init__(self,
                 bot: 'MyBot',
                 player: discord.Member,
                 opponent: discord.Member,
                 bo: int = 7):
        self.bot = bot
        self.player = player
        self.opponent = opponent
        self.player_info = None
        self.opponent_info = None
        self.BO = bo
        self.__id = Match.__id
        Match.__id += 1
        self.channel: Optional[discord.TextChannel] = None
        self.made_time = datetime.datetime.utcnow()
        self.playID: Dict[int, Optional[dict]] = {self.player.id: None, self.opponent.id: None}
        self.uuid: Dict[int, Optional[str]] = {self.player.id: None, self.opponent.id: None}

        self.mappool_uuid: Optional[str] = None
        self.map_infos: Dict[str, osuapi.osu.Beatmap] = dict()
        self.map_order: List[str] = []
        self.map_tb: Optional[str] = None

        self.scrim: Optional[Scrim] = None
        self.role: Optional[discord.Role] = None
        self.timer: Optional[Timer] = None

        self.round = -1
        # -1 = 매치 생성 전
        # 0 = 플레이어 참가 대기
        # n = n라운드 준비 대기
        self.winfor = (bo / d('2')).to_integral(rounding=decimal.ROUND_HALF_UP)
        self.match_end = False
        self.aborted = False

        self.elo_manager = EloRating(k=ELO_K, stdv=ELO_STDV)

        self.player_ready: bool = False
        self.opponent_ready: bool = False

        self.match_task: Optional[asyncio.Task] = None
        self.readyable: bool = False

    def get_id(self):
        return self.__id
    
    def get_debug_txt(self):
        if self.match_task.exception() is not None:
            return get_traceback_str(self.match_task.exception())

    async def switch_ready(self, subj):
        if not self.readyable: return
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
                title=f"{subj.name} ready!",
                color=discord.Colour.green()
            ))
        else:
            await self.channel.send(embed=discord.Embed(
                title=f"{subj.name} unready!",
                color=discord.Colour.green()
            ))

    def is_all_ready(self):
        return self.player_ready and self.opponent_ready

    def reset_ready(self):
        self.player_ready = False
        self.opponent_ready = False
    
    async def go_next_status(self, timer_cancelled):
        self.readyable = False
        if self.round == -1:
            if timer_cancelled:
                await self.channel.send(embed=discord.Embed(
                    title="ALL READY!",
                    description="Making match & Selecting mappool...",
                    color=discord.Colour.dark_red()
                ))

                await self.scrim.maketeam("RED", False)
                await self.scrim.maketeam("BLUE", False)
                await self.scrim.addplayer("RED", self.player, False)
                await self.scrim.addplayer("BLUE", self.opponent, False)
                self.scrim.setmoderule(
                    {0, 128, },  # NM
                    {16, 144, },  # HD
                    {8, 136, },  # HR
                    {32, 160, },  # DT
                    {0, 1, 8, 16, 17, 24, 128, 129, 136, 144, 145, 152},  # FM
                    {0, 1, 8, 16, 17, 24, 128, 129, 136, 144, 145, 152}  # TB
                )
            else:
                await self.channel.send(embed=discord.Embed(
                    title="The Opponent didn't participate.",
                    description="Match aborted.",
                    color=discord.Colour.dark_red()
                ))
                self.aborted = True
        elif self.round == 0:
            if timer_cancelled:
                await self.channel.send(embed=discord.Embed(
                    title="ALL READY!",
                    description="Preparing the round...",
                    color=discord.Colour.dark_red()
                ))
            else:
                await self.channel.send(embed=discord.Embed(
                    title="The Opponent didn't ready.",
                    description="Match aborted.",
                    color=discord.Colour.dark_red()
                ))
                self.aborted = True
        else:
            if timer_cancelled:
                message = await self.channel.send(embed=discord.Embed(
                    title="ALL READY!",
                    description=f"Round #{self.round} starts in 10...",
                    color=discord.Colour.purple()
                ))
                for i in range(9, -1, -1):
                    await asyncio.gather(message.edit(embed=discord.Embed(
                        title="ALL READY!",
                        description=f"Round #{self.round} starts in **{i}**...",
                        color=discord.Colour.purple()
                    )), asyncio.sleep(1))
            else:
                message = await self.channel.send(embed=discord.Embed(
                    title="READY TIME OVER!",
                    description=f"Force Round #{self.round} to start in 10...",
                    color=discord.Colour.purple()
                ))
                for i in range(9, -1, -1):
                    await asyncio.gather(message.edit(embed=discord.Embed(
                        title="READY TIME OVER!",
                        description=f"**Force** Round #{self.round} to start in **{i}**...",
                        color=discord.Colour.purple()
                    )), asyncio.sleep(1))
            await self.scrim.do_match_start()
            mid, msid = self.scrim.getmapid()
            self.playID = {self.player.id: await self.bot.req.create_playID(self.uuid[self.player.id], mid, msid),
                           self.opponent.id: await self.bot.req.create_playID(self.uuid[self.opponent.id], mid, msid)}
            if isinstance(pl := self.playID[self.player.id], self.bot.req.ERRORS):
                print(pl.data)
                raise pl
            if isinstance(op := self.playID[self.opponent.id], self.bot.req.ERRORS):
                print(op.data)
                raise op
            if (mh := pl['mapHash']) == op['mapHash']:
                self.scrim.setmaphash(mh)
            if not timer_cancelled:
                self.player_ready = True
                self.opponent_ready = True
        self.round += 1
    
    async def do_progress(self):
        if self.match_end or self.aborted:
            return
        elif self.round == -1:
            chname = f"match-{self.__id}"
            guild = self.bot.RANKED_OSUDROID_GUILD
            self.role = await guild.create_role(name=chname, color=discord.Colour.random())
            await self.player.add_roles(self.role)
            await self.opponent.add_roles(self.role)
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(read_messages=False),
                guild.get_role(823415179177885706):
                    discord.PermissionOverwrite(read_messages=True, send_messages=False),  # verified
                guild.get_role(823730690058354688):
                    discord.PermissionOverwrite(read_messages=True, send_messages=True),  # Staff member
                self.role: discord.PermissionOverwrite(read_messages=True, send_messages=True)
            }
            self.channel = await self.bot.match_place.create_text_channel(chname, overwrites=overwrites)
            self.scrim = Scrim(self.bot, self.channel, self)
            self.player_info = await self.bot.get_user_info(self.player.id)
            if isinstance(self.player_info, self.bot.req.ERRORS):
                await self.channel.send(
                    embed=discord.Embed(
                        title="Error occured",
                        description=f"{self.player_info}\nCheck the log."
                    )
                )
                print(self.player_info.data)
                raise self.player_info
            self.opponent_info = await self.bot.get_user_info(self.opponent.id)
            if isinstance(self.opponent_info, self.bot.req.ERRORS):
                await self.channel.send(
                    embed=discord.Embed(
                        title="Error occured",
                        description=f"{self.opponent_info}\nCheck the log."
                    )
                )
                print(self.opponent_info.data)
                raise self.opponent_info
            self.uuid[self.player.id] = self.player_info['uuid']
            self.uuid[self.opponent.id] = self.opponent_info['uuid']
            self.elo_manager.set_player_rating(self.bot.ratings[self.player_info['uuid']])
            self.elo_manager.set_opponent_rating(self.bot.ratings[self.opponent_info['uuid']])
            await self.channel.send(
                f"{self.player.mention} {self.opponent.mention}",
                embed=discord.Embed(
                    title="Match initiated!",
                    description="Chat `rdy` to participate in 2 minutes!"
                )
            )
            self.timer = Timer(self.bot, self.channel, f"Match_{self.__id}_invite", 120, self.go_next_status)
        elif self.round == 0:
            rate_lower, rate_highter = sorted(self.elo_manager.get_ratings())
            # print('Before select_pool_mmr_range :', rate_lower, rate_highter)
            # 1000 ~ 2000 => 1200 ~ 3300
            rate_lower = elo_convert(rate_lower)
            rate_highter = elo_convert(rate_highter)
            # print('After  select_pool_mmr_range :', rate_lower, rate_highter)
            pool_pools = list(filter(
                lambda po: rate_lower - 50 <= po['averageMMR'] <= rate_highter + 50,
                maidbot_pools
            ))
            selected_pool = random.choice(pool_pools)
            while selected_pool['uuid'] in unplayable_pools_uuid:
                selected_pool = random.choice(pool_pools)
            self.mappool_uuid = selected_pool['uuid']
            # print('Selected pool :', selected_pool['name'])
            await self.channel.send(embed=discord.Embed(
                title="Mappool is selected!",
                description=f"Mappool Name : `{selected_pool['name']}`\n"
                            f"Mappool MMR (modified) : "
                            f"{elo_convert_rev(selected_pool['averageMMR']).quantize(d('.0001'))}\n"
                            f"Mappool UUID : `{self.mappool_uuid}`",
                color=discord.Colour(0x0ef37c)
            ))

            calcmsg = await self.channel.send(embed=discord.Embed(
                title="Mappool initiating...",
                color=discord.Colour.blurple()
            ))

            for md in selected_pool['maps']:
                tempmap = await self.bot.osuapi.get_beatmaps(beatmap_id=md['mapId'])
                if len(tempmap) == 0:
                    print('[@] Match.do_progress (mappool initiating) :', md['mapId'], 'error')
                    await calcmsg.edit(content=f"{self.player.mention} {self.opponent.mention}", embed=discord.Embed(
                        title="There's unplayable map in the mappool!",
                        description=f"Map id = {md['mapId']}\n"
                                    f"Call the moderator.\n"
                                    f"**This match will be aborted.**"
                    ))
                    self.aborted = True
                    return
                self.map_infos[md['sheetId']] = tempmap[0]

            maps = dict([(i, []) for i in modes])
            for k in self.map_infos:
                m = moder.match(k)
                if m:
                    maps[m.group(1)].append(k)
            for mm in maps:
                random.shuffle(maps[mm])
            mode_order = ['NM', 'HD', 'HR', 'DT']
            random.shuffle(mode_order)
            for mm in mode_order:
                self.map_order.append(maps[mm].pop())
            self.map_order.append(maps['FM'].pop())
            self.map_order.append(maps['NM'].pop())
            self.map_tb = maps['TB'].pop()

            await calcmsg.edit(content=f"{self.player.mention} {self.opponent.mention}", embed=discord.Embed(
                title="Mappool successfully initiated!",
                description=f"If you got ready, chat `rdy`.\n"
                            f"You have 1 minute to continue.",
                color=discord.Colour.blue()
            ))
            self.timer = Timer(self.bot, self.channel, f"Match_{self.__id}_finalready", 60, self.go_next_status)
        elif (self.map_tb is None and self.round > len(self.map_order)) or self.round > self.BO or \
                self.winfor in set(self.scrim.setscore.values()):
            await self.scrim.end()
            score_diff = \
                self.scrim.setscore["RED"] - self.scrim.setscore["BLUE"]
            div_ = d(2 * self.winfor)
            rate = d('.5') + score_diff / div_
            prate_bef, orate_bef = self.elo_manager.get_ratings()
            pdrate, odrate = self.elo_manager.update(rate, True)
            prate_aft, orate_aft = self.elo_manager.get_ratings()
            self.bot.ratings[self.player_info['uuid']], self.bot.ratings[self.opponent_info['uuid']] = \
                prate_aft, orate_aft
            c = decimal.DefaultContext
            c.rounding = decimal.ROUND_FLOOR
            await self.channel.send(embed=discord.Embed(
                title="MATCH FINISHED",
                description=f"__{self.player.name}__ : "
                            f"{c.to_integral(prate_bef)} => **{c.to_integral(prate_aft)}** "
                            f"({c.quantize(pdrate, d('.1')):+f})\n"
                            f"__{self.opponent.name}__ : "
                            f"{c.to_integral(orate_bef)} => **{c.to_integral(orate_aft)}** "
                            f"({c.quantize(odrate, d('.1')):+f})\n",
                color=discord.Colour(0xcaf32a)
            ))
            self.match_end = True
        else:
            if self.round == self.BO and self.map_tb is not None:
                now_mapnum = self.map_tb
            else:
                now_mapnum = self.map_order[self.round - 1]
            now_beatmap = self.map_infos[now_mapnum]
            self.scrim.setnumber(now_mapnum)
            self.scrim.setartist(now_beatmap.artist)
            self.scrim.setauthor(now_beatmap.creator)
            self.scrim.settitle(now_beatmap.title)
            self.scrim.setdiff(now_beatmap.version)
            self.scrim.setmaplength(now_beatmap.total_length)
            self.scrim.setmode(now_mapnum[:2])
            self.scrim.setmapid(now_beatmap.beatmap_id, now_beatmap.beatmapset_id)
            mid = self.scrim.getmapid()
            download_link = f"Osu!\t: https://osu.ppy.sh/beatmapsets/{mid[1]}#osu/{mid[0]}\n" \
                            f"Chimu\t: https://chimu.moe/en/d/{mid[1]}\n" \
                            f"Beatconnect\t: https://beatconnect.io/b/{mid[1]}"
            await self.channel.send(embed=discord.Embed(
                title=f"Map selected!",
                description=f"Map Info : `{self.scrim.getmapfull()}`\n"
                            f"Map Number : `{self.scrim.getnumber()}`\n"
                            f"Map Length : `{self.scrim.getmaplength()}` sec\n"
                            f"Allowed modes : "
                            f"`{', '.join(map(inttomode, self.scrim.availablemode[self.scrim.getmode()]))}`\n\n"
                            f"*Download links here :*\n{download_link}",
                color=discord.Colour.blue()
            ))
            await self.channel.send(embed=discord.Embed(
                title=f"Only map infos here :",
                description=f"Artist : **{self.scrim.getartist()}**\n"
                            f"Title : **{self.scrim.gettitle()}**\n"
                            f"Author : **{self.scrim.getauthor()}**\n"
                            f"Difficulty : **{self.scrim.getdiff()}**",
                color=discord.Colour.green()
            ))
            await self.channel.send(embed=discord.Embed(
                title=f"Round #{self.round} ready!",
                description="Chat `rdy` in 5 minutes.",
                color=discord.Colour.orange()
            ))
            self.timer = Timer(self.bot, self.channel, f"Match_{self.__id}_{self.round}", 300, self.go_next_status)

    async def match_start(self):
        try:
            while not self.match_end or self.aborted:
                await self.do_progress()
                self.readyable = True
                while True:
                    if self.match_end:
                        await self.channel.send(embed=discord.Embed(
                            title="Match successfully finished",
                            description="Delete after 600 seconds."
                        ))
                        break
                    elif self.aborted:
                        await self.channel.send(embed=discord.Embed(
                            title="Match successfully aborted",
                            description="Delete after 10 seconds."
                        ))
                        break
                    if self.is_all_ready():
                        await self.timer.cancel()
                        self.reset_ready()
                        # if self.scrim is not None and not self.scrim.match_task.done():
                        if self.round > 1 and not (self.match_end or self.aborted):
                            await self.scrim.match_task
                        break
                    await asyncio.sleep(1)
                if self.match_end or self.aborted:
                    # player_updated_elo, opponent_updated_elo = self.elo_manager.get_ratings()
                    break
        except BaseException as ex_:
            print('[@] Match.match_start :')
            print(get_traceback_str(ex_))
            await self.channel.send(embed=discord.Embed(
                title="Error Ocurred",
                description=f"{ex_}\nCheck the log.\n**This match will be aborted.**",
            ))
            raise ex_
        finally:
            if self.scrim.match_task is not None and not self.scrim.match_task.done():
                self.scrim.match_task.cancel()
            self.bot.finished_matches.append(self)
            del self.bot.matches[self.player], self.bot.matches[self.opponent]

            async def do_stuff(*args):
                if not self.match_task.done():
                    self.match_task.cancel()
                await self.channel.delete()
                await self.role.delete()
                self.bot.finished_matches.remove(self)
            self.timer = Timer(
                self.bot,
                self.channel,
                f"Match_{self.__id}_delete",
                10 if self.aborted else 600,
                do_stuff
            )

    async def do_match_start(self):
        if self.match_task is None or self.match_task.done():
            self.match_task = self.bot.loop.create_task(self.match_start())
        else:
            await self.channel.send(embed=discord.Embed(
                title="Match is already processing!",
                description="Try again after the match ends.",
                color=discord.Colour.dark_red()
            ))
