# TOKEN : NjYwODQxNzg2MTEyOTk5NDI1.XgjODg.qJmbmZVUlhCFcyCMSv76HD-KE_M

import asyncio, discord, time

token = "NjYwODQxNzg2MTEyOTk5NDI1.XgjODg.qJmbmZVUlhCFcyCMSv76HD-KE_M"
app = discord.Client()

datas = dict()
teams = dict()

helptxt = """
v. 20191231.23.0

__**BASIC** COMMAND__

f:hello
==> Huy I'm here XD

f:say blah
==> Say blah


__COMMAND FOR **MATCH**__

f:match __team add__ *TEAM_NAME* 
f:match __team remove__ *TEAM_NAME*
==> Add/remove team to/from team list.

f:match __player add__ *TEAM_NAME*
f:match __player remove__ *TEAM_NAME*
==> Add/remove player to/from team; *There's not that player in that team.*

f:match __score add__ *YOUR_SCORE*
f:match __score remove__ *YOUR_SCORE*
==> Add/remove player's score in player's team; *Removing means making player's score 0*

f:match __submit__
==> Sum scores of each team and give setscore(+1) to the team that got highest scores; If there's same top score, all teams that got top score will have score.

f:match __now__
==> Show *now* setscores of each team.

f:match __end__
==> Make the current match end and show the winner team; ~~*still you can continue the match. I'll fix it later.*~~

f:match reset
==> Delete the whole info of the current match. (team names, players configs, etc.) You have to set those *again from the beginnig*.

"""

@app.event
async def on_ready():
    print("BOT NAME :", app.user.name)
    print("BOT ID   :", app.user.id)
    game = discord.Game("BETA TESTING")
    await app.change_presence(status=discord.Status.online, activity=game)
    print("==========BOT START==========")

@app.event
async def on_message(message):
    try:
        p = message.author
        g = message.guild
        ch = message.channel
        err = "WRONG COMMAND"
        if p == app.user:
            return None
        if message.content.startswith("f:"):
            print(f"[{time.strftime('%Y-%m-%d %b %X', time.localtime(time.time()))}] <{message.author.name}> {message.content}")
            command = message.content[2:].split(' ')


            if command[0]=="hello":
                await ch.send("Huy I'm here XD")
            

            elif command[0]=="help":
                await ch.send(helptxt)
            

            elif command[0]=="match":
                global datas, teams
                if not g in datas:
                    datas[g] = dict()
                if not ch in datas[g]:
                    datas[g][ch] = dict()
                if not g in teams:
                    teams[g] = dict()
                if not ch in teams[g]:
                    teams[g][ch] = dict()
                nowmatch = datas[g][ch]
                nowteams = teams[g][ch]

                if not "setscores" in nowmatch:
                    nowmatch["setscores"] = dict()
                if not "scores" in nowmatch:
                    nowmatch["scores"] = dict()

                if command[1]=="team":
                    if command[2]=="add":
                        if not command[3] in nowmatch["setscores"] or not command[3] in nowmatch["scores"]:
                            nowmatch["setscores"][command[3]] = 0
                            nowmatch["scores"][command[3]] = dict()
                            await ch.send(f"Added Team \"{command[3]}\".")
                        else:
                            await ch.send(f"Team \"{command[3]}\" already exists.")
                    elif command[2]=="remove":
                        del nowmatch["setscores"][command[3]]
                        del nowmatch["scores"][command[3]]
                        await ch.send(f"Removed Team \"{command[3]}\"")
                    else:
                        await ch.send(err)
                
                elif command[1]=="player":
                    if command[2]=="add":
                        nowteams[p] = command[3]
                        nowmatch["scores"][nowteams[p]][p] = 0
                        await ch.send(f"Added Player \"{p.name}\" to Team \"{command[3]}\"")
                    elif command[2]=="remove":
                        del nowteams[p]
                        del nowmatch["scores"][nowteams[p]][p]
                        await ch.send(f"Removed Player \"{p.name}\" to Team \"{command[3]}\"")
                    else:
                        await ch.send(err)

                elif command[1]=="score":
                    if command[2]=="add":
                        nowmatch["scores"][nowteams[p]][p] = int(command[3])
                        await ch.send(f"Added (or changed) {p.name}'(s) score; {command[3]} (Team \"{nowteams[p]}\")")
                    elif command[2]=="remove":
                        nowmatch["scores"][nowteams[p]][p] = 0
                        await ch.send(f"Removed (changed score to 0) {p.name}'(s) score; {command[3]} (Team \"{nowteams[p]}\")")
                    else:
                        await ch.send(err)
                
                elif command[1]=="submit":
                    sums = dict([(t, sum(nowmatch["scores"][t].values())) for t in nowmatch["scores"]])
                    sendtxt = '\n'.join(f"__TEAM {i}__: **{sums[i]}**" for i in sums)
                    if sendtxt!="":
                        winners = list(filter(lambda x: sums[x]==max(sums.values()), sums.keys()))
                        for w in winners:
                            nowmatch["setscores"][w] += 1
                        sendtxt += f"\n\n__**Team {', '.join(winners)} take(s) a point!**__"
                        sendtxt += f"\nNow match points:\n"
                        sendtxt += '\n'.join(f"__TEAM {i}__: **{nowmatch['setscores'][i]}**" for i in sums)
                        await ch.send(sendtxt)
                        for t in sums:
                            for p in nowmatch["scores"][t]:
                                nowmatch["scores"][t][p] = 0
                        await ch.send("Successfully reset scores")
                    else:
                        await ch.send("No teams added!")
                
                elif command[1]=="now":
                    sendtxt = '\n'.join(f"__TEAM {i}__: **{nowmatch['setscores'][i]}**" for i in nowmatch["setscores"])
                    await ch.send(sendtxt)

                elif command[1]=="end":
                    sums = sorted(list(nowmatch["setscores"].items()), key=lambda x: x[1], reverse=True)
                    if sums!=[]:
                        sendtxt = "__**MATCH END**__\n"
                        for i, t in enumerate(sums):
                            sendtxt += "\n"
                            if (i+1)%10==1:
                                sendtxt += f"{i+1}st"
                            elif (i+1)%10==2:
                                sendtxt += f"{i+1}nd"
                            elif (i+1)%10==3:
                                sendtxt += f"{i+1}rd"
                            else:
                                sendtxt += f"{i+1}th"
                            sendtxt +=  f" TEAM : {t[0]} <== {t[1]} score(s)"
                        sendtxt += f"\n\n__**TEAM {sums[0][0]}, YOU ARE WINNER!\nCONGRATURATIONS!!!**__\n\nIf you want to play new match, chat \"f:match reset\""
                        await ch.send(sendtxt)
                    else:
                        await ch.send("No teams added!")
                
                elif command[1]=="reset":
                    nowmatch = dict()
                    nowteams = dict()
                    await ch.send("Successfully reset\nYou need to set teams and players *again*.")
                
                else:
                    await ch.send(err)
                
                datas[g][ch] = nowmatch
                teams[g][ch] = nowteams
            

            elif command[0]=="say":
                sendtxt = " ".join(command[1:])
                if not message.mention_everyone:
                    for u in message.mentions:
                        sendtxt = sendtxt.replace("<@!"+str(u.id)+">", u.name)
                    if sendtxt!="":
                        print("QUERY:", sendtxt)
                        await ch.send(sendtxt)
                    else:
                        await ch.send("EMPTY")
                else:
                    await ch.send("DO NOT MENTION EVERYONE OR HERE")
            
            
            elif command[0]=="run":
                exec(' '.join(command[1:]))
                await ch.send("RAN COMMAND(S)")
            
            else:
                await ch.send(err)

    
    except Exception as ex:
        await ch.send(f"ERROR OCCURED: {ex}")
        print("ERROR OCCURED:", ex)
        
app.run(token)