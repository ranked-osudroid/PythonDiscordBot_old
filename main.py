from friend import *
from friend import _main

loop = asyncio.get_event_loop()
main_run = loop.create_task(_main(token_=token))
try:
    loop.run_until_complete(main_run)
except KeyboardInterrupt:
    print('Ctrl+C')
except BaseException as ex:
    print(get_traceback_str(ex))
finally:
    main_run.cancel()
    loop.run_until_complete(loop.shutdown_asyncgens())
    print('Shutdown asyncgens done / close after 3 sec.')
    loop.run_until_complete(asyncio.sleep(3))
    loop.close()
    print('loop closed')