import sys
sys.path.insert(0, '/Users/lei/workspace/program/asyncio-src/')

import mini_asyncio

async def f():
    return 1

async def main():
    await f()


async def main2():
    task = mini_asyncio.create_task(f())
    await task


mini_asyncio.run(main2())

"""
>>> dis.dis(f)
  6           0 RETURN_GENERATOR
              2 POP_TOP
              4 RESUME                   0

  7           6 LOAD_CONST               1 (1)
              8 RETURN_VALUE

main:
>>> dis.dis(main)
  9           0 RETURN_GENERATOR
              2 POP_TOP
              4 RESUME                   0

 10           6 LOAD_GLOBAL              1 (NULL + f)
             18 PRECALL                  0
             22 CALL                     0
             32 GET_AWAITABLE            0
             34 LOAD_CONST               0 (None)
        >>   36 SEND                     3 (to 44)
             38 YIELD_VALUE
             40 RESUME                   3
             42 JUMP_BACKWARD_NO_INTERRUPT     4 (to 36)
        >>   44 POP_TOP
             46 LOAD_CONST               0 (None)
             48 RETURN_VALUE

             
main2:
>>> dis.dis(main2)
 13           0 RETURN_GENERATOR
              2 POP_TOP
              4 RESUME                   0

 14           6 LOAD_GLOBAL              1 (NULL + mini_asyncio)
             18 LOAD_ATTR                1 (create_task)
             28 LOAD_GLOBAL              5 (NULL + f)
             40 PRECALL                  0
             44 CALL                     0
             54 PRECALL                  1
             58 CALL                     1
             68 STORE_FAST               0 (task)

 15          70 LOAD_FAST                0 (task)
             72 GET_AWAITABLE            0
             74 LOAD_CONST               0 (None)
        >>   76 SEND                     3 (to 84)
             78 YIELD_VALUE
             80 RESUME                   3
             82 JUMP_BACKWARD_NO_INTERRUPT     4 (to 76)
        >>   84 POP_TOP
             86 LOAD_CONST               0 (None)
             88 RETURN_VALUE


"""