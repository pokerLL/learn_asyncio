import sys
sys.path.insert(0, '/Users/lei/workspace/program/asyncio-src/')

import mini_asyncio
import time
import random

async def hi(msg, sec):
    print(f"- - enter hi({msg}), {time.strftime('%H:%M:%S')}")
    await mini_asyncio.sleep(sec)
    print(f"- - exit  hi({msg}), {time.strftime('%H:%M:%S')}")
    return sec

async def main():
    print("main() begin")
    for i in range(1, 4):
        await hi(i, random.randint(1, 3))
        print(f"- main() end hi({i}) at {time.strftime('%H:%M:%S')}")
    print(f"main() end at {time.strftime('%H:%M:%S')}")

mini_asyncio.run(main())
print('done!')

"""
main() begin
- - enter hi(1), 16:35:52
- - exit  hi(1), 16:35:54
- main() end hi(1) at 16:35:54
- - enter hi(2), 16:35:54
- - exit  hi(2), 16:35:56
- main() end hi(2) at 16:35:56
- - enter hi(3), 16:35:56
- - exit  hi(3), 16:35:59
- main() end hi(3) at 16:35:59
main() end at 16:35:59
done!
"""