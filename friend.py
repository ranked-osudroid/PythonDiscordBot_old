import asyncio, discord, time, gspread, re, datetime, random
from oauth2client.service_account import ServiceAccountCredentials as SAC

scope = [
'https://spreadsheets.google.com/feeds',
'https://www.googleapis.com/auth/drive',
]
jsonfile = 'friend-266503-91ab7f0dce62.json'
credentials = SAC.from_json_keyfile_name(jsonfile, scope)
gs = gspread.authorize(credentials)
gs.login()
spreadsheet = "https://docs.google.com/spreadsheets/d/1SA2u-KgTsHcXcsGEbrcfqWugY7sgHIYJpPa5fxNEJYc/edit#gid=0"
doc = gs.open_by_url(spreadsheet)

worksheet = doc.worksheet('data')

app = discord.Client()

with open("key.txt", 'r') as f:
    token = f.read()

err = "WRONG COMMAND : "

datas = dict()
teams = dict()

timers = dict()

noticechannels = [651054921537421323, 652487382381363200]

neroscoreV2 = lambda maxscore, score, acc, miss: round((score/maxscore * 600000 + (acc**4)/250) * (1-0.003*miss))

analyze = re.compile(r"(.*) [-] (.*) [(](.*)[)] [\[](.*)[\]]")
makefull = lambda author, artist, title, diff, sss: f"{artist} - {title} ({author}) [{diff}]"

def dice(s):
    s = s.partition('d')
    if s[1]=='': return None
    return tuple(str(random.randint(1, int(s[2]))) for i in range(int(s[0])))

class Timer:
    def __init__(self, ch, name, seconds):
        self.channel = ch
        self.name = name
        self.seconds = seconds
        self.nowloop = asyncio.get_event_loop()
        self.starttime = datetime.datetime.utcnow()
        self.task = self.nowloop.create_task(self.run())
    
    async def run(self):
        await asyncio.sleep(self.seconds)
        await self.callback()
    
    async def callback(self):
        global timers
        await self.channel.send(f"Timer **{self.name}**: TIME OVER.")
        del timers[self.name]

    def left(self):
        return self.seconds - (datetime.datetime.utcnow()-self.starttime).total_seconds()


helptxt = discord.Embed(title="COMMANDS DESCRIPTHION",
                        description='**ver. 1.3_20200302**\n'
                                    '<neccesary parameter> (optional parameter) [multi-case parameter]',
                        color=discord.Colour(0xfefefe))
helptxt.add_field(name='f:hello', value='"Huy I\'m here XD"')
helptxt.add_field(name='f:say *<message>*', value='Say <message>.')
helptxt.add_field(name='f:dice *<dice1>* *(dice2)* *(dice3)* ...', value='Roll the dice(s).\n'
                                                                         'Dice input form is *<count>*d*<range>*\n'
                                                                         'ex) 1d100, 3d10\n'
                                                                         'Dice(s) with wrong form will be ignored.')
helptxt.add_field(name='f:timer *(name)* *<second>*', value='Set timer. '
                                                            'You can omit *name*, then the bot will name it as number. '
                                                            '(start from 0)')
helptxt.add_field(name='f:timernow *<name>*', value='See how much time is left.')
helptxt.add_field(name='f:match __team <[add/remove]>__ *<team name>*', value='Add/remove team.')
helptxt.add_field(name='f:match __player <[add/remove]>__ *<team name>*', value='Add/remove **you (not another user)** to/from team.')
helptxt.add_field(name='f:match __score <[add/remove]>__ *<score>* *<acc>* *<miss>*', value='Add/remove score to/from **your** team; if you already added score, it\'ll chandge to new one; the parameter *(score)* can be left out when \'remov\'ing the score.')
helptxt.add_field(name='f:match __submit__', value='Sum scores of each team and give setscore(+1) to the winner team(s); **If there\'s tie, all teams of tie will get a point**.')
helptxt.add_field(name='f:match __now__', value='Show how many scores each team got.')
helptxt.add_field(name='f:match __end__', value='Compare setscores of each team and show who\'s the winner team(s).')
helptxt.add_field(name='f:match __reset__', value='DELETE the current match')
helptxt.add_field(name='f:match __setmap__ *<[kind]>*', value='Set a map of current play\n'
                                                      'f:setmap **infos** _<artist>_**::**_<title>_**::**_<author>_**::**_<difficult>_\n'
                                                      'f:setmap **full** *<artist>* - *<title>* (*<author>**) [*<difficult>*]\n'
                                                      'f:setmap **score** *<autoScore>*\n'
                                                      'f:setmap _**<mapNickname>**_\n\n'
                                                      'If you want to submit with scoreV2, you need to set autoscore '
                                                      'by using "f:setmap score" or "f:setmap _mapNickname_".')

@app.event
async def on_ready():
    print(f"[{time.strftime('%Y-%m-%d %a %X', time.localtime(time.time()))}]")
    print("BOT NAME :", app.user.name)
    print("BOT ID   :", app.user.id)
    game = discord.Game("f:help")
    await app.change_presence(status=discord.Status.online, activity=game)
    print("==========BOT START==========")

@app.event
async def on_message(message):
    ch = message.channel
    msgtime = message.created_at
    nowtime = datetime.datetime.utcnow()
    ping = f"{(nowtime-msgtime).total_seconds() * 1000 :.4f}"
    if credentials.access_token_expired:
        gs.login()
    try:
        global datas, teams, timers
        p = message.author
        g = message.guild.id
        chid = ch.id
        if p == app.user:
            return None
        if message.content.startswith("f:"):
            print(f"[{time.strftime('%Y-%m-%d %a %X', time.localtime(time.time()))} ({ping}ms)] [{message.guild.name};{ch.name}] <{p.name};{p.id}> {message.content}")
            command = message.content[2:].split(' ')


            if command[0]=="hello":
                await ch.send("Huy I'm here XD")
            
            elif command[0]=="ping":
                await ch.send(f"**Pong!**\n`{ping}ms`")

            elif command[0]=="help":
                await ch.send(embed=helptxt)


            elif command[0]=="dice":
                dices = command[1:]
                sendtxt = []
                for d in dices:
                    x = dice(d)
                    if x==None:
                        continue
                    sendtxt.append(f"__{d}__: **{' / '.join(x)}**")
                await ch.send(embed=discord.Embed(title="Dice Roll Result", description='\n'.join(sendtxt)))
            

            elif command[0]=="match":
                if not g in datas:
                    datas[g] = dict()
                if not chid in datas[g]:
                    datas[g][chid] = dict()
                if not g in teams:
                    teams[g] = dict()
                if not chid in teams[g]:
                    teams[g][chid] = dict()
                nowmatch = datas[g][chid]
                nowteams = teams[g][chid]

                if not "setscores" in nowmatch:
                    nowmatch["setscores"] = dict()
                if not "scores" in nowmatch:
                    nowmatch["scores"] = dict()

                if command[1]=="team":
                    teamname = ' '.join(command[3:])
                    if command[2]=="add":
                        if not teamname in nowmatch["setscores"] or not teamname in nowmatch["scores"]:
                            nowmatch["setscores"][teamname] = 0
                            nowmatch["scores"][teamname] = dict()
                            await ch.send(embed=discord.Embed(title=f"Added Team \"{teamname}\".", description=f"Now team list:\n{chr(10).join(nowmatch['scores'].keys())}", color=discord.Colour.blue()))
                        else:
                            await ch.send(embed=discord.Embed(title=f"Team \"{teamname}\" already exists.", description=f"Now team list:\n{chr(10).join(nowmatch['scores'].keys())}", color=discord.Colour.blue()))
                    elif command[2]=="remove":
                        del nowmatch["setscores"][teamname]
                        del nowmatch["scores"][teamname]
                        await ch.send(embed=discord.Embed(title=f"Removed Team \"{teamname}\"", description=f"Now team list:\n{chr(10).join(nowmatch['scores'].keys())}", color=discord.Colour.blue()))
                    else:
                        await ch.send(err+command[2])
                
                elif command[1]=="player":
                    teamname = ' '.join(command[3:])
                    if command[2]=="add":
                        if not p in nowteams:
                            nowteams[p] = teamname
                            nowmatch["scores"][nowteams[p]][p] = (0,0,0)
                            await ch.send(embed=discord.Embed(title=f"Added Player \"{p.display_name}\" to Team \"{teamname}\"", description=f"Now Team {teamname} list:\n{chr(10).join(pl.display_name for pl in nowmatch['scores'][nowteams[p]].keys())}", color=discord.Colour.blue()))
                        else:
                            await ch.send(embed=discord.Embed(title=f"Player \"{p.display_name}\" is already in a team!", description=f"You already participated in Team {nowteams[p]}. If you want to change the team please command 'f:match remove {nowteams[p]}'."))
                    elif command[2]=="remove":
                        temp = nowteams[p]
                        del nowteams[p]
                        del nowmatch["scores"][temp][p]
                        await ch.send(embed=discord.Embed(title=f"Removed Player \"{p.display_name}\" to Team \"{teamname}\"", description=f"Now Team {teamname} list:\n{chr(10).join(pl.display_name for pl in nowmatch['scores'][temp].keys())}", color=discord.Colour.blue()))
                    elif command[2]=="forceadd":
                        if p.name != 'Friendship1226':
                            await ch.send("ACCESS DENIED")
                            return
                        teamname = ' '.join(teamname.split(' ')[:-1])
                        p = app.get_user(int(command[-1]))
                        if not p in nowteams:
                            nowteams[p] = teamname
                            nowmatch["scores"][nowteams[p]][p] = (0,0,0)
                            await ch.send(embed=discord.Embed(title=f"Added Player \"{p.display_name}\" to Team \"{teamname}\"", description=f"Now Team {teamname} list:\n{chr(10).join(pl.display_name for pl in nowmatch['scores'][nowteams[p]].keys())}", color=discord.Colour.blue()))
                        else:
                            await ch.send(embed=discord.Embed(title=f"Player \"{p.display_name}\" is already in a team!", description=f"You already participated in Team {nowteams[p]}. If you want to change the team please command 'f:match remove {nowteams[p]}'."))
                    elif command[2]=="forceremove":
                        if p.name != 'Friendship1226':
                            await ch.send("ACCESS DENIED")
                            return
                        teamname = ' '.join(teamname.split(' ')[:-1])
                        p = app.get_user(int(command[-1]))
                        temp = nowteams[p]
                        del nowteams[p]
                        del nowmatch["scores"][temp][p]
                        await ch.send(embed=discord.Embed(title=f"Removed Player \"{p.display_name}\" to Team \"{teamname}\"", description=f"Now Team {teamname} list:\n{chr(10).join(pl.display_name for pl in nowmatch['scores'][temp].keys())}", color=discord.Colour.blue()))
                    else:
                        await ch.send(err+command[2])

                elif command[1]=="score":
                    if command[2]=="add":
                        nowmatch["scores"][nowteams[p]][p] = tuple(map(float, command[3:6]))
                        await ch.send(embed=discord.Embed(title=f"Added/changed {p.display_name}'(s) score", description=f"{command[3]} to Team {nowteams[p]}", color=discord.Colour.blue()))
                    elif command[2]=="remove":
                        temp = nowmatch["scores"][nowteams[p]][p]
                        nowmatch["scores"][nowteams[p]][p] = (0,0,0)
                        await ch.send(embed=discord.Embed(title=f"Removed {p.display_name}'(s) score", description=f"{temp} from Team {nowteams[p]}", color=discord.Colour.blue()))
                    elif command[2]=="forceadd":
                        if p.name != 'Friendship1226':
                            await ch.send("ACCESS DENIED")
                            return
                        p = app.get_user(int(command[-1]))
                        nowmatch["scores"][nowteams[p]][p] = tuple(map(float, command[3:6]))
                        await ch.send(embed=discord.Embed(title=f"Added/changed {p.display_name}'(s) score", description=f"{command[3]} to Team {nowteams[p]}", color=discord.Colour.blue()))
                    elif command[2]=="forceremove":
                        if p.name != 'Friendship1226':
                            await ch.send("ACCESS DENIED")
                            return
                        p = app.get_user(int(command[-1]))
                        temp = nowmatch["scores"][nowteams[p]][p]
                        nowmatch["scores"][nowteams[p]][p] = (0,0,0)
                        await ch.send(embed=discord.Embed(title=f"Removed {p.display_name}'(s) score", description=f"{temp} from Team {nowteams[p]}", color=discord.Colour.blue()))
                    else:
                        await ch.send(err+command[2])
                
                elif command[1]=="setmap":
                    done = True
                    if not "map" in nowmatch:
                        nowmatch["map"] = dict()
                    if command[2]=="infos":
                        nowmatch["map"]["artist"], nowmatch["map"]["title"], nowmatch["map"]["author"], nowmatch["map"]["diff"] = ' '.join(command[3:]).split('::')
                    elif command[2]=="full":
                        nowmatch["map"]["artist"], nowmatch["map"]["title"], nowmatch["map"]["author"], nowmatch["map"]["diff"] = analyze.match(' '.join(command[3:])).groups()
                    elif command[2]=="score":
                        nowmatch["map"]["sss"] = int(command[3])
                    else:
                        c = worksheet.findall(command[2])
                        if c!=[]:
                            c = c[0]
                            nowmatch["map"]["author"], nowmatch["map"]["artist"], nowmatch["map"]["title"], nowmatch["map"]["diff"], nowmatch["map"]["sss"] = tuple(worksheet.cell(c.row, i+1).value for i in range(5))
                        else:
                            await ch.send(f"NOT FOUND: {command[2]}")
                            done = False
                    if done:
                        await ch.send('DONE')
                            

                elif command[1]=="submit":
                    scores = dict()
                    sums = dict()
                    if len(command)>2:
                        if command[2]=="nero2":
                            if "sss" in nowmatch["map"]:
                                for t in nowmatch["scores"]:
                                    scores[t] = dict()
                                    sums[t] = 0
                                    for p in nowmatch["scores"][t]:
                                        v = neroscoreV2(int(nowmatch["map"]["sss"]), *nowmatch["scores"][t][p])
                                        scores[t][p] = v
                                        sums[t] += v
                            else:
                                await ch.send("You have to set map with auto score.")
                                return
                    else:
                        for t in nowmatch["scores"]:
                            scores[t] = dict()
                            sums[t] = 0
                            for p in nowmatch["scores"][t]:
                                v = nowmatch["scores"][t][p][0]
                                scores[t][p] = v
                                sums[t] += v
                            
                    winners = list(filter(lambda x: sums[x]==max(sums.values()), sums.keys()))
                    mapinfo = "Map: "
                    if not "map" in nowmatch:
                        mapinfo += "None"
                    else:
                        if nowmatch["map"]!=dict():
                            mapinfo += makefull(**nowmatch["map"])
                        else:
                            mapinfo += "None"
                    for w in winners:
                        nowmatch["setscores"][w] += 1
                    desc = mapinfo+"\n\n"+'\n\n'.join(f"__TEAM {i}__: **{sums[i]}**\n"+('\n'.join(f"{j}: {scores[i][j]}" for j in scores[i])) for i in sums)
                    sendtxt = discord.Embed(title=f"__**Team {', '.join(winners)} take(s) a point!**__", description=desc, color=discord.Colour.red())
                    sendtxt.add_field(name=f"\nNow match points:", value='\n'.join(f"__TEAM {i}__: **{nowmatch['setscores'][i]}**" for i in sums))
                    await ch.send(embed=sendtxt)
                    for t in sums:
                        for p in nowmatch["scores"][t]:
                            nowmatch["scores"][t][p] = (0,0,0)
                    nowmatch["map"] = dict()
                    await ch.send(embed=discord.Embed(title="Successfully reset round", color=discord.Colour.red()))
                
                elif command[1]=="now":
                    await ch.send(embed=discord.Embed(title="Current match progress", description='\n'.join(f"__TEAM {i}__: **{nowmatch['setscores'][i]}**" for i in nowmatch["setscores"]), color=discord.Colour.orange()))

                elif command[1]=="end":
                    sums = sorted(list(nowmatch["setscores"].items()), key=lambda x: x[1], reverse=True)
                    tl = []
                    tt = "__**MATCH END**__"
                    for i, t in enumerate(sums):
                        temp = ''
                        if (i+1)%10==1:
                            temp += f"{i+1}st"
                        elif (i+1)%10==2:
                            temp += f"{i+1}nd"
                        elif (i+1)%10==3:
                            temp += f"{i+1}rd"
                        else:
                            temp += f"{i+1}th"
                        tl.append(temp+f" TEAM : {t[0]} <== {t[1]} score(s)")
                    sendtxt = discord.Embed(title=tt, description='\n'.join(tl)+f"\n\n__**TEAM {sums[0][0]}, YOU ARE WINNER!\nCONGRATURATIONS!!!**__", color=discord.Colour.gold())
                    await ch.send(embed=sendtxt)
                
                elif command[1]=="reset":
                    nowmatch = dict()
                    nowteams = dict()
                    await ch.send(embed=discord.Embed(title="Successfully reset.", color=discord.Colour(0x808080)))
                
                else:
                    await ch.send(err+command[1])
                
                datas[g][chid] = nowmatch
                teams[g][chid] = nowteams
            
            
            elif command[0]=="timer":
                if len(command)==2:
                    i = 0
                    while 1:
                        if not (str(i) in timers):
                            break
                        i += 1
                    name = str(i)
                    sec = int(command[1])
                    timers[name] = Timer(ch, name, sec)
                    await ch.send(f"Timer **{name}** set. ({sec}s)")
                else:
                    name, sec = ' '.join(command[1:-1]), int(command[-1])
                    if name in timers:
                        await ch.send("Already running")
                    else:
                        timers[name] = Timer(ch, name, sec)
                        await ch.send(f"Timer **{name}** set. ({sec}s)")

            elif command[0]=="timernow":
                name = command[1]
                if name in timers:
                    await ch.send(f"Timer {name}: {timers[name].left() :.3f}s left.")
                else:
                    await ch.send(f"No timer named {name}!")

            elif command[0]=="say":
                sendtxt = " ".join(command[1:])
                if not message.mention_everyone:
                    for u in message.mentions:
                        sendtxt = sendtxt.replace("<@!"+str(u.id)+">", "*"+u.display_name+"*")
                    if sendtxt!="":
                        print("QUERY:", sendtxt)
                        await ch.send(sendtxt)
                    else:
                        await ch.send("EMPTY")
                else:
                    await ch.send("DO NOT MENTION EVERYONE OR HERE")
            
            
            elif command[0]=="sayresult":
                if p.name=="Friendship1226":
                    await ch.send(eval(' '.join(command[1:])))
                else:
                    await ch.send("ACCESS DENIED")
            
            elif command[0]=="ns2":
                await ch.send(f"__{p.display_name}__'(s) NeroScoreV2 result = __**{neroscoreV2(*map(float, command[1:]))}**__")
            
            elif command[0]=="run":
                if p.name=="Friendship1226":
                    exec(' '.join(command[1:]), globals(), locals())
                    await ch.send("RAN COMMAND(S)")
                else:
                    await ch.send("ACCESS DENIED")

            elif command[0]=="asyncrun":
                if p.name=="Friendship1226":
                    exec('async def __do():\n ' + '\n '.join(' '.join(command[1:]).split('\n')), dict(locals(), **globals()), locals())
                    await locals()['__do']()
                    await ch.send('RAN COMMAND(S)')
                else:
                    await ch.send("ACCESS DENIED")
            
            else:
                await ch.send(err+command[0])

    
    except Exception as ex:
        await ch.send(f"ERROR OCCURED: {ex}")
        print("ERROR OCCURED:", ex)


class Restart(BaseException):
    def __str__(self):
        return "Stop the bot for restart."

async def botoff():
    while 1:
        d = datetime.datetime.utcnow()
        if d.minute==50 and d.hour==19: # 50, 19
            break
        await asyncio.sleep(10) # 10
    await asyncio.gather(
        *[app.get_channel(ch).send("**The bot will be turned off at KST 4:55(UTC 19:55) for about 2 minutes.\n"
                                   "__*Now playing matches will be reset.*__**")
          for ch in noticechannels])
    while 1:
        d = datetime.datetime.utcnow()
        if d.second>=45 and d.minute==54 and d.hour==19: # 45, 54, 19
            break
        await asyncio.sleep(2)
    await asyncio.gather(
        *[app.get_channel(ch).send("**Now turn off.**")
          for ch in noticechannels])
    raise Restart

loop = asyncio.get_event_loop()
try:
    t = loop.create_task(botoff())
    loop.run_until_complete(app.start(token))
except KeyboardInterrupt:
    print("\nForce stop")
except BaseException as ex:
    print(ex)
finally:
    t.cancel()
    loop.run_until_complete(app.logout())
    loop.run_until_complete(loop.shutdown_asyncgens())
    loop.close()