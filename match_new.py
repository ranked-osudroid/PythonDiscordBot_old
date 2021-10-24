from friend_import import *
from scrim import Scrim
from timer import Timer
from mappoolmaker import MappoolMaker
from elo_rating import EloRating

if TYPE_CHECKING:
    from friend import MyBot

"""
oma_pools.json
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
    def __init__(self,
                 bot: 'MyBot',
                 player: discord.Member,
                 opponent: discord.Member,
                 bo: int = 7):
        self.bot = bot
        self.player = player
        self.opponent = opponent
        self.BO = bo