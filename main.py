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
    print('finally')
    main_run.cancel()
    loop.run_until_complete(loop.shutdown_asyncgens())
    for t in asyncio.all_tasks(loop):
        try:
            t.cancel()
            t.result()
        except asyncio.CancelledError:
            pass
        except Exception as ex:
            print(t, ex)
    print('Shutdown asyncgens done.')
    loop.close()
    print('loop closed')
