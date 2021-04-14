import discord

helptxt_title = "COMMAND DESCRIPTION "
helptxt_desc = """
**ver. 20210414**
<this parameter is necessary>
(this parameter is optional)
__choose|one|of|these|parameters__
""".strip()

blank = '\u200b'

helptxt_page1 = discord.Embed(title=helptxt_title + "(1/5)", description=helptxt_desc, color=discord.Colour(0xfefefe))
helptxt_page2 = discord.Embed(title=helptxt_title + "(2/5)", description=helptxt_desc, color=discord.Colour(0xfefefe))
helptxt_page3 = discord.Embed(title=helptxt_title + "(3/5)", description=helptxt_desc, color=discord.Colour(0xfefefe))
helptxt_page4 = discord.Embed(title=helptxt_title + "(4/5)", description=helptxt_desc, color=discord.Colour(0xfefefe))
helptxt_page5 = discord.Embed(title=helptxt_title + "(5/5)", description=helptxt_desc, color=discord.Colour(0xfefefe))

helptxt_page1.add_field(
    name="m;make",
    value="Make a scrim. You can use commands below after using this command.",
    inline=False
)

helptxt_page1.add_field(
    name="m;__teamadd|t__ <*name*>",
    value="Create Team *name*."
)

helptxt_page1.add_field(
    name="m;__teamremove|tr__ <*name*>",
    value="""Remove Team *name*.
(Players in the team will be left.)"""
)

helptxt_page1.add_field(
    name=blank,
    value=blank,
    inline=False
)

helptxt_page1.add_field(
    name="m;in <*name*>",
    value="Participate in Team *name*."
)

helptxt_page1.add_field(
    name="m;out",
    value="Leave your team."
)

helptxt_page1.add_field(
    name=blank,
    value=blank,
    inline=False
)

helptxt_page1.add_field(
    name="m;map __<*info*|*nickname*>__",
    value="""Set a map.

*info* should have format `artist - title (author) [diff]`.
Ex) `TUYU - Doro no Bunzai de Watashi dake no Taisetsu o Ubaouda Nante (SnowNiNo_) [Estrangement]`

*nickname* should be a specific string in my private spreadsheet. (Check sheet data by using `m;sheetslink`)
Ex) `practice24;NM1`"""
)

helptxt_page1.add_field(
    name=blank,
    value=blank,
    inline=False
)

helptxt_page1.add_field(
    name="m;__mapmode|mm__ <*mode*>",
    value="""Set a mode. *mode* should be one of below.
`'NM', 'HD', 'HR', 'DT', 'FM', 'TB'`"""
)

helptxt_page1.add_field(
    name="m;__maptime|mt__ <*seconds*>",
    value="Set a map length."
)

helptxt_page2.add_field(
    name="m;__mapscore|ms__ __<*int*|auto>__ (*filepath*)",
    value="""Set autoplay score. This score is used at calculating V2-kind score.

If you enter *int*, the score is set to *int*. *int* should be integer. You don't have to enter *filepath*

If you enter auto, you should enter *filepath*.
*filepath* is the path of `.osu` file that we want to get autoplay score of. (recommended not to use this)
Built-in script will calculate autoplay score, and the score will (mostly) not same with in-game SS score."""
)

helptxt_page2.add_field(
    name=blank,
    value=blank,
    inline=False
)

helptxt_page2.add_field(
    name="m;__mapmoderule|mr__ <*numbers1*> <*numbers2*> <*numbers3*> <*numbers4*> <*numbers5*> <*numbers6*>",
    value="""Set available modes.
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
`m;mapmoderule 0,8 2,10 1,9 4,5,12,13 0,1,2,3,8,9,10,11 0,1,2,3,8,9,10,11`"""
)

helptxt_page2.add_field(
    name=blank,
    value=blank,
    inline=False
)

helptxt_page2.add_field(
    name="m;__maphash|mh__ <*hash*>",
    value="""Set hash of map. *hash* is MD5 value of `.osu` file of map.
```python
with open("target.osu", 'rb') as f:
    hashOfMap = hashlib.md5(f.read()).hexdigest()
```"""
)

helptxt_page2.add_field(
    name=blank,
    value=blank,
    inline=False
)

helptxt_page2.add_field(
    name="m;form <*format*>",
    value="""Set a format of difficulty name.
If map infos are in map's difficulty name (like in tournament, using its own pool), you should use this.
Enter *format* using these words: `artist`, `title`, `author`, `diff`, `number`

For example, if one of difficulty names of maps is `[FM1] Everybody Falls [Neli's Eliminated]`,
*form* should be `[number] title [diff]`.

Check if there's some typos, or mis-spacing. (like `[number]title [diff]` or `[number] title (diff)`)"""
)

helptxt_page3.add_field(
    name="m;__onlineload|l__ (*number*)",
    value="""Get player's recent plays online. (http://ops.dgsrz.com/)
If you didn't bind with your UID, your play will not be loaded.
If you have wrong title or difficulty name etc, your play will not be loaded too.
If there's mode set by `m;map` or `m;mapmode`, only plays that fit with rules modified by `m;mapmoderule` will be loaded.

If you enter *number*, you can load your play by checking specific element.
`artist=1 / title=2 / author=4 / diff=8 / mode=16`
For example, if you want to check only artist, title, and diff, enter 1+2+8=11.
Default value is 31.

If `m;form` is used, check if play's difficulty name matches with the format, and check their elements.
In this case, *number* is ignored.

If `m;maphash` is used once, ignore the form and *number*, and use only mode rule."""
)

helptxt_page3.add_field(
    name=blank,
    value=blank,
    inline=False
)

helptxt_page3.add_field(
    name="m;submit __(nero2|jet2|osu2)__",
    value="""Calculate scores and show result.
`nero2`, `jet2`, and `osu2` are kinds of calculating V2 score.
If you enter one of them, the autoplay score should be set.
If you only chat `m;submit`, the score will be calculated by V1.

nero2 = used in tournaments held in osu!droid (International) discord server.
`V2Score = RoundHalfUp( {(score/auto_score) x 600,000 + (acc/100)^4 x 400,000} x (1 - 0.003 x misses) )`

jet2 = made by 제토넷#8729.
`V2Score = RoundHalfUp( (score/auto_score) x 500,000 + (Max(acc-80, 0)/20)^2 x 500,000 )`

osu2 = used in osu!
`V2Score = RoundHalfUp( (score/auto_score) x 700,000 + (acc/100)^10 x 300,000 )`"""
)

helptxt_page3.add_field(
    name=blank,
    value=blank,
    inline=False
)

helptxt_page3.add_field(
    name="m;__score|sc__ <*score*> (*acc*) (*miss*) (*rank*) (*mode*)",
    value="""If you want to upload your score manually, use this.
Ex) `m;score 12345678 99.1 0 SH NFHRHD"""
)

helptxt_page3.add_field(
    name="m;__scoreremove|scr__",
    value="If you want to remove your score manually, use this."
)

helptxt_page4.add_field(
    name="m;start",
    value="""If map datas fully set (infos, autoplay score, length etc.), execute these sequentially
1. wait for map length.
2. wait additional 30 seconds.
3. `m;onlineload` then `m;submit nero2`"""
)

helptxt_page4.add_field(
    name=blank,
    value=blank,
    inline=False
)

helptxt_page4.add_field(
    name="m;abort",
    value="Abort now running match (by `m;start`)."
)

helptxt_page4.add_field(
    name="m;end",
    value="End the scrim and reset it."
)

helptxt_page5.add_field(
    name="m;verify <*UID*>",
    value="Used for binding you with *UID*.",
)

helptxt_page5.add_field(
    name="m;__profileme|pfme__ (*discordID*)",
    value="See user's UID, ELO, and TIER."
)

helptxt_page5.add_field(
    name=blank,
    value=blank,
    inline=False
)

helptxt_page5.add_field(
    name="m;__queue|q__",
    value="Join the rank queue."
)

helptxt_page5.add_field(
    name="m;__unqueue|uq__",
    value="Leave the rank queue."
)

helptxt_page5.add_field(
    name=blank,
    value=blank,
    inline=False
)

helptxt_page5.add_field(
    name="m;ping",
    value="Pong!",
    inline=False
)

helptxt_page5.add_field(
    name="m;timer __<*seconds*|now|cancel>__ (*name*)",
    value="""Set timer. Enter time limit at *seconds*. If you didn't enter *name*, then an integer will be its name.
It starts countdown as soon as it's made.

If you enter now, it displays timer *name*'s time left.
If you enter cancel, it stops timer *name*."""
)

helptxt_page5.add_field(
    name="m;roll <*dice*>",
    value="""Roll a dice.
*dice* should have this format: (number)d(number). (Ye it's what you know.)
You can enter multiple *dice*es."""
)

helptxt_pages = [helptxt_page1, helptxt_page2, helptxt_page3, helptxt_page4, helptxt_page5]

if __name__ == '__main__':
    pass
