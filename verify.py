from friend_import import *
from timer import Timer

if TYPE_CHECKING:
    from friend import MyBot

verify_map_hash = "dab1147095fdafab5d1c9a37cc546ec1"

class Verify:
    def __init__(self, bot: 'MyBot', ch: discord.TextChannel, member: discord.Member, uid: int):
        self.bot = bot
        self.channel = ch
        self.member = member
        self.uid = uid
        self.timer = Timer(bot, ch, f"{member.name}_verify", 300, self.timeover)

    async def do_verify(self):
        player_recent = await self.bot.getrecent(self.uid)
        if player_recent is None:
            return False
        hash = player_recent[2][1].strip()
        if hash == verify_map_hash:
            await self.timer.cancel()
            return True
        return False

    async def timeover(self, cancelled):
        if not cancelled:
            del self.bot.verifies[self.member.id]
            await self.channel.send(embed=discord.Embed(
                title=f'Failed to bind. (Time over)\n',
                description=f'Try again.',
                color=discord.Colour.dark_red()
            ))
