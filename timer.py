from friend_import import *

if TYPE_CHECKING:
    from friend import MyBot

class Timer:
    def __init__(self,
                 bot: 'MyBot',
                 ch: discord.TextChannel,
                 name: str,
                 seconds: Union[float, d],
                 async_callback=None,
                 args=None):
        self.ownedBot = bot
        self.ownedBot.timers[name] = self
        self.channel: discord.TextChannel = ch
        self.name: str = name
        self.seconds: float = seconds
        self.start_time: datetime.datetime = datetime.datetime.utcnow()
        self.loop = self.ownedBot.loop
        self.message: Optional[discord.Message] = None
        self.done = False
        self.callback = async_callback
        self.args = args
        if self.args is None:
            self.args = tuple()

        self.__task: asyncio.Task = self.loop.create_task(self.run())

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
            return
        except GeneratorExit:
            return
        except BaseException as ex_:
            print(get_traceback_str(ex_))
            raise ex_

    async def edit(self):
        if self.done:
            return
        await self.message.edit(embed=discord.Embed(
                title="TIMER RUNNING...",
                description=f"Timer Name : `{self.name}`\n"
                            f"Time Limit : {self.seconds}\n"
                            f"Time Left : {self.left_sec()}",
                color=discord.Colour.dark_orange()
            ))

    async def timeover(self):
        if self.done: return
        self.done = True
        await self.message.edit(embed=discord.Embed(
            title="TIME OVER!",
            description=f"Timer Name : `{self.name}`\n"
                        f"Time Limit : {self.seconds}",
            color=discord.Colour.dark_grey()
        ))
        await self.call_back(False)

    async def cancel(self):
        if self.done: return
        self.done = True
        self.__task.cancel()
        await self.message.edit(embed=discord.Embed(
            title="TIMER STOPPED!",
            description=f"Timer Name : `{self.name}`\n"
                        f"Time Limit : {self.seconds}\n"
                        f"Time Left : {self.left_sec()}",
            color=discord.Colour.dark_red()
        ))
        await self.call_back(True)

    async def call_back(self, cancelled):
        del self.ownedBot.timers[self.name]
        if self.callback is None:
            return
        await self.callback(cancelled, *self.args)

    def left_sec(self) -> float:
        return round(self.seconds - ((datetime.datetime.utcnow() - self.start_time).total_seconds()), 6)

