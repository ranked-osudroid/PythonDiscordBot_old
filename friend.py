import asyncio, discord, time

app = discord.Client()

with open("key.txt", 'r') as f:
    token = f.read()

err = "WRONG COMMAND : "

datas = dict()
teams = dict()

neroscoreV2 = lambda maxscore, score, acc, miss: round((score/maxscore * 600000 + (acc**4)/250) * (1-0.003*miss))

helptxt = discord.Embed(title="COMMANDS DESCRIPTHION", description='**ver. 1.2_20200106**', color=discord.Colour(0xfefefe))
helptxt.add_field(name='f:hello', value='"Huy I\'m here XD"')
helptxt.add_field(name='f:say *<message>*', value='Say <message>.')
helptxt.add_field(name='f:match __team [add/remove]__ *<team name>*', value='Add/remove team.')
helptxt.add_field(name='f:match __player [add/remove]__ *<team name>*', value='Add/remove **you (not another user)** to/from team.')
helptxt.add_field(name='f:match __score [add/remove]__ *(score)*', value='Add/remove score to/from **your** team; if you already added score, it\'ll chandge to new one; the parameter *(score)* can be left out when \'remov\'ing the score.')
helptxt.add_field(name='f:match __submit__', value='Sum scores of each team and give setscore(+1) to the winner team(s); **If there\'s tie, all teams of tie will get a point**.')
helptxt.add_field(name='f:match __now__', value='Show how many scores each team got.')
helptxt.add_field(name='f:match __end__', value='Compare setscores of each team and show who\'s the winner team(s).')
helptxt.add_field(name='f:match __reset__', value='DELETE the current match')

@app.event
async def on_ready():
    print("BOT NAME :", app.user.name)
    print("BOT ID   :", app.user.id)
    game = discord.Game("f:help")
    await app.change_presence(status=discord.Status.online, activity=game)
    print("==========BOT START==========")

@app.event
async def on_message(message):
    ch = message.channel
    try:
        global datas, teams
        p = message.author
        g = message.guild.id
        chid = ch.id
        if p == app.user:
            return None
        if message.content.startswith("f:"):
            print(f"[{time.strftime('%Y-%m-%d %a %X', time.localtime(time.time()))}] [{message.guild.name};{ch.name}] <{p.name};{p.id}> {message.content}")
            command = message.content[2:].split(' ')


            if command[0]=="hello":
                await ch.send("Huy I'm here XD")
            

            elif command[0]=="help":
                await ch.send(embed=helptxt)
            

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
                            nowmatch["scores"][nowteams[p]][p] = 0
                            await ch.send(embed=discord.Embed(title=f"Added Player \"{p.display_name}\" to Team \"{teamname}\"", description=f"Now Team {teamname} list:\n{chr(10).join(pl.display_name for pl in nowmatch['scores'][nowteams[p]].keys())}", color=discord.Colour.blue()))
                        else:
                            await ch.send(embed=discord.Embed(title=f"Player \"{p.display_name}\" is already in a team!", description=f"You already participated in Team {nowteams[p]}. If you want to change the team please command 'f:match remove {nowteams[p]}'."))
                    elif command[2]=="remove":
                        temp = nowteams[p]
                        del nowteams[p]
                        del nowmatch["scores"][temp][p]
                        await ch.send(embed=discord.Embed(title=f"Removed Player \"{p.display_name}\" to Team \"{teamname}\"", description=f"Now Team {teamname} list:\n{chr(10).join(pl.display_name for pl in nowmatch['scores'][temp].keys())}", color=discord.Colour.blue()))
                    else:
                        await ch.send(err+command[2])

                elif command[1]=="score":
                    if command[2]=="add":
                        nowmatch["scores"][nowteams[p]][p] = int(command[3])
                        await ch.send(embed=discord.Embed(title=f"Added/changed {p.display_name}'(s) score", description=f"{command[3]} to Team {nowteams[p]}", color=discord.Colour.blue()))
                    elif command[2]=="remove":
                        temp = nowmatch["scores"][nowteams[p]][p]
                        nowmatch["scores"][nowteams[p]][p] = 0
                        await ch.send(embed=discord.Embed(title=f"Removed {p.display_name}'(s) score", description=f"{temp} from Team {nowteams[p]}", color=discord.Colour.blue()))
                    else:
                        await ch.send(err+command[2])
                
                elif command[1]=="submit":
                    sums = dict([(t, sum(nowmatch["scores"][t].values())) for t in nowmatch["scores"]])
                    winners = list(filter(lambda x: sums[x]==max(sums.values()), sums.keys()))
                    for w in winners:
                        nowmatch["setscores"][w] += 1
                    sendtxt = discord.Embed(title=f"__**Team {', '.join(winners)} take(s) a point!**__", description='\n'.join(f"__TEAM {i}__: **{sums[i]}**" for i in sums), color=discord.Colour.red())
                    sendtxt.add_field(name=f"\nNow match points:", value='\n'.join(f"__TEAM {i}__: **{nowmatch['setscores'][i]}**" for i in sums))
                    await ch.send(embed=sendtxt)
                    for t in sums:
                        for p in nowmatch["scores"][t]:
                            nowmatch["scores"][t][p] = 0
                    await ch.send(embed=discord.Embed(title="Successfully reset scores", color=discord.Colour.red()))
                
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
            

            elif command[0]=="say":
                sendtxt = " ".join(command[1:])
                if not message.mention_everyone:
                    for u in message.mentions:
                        sendtxt = sendtxt.replace("<@!"+str(u.id)+">", u.display_name)
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
            
            else:
                await ch.send(err+command[0])

    
    except Exception as ex:
        await ch.send(f"ERROR OCCURED: {ex}")
        print("ERROR OCCURED:", ex)
        

loop = asyncio.get_event_loop()
try:
    loop.run_until_complete(app.start(token))
except KeyboardInterrupt:
    print()
    loop.run_until_complete(app.logout())
finally:
    loop.close()