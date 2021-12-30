from friend import *
from friend import _main
import platform

if platform.system() == 'Windows':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
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
    print('Shutdown asyncgens done.')
    for t in asyncio.all_tasks(loop):
        try:
            t.cancel()
            loop.run_until_complete(t)
        except asyncio.CancelledError:
            pass
        except Exception as ex:
            print('Error:', ex, t)
    print("Cancelling tasks done.")
    try:
        loop.close()
    except RuntimeError:
        pass
    print('loop close')
