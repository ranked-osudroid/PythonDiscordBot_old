from friend import *
from friend import _main

with open('testkey.txt', 'r') as f:
    ttoken = f.read().strip()

RANK_EMOJI = {
    'A': "<:rankingA:829276952649138186>",
    'B': "<:rankingB:829276952728174612>",
    'C': "<:rankingC:829276952229052488>",
    'D': "<:rankingD:829276952778113044>",
    'S': "<:rankingS:829276952748883998>",
    'SH': "<:rankingSH:829276952622923786>",
    'X': "<:rankingX:829276952841158656>",
    'XH': "<:rankingXH:829276952430772255>",
    None: ":question:"
}

loop = asyncio.get_event_loop()
main_run = loop.create_task(_main(
    token_=ttoken,
    match_place_id=824985957165957151,
    RANKED_OSUDROID_GUILD_ID=TEST_GUILD_ID,
    RANK_EMOJI=RANK_EMOJI
))
try:
    loop.run_until_complete(main_run)
except KeyboardInterrupt:
    print('Ctrl+C')
except BaseException as ex:
    print(get_traceback_str(ex))
finally:
    main_run.cancel()
    loop.run_until_complete(loop.shutdown_asyncgens())
    for t in asyncio.all_tasks(loop):
        try:
            t.cancel()
        except asyncio.CancelledError:
            pass
    print('Shutdown asyncgens done / close after 3 sec.')
    loop.run_until_complete(asyncio.sleep(3))
    loop.close()
    print('loop closed')