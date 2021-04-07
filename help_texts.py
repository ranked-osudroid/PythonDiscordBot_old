import discord

helptxt_title = "COMMAND DESCRIPTION"
helptxt_desc = """
**ver. 2.20210406**
<this parameter is necessary>
(this parameter is optional)
__choose|one|of|these|parameters__
""".strip()

helptxt_forscrim_name = "\u200b\n\n*스크림 관련 | For scrim*"
helptxt_forscrim_desc1 = """
**m;make**
Make a match. You can use commands below after using this command.

**m;__teamadd|t__ <*name*>**
Create Team *name*

**m;__teamremove|tr__ <*name*>**
Remove Team *name*
(Players in the team will be left.)

**m;in <*name*>**
Participate in Team *name*

**m;out**
Leave Team *name*

**m;map __<*info*|*nickname*>__**
Set a map.

*info* should have format `artist - title (author) [diff]`.
예 : `TUYU - Doro no Bunzai de Watashi dake no Taisetsu o Ubaouda Nante (SnowNiNo_) [Estrangement]`

*nickname* should be a specific string in my private spreadsheet. (Check sheet data by using `m;sheetslink`)
예 : `practice24;NM1`

**m;__mapmode|mm__ <*mode*>**
Set a mode. *mode* should be one of below.
`'NM', 'HD', 'HR', 'DT', 'FM', 'TB'`

**m;__maptime|mt__ <*seconds*>**
Set a map length.

**m;__mapscore|ms__ __<*int*|auto>__ (*filepath*)**
Set autoplay score. This score is used at calculating V2-kind score.

If you enter *int*, the score is set to *int*. *int* should be integer. You don't have to enter *filepath*

If you enter auto, you should enter *filepath*.
*filepath* is the path of `.osu` file that we want to get autoplay score of.
Built-in script will calculate autoplay score, and the score will (mostly) not same with in-game SS score.

**m;__score|sc__ <*score*> (*acc*) (*miss*)**
If you want to upload your score manually, use this.

**m;__scoreremove|scr__**
If you want to remove your score manually, use this.

**m;end**
End the scrim and reset it.
""".strip()

helptxt_forscrim_desc2 = """
**m;__mapmoderule|mr__ <*numbers1*> <*numbers2*> <*numbers3*> <*numbers4*> <*numbers5*> <*numbers6*>**
Set available modes.
*numbers1* ~ *numbers6* should be numbers seperated with `,`(comma).
Each *numbers* means modes that is allowed when the mode is NM, HD, HR, DT, FM or TB.
Referring to below, convert mode combination into number.
```'None': 0,
'Hidden': 1,
'HardRock': 2,
'DoubleTime': 4,
'NoFail': 8,
'HalfTime': 16,
'NightCore': 32,
'Easy': 64
'Precise': 128```

For example, if you want to allow only None and NF when mode is NM, you enter `0,8` at *number1*.
If you want to allow NFDT and NFHDDT when mode is DT, you enter `12,13` at *number4*.

Default value is here.
`m;mapmoderule 0,8 2,10 1,9 4,5,12,13 0,1,2,3,8,9,10,11 0,1,2,3,8,9,10,11`

**m;__onlineload|l__ (*number*)**
Get player's recent plays online. (http://ops.dgsrz.com/)
If you didn't bind with your UID, your play will not be loaded.
If you have wrong title or difficulty name etc, your play will not be loaded too.
If there's mode set by `m;map` or `m;mapmode`, only plays that fit with rules modified by `m;mapmoderule` will be loaded.

If you enter *number*, you can load your play by checking specific element.
`artist=1 / title=2 / author=4 / diff=8 / mode=16`
For example, if you want to check only artist, title, and diff, enter 1+2+8=11.
Default value is 31.

If `m;form` is used, check if play's difficulty name matches with the format, and check their elements.
In this case, *number* is ignored.
""".strip()

helptxt_forscrim_desc3 = """
**m;form <*format*>**
Set a format of difficulty name.
If map infos are in map's difficulty name (like in tournament, using its own pool), you should use this.
Enter *format* using these words: `artist`, `title`, `author`, `diff`, `number`

For example, if one of difficulty names of maps is `[FM1] Everybody Falls [Neli's Eliminated]`,
*form* should be `[number] title [diff]`.

Check if there's some typos, or mis-spacing. (like `[number]title [diff]` or `[number] title (diff)`)

**m;verify <*uid*>**
Used for binding you with *uid*.

**m;submit __(nero2|jet2|osu2)__**
Calculate scores and show result.
`nero2`, `jet2`, and `osu2` are kinds of calculating V2 score.
If you enter one of them, the autoplay score should be set.
If you only chat `m;submit`, the score will be calculated by V1.

nero2 = used in tournaments held in osu!droid (International) discord server.
`V2Score = RoundHalfUp( {(score/auto_score) x 600,000 + (acc/100)^4 x 400,000} x (1 - 0.003 x misses) )`

jet2 = made by 제토넷#8729.
`V2Score = RoundHalfUp( (score/auto_score) x 500,000 + (Max(acc-80, 0)/20)^2 x 500,000 )`

osu2 = used in osu!
`V2Score = RoundHalfUp( (score/auto_score) x 700,000 + (acc/100)^10 x 300,000 )`
\u200b
"""
helptxt_forscrim_desc4 = """
**m;start**
If map datas fully set (infos, autoplay score, length etc.), execute these sequentially
1. wait for map length.
2. wait additional 30 seconds.
3. `m;onlineload` then `m;submit nero2`

**m;abort**
Abort this scrim.

**m;__queue|q__**
Join the match queue.

**m;__unqueue|uq__**
Leave the match queue.

**m;profileme|pfme**
See my UID and ELO.

\u200b
""".strip()

helptxt_other_name = "\u200b\n\nOthers"
helptxt_other_desc = """
**m;ping**
Pong!

**m;timer __<*seconds*|now|cancel>__ (*name*)**
Set timer. Enter time limit at *seconds*. If you didn't enter *name*, then an integer will be its name.
It starts countdown as soon as it's made.

If you enter now, it displays timer *name*'s time left.
If you enter cancel, it stops timer *name*.

**m;roll <*dice*>**
Roll a dice.
*dice* should have this format: (number)d(number). (Yeah what you know.)
You can enter multiple *dice*es.
""".strip()

helptxt_admin = """
m;teamforceadd (tf) <not yet>
m;teamforceremove (tfr) <not yet>
m;say
m;sayresult
m;run
""".strip()

helptxt = discord.Embed(title=helptxt_title, description=helptxt_desc, color=discord.Colour(0xfefefe))
helptxt.add_field(name=helptxt_forscrim_name, value=helptxt_forscrim_desc1, inline=False)
helptxt.add_field(name='\u200b', value=helptxt_forscrim_desc2, inline=False)
helptxt.add_field(name='\u200b', value=helptxt_forscrim_desc3, inline=False)
helptxt.add_field(name='\u200b', value=helptxt_forscrim_desc4, inline=False)
helptxt.add_field(name=helptxt_other_name, value=helptxt_other_desc, inline=False)

if __name__ == '__main__':
    print(len(helptxt_forscrim_desc1))
    print(len(helptxt_forscrim_desc2))
    print(len(helptxt_forscrim_desc3))
    print(len(helptxt_forscrim_desc4))
