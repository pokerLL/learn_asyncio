import sys
sys.path.insert(0, '/Users/lei/workspace/program/asyncio-src/')

import mini_asyncio

# import asyncio as mini_asyncio

import time
import random

async def hi(msg, sec):
    print(f"enter hi({msg}, {sec}), {time.strftime('%H:%M:%S')}")
    await mini_asyncio.sleep(sec)
    print(f"exit  hi({msg}, {sec}), {time.strftime('%H:%M:%S')}")
    return f'{msg}-{sec}'

async def main():
    print(f"main() begin at {time.strftime('%H:%M:%S')}")
    tasks = []
    for i in range(1, 5):
        t = mini_asyncio.create_task(hi(i, random.randint(1, 3))) # 四个task会被创建并在创建时扔到_ready队列中
                                                        # 实际被加到_ready中的是Handle类包裹的task的_step方法
        tasks.append(t)
    
    for t in tasks:
        print(f"main await at {time.strftime('%H:%M:%S')}")
        b = await t
        print(f"b is: {b}")
    
    print(f"main() end at {time.strftime('%H:%M:%S')}")

mini_asyncio.run(main())

"""
注意:
    1. exit 1 后并没有立马 print b 因为只是sleep结束只是向_ready中加了一个wakeup任务 
        - wakeup任务会在下次run_once的时候被执行, 实际执行的就是真正的callback
    同理还有select触发后 也只是把calllback加入_ready中
    或者依赖的任务结束后 也仅仅是把callback加入_ready中
    只有在下次run_once的时候 才会真正的执行callback
这样做而不是直接运行callback的原因:
    1. 所有任务都有自己的上下文 不可以在当前环境下运行
    2. 公平调度问题: 如果某个任务的callback很多或很深 那么其他任务就会被饿死-尤其是那些已经准备好的任务

# 忽略注释, 可能有错误
# await 后面的是一个协程对象时:
#     1. 直接send(None) 直到其自己结束或者因为await放出控制权
#     2. 注意, 此时main()函数并没有结束, 而是在等待hi()函数结束,并没有放出控制权
#
# await 后面是一个task对象时:
#     1. 交出控制权
#     2. 把自己设为task的callback     # 这里对应的代码还没有找到
# 这两者dis的结果都是一致的, GET_AWAITABLE 和 YIELD_FROM 因此说明其背后逻辑是一致的

这一段作为一个补充,了解即可,不要当真:
    await 实际是 yield from 的语法糖, 仅仅是作为外部调用和内部调用的桥梁-做一个中转
        当外部向自己send值时, 会把值传给yield from后面的对象
        当内部yield from后面的对象yield值, 会把值传给外部调用者

因此当当前协程一个对象时,实际是调用其__await__方法, 但是future的__await__方法调用时只要还没有done都是直接yield self, 
    然后yield的值因为yield from的存在也会直接yield出去, 当前协程就此失去控制权
    当yield出去的是一个future,当前协程被阻塞, 在__step中就会把自己的wakeup设为future的callback,并将这个future加入到_ready中
    并且在这之后会在yield_from字节码中将当前协程的last_fi向前调一个位置, 意思是下次执行当前协程时还是从await的位置开始执行 会再执行一次awiit "something"
    当当前协程被唤醒(__wakeup)时, 会继续执行__step, 会执行到yield from的位置, 会把yield出去的future的result或exception传递出去

    如果当前协程自己也是一个future, 当自己结束时首先会设置自己的result和执行状态, 然后把自己的callback一个个加入到_ready中-call_soon

"""


"""

main() begin at 19:56:22
main await at 19:56:22
enter hi(1, 2), 19:56:22
enter hi(2, 2), 19:56:22
enter hi(3, 3), 19:56:22
enter hi(4, 1), 19:56:22
exit  hi(4, 1), 19:56:23
exit  hi(1, 2), 19:56:24   
exit  hi(2, 2), 19:56:24
b is: 1-2
main await at 19:56:24
b is: 2-2
main await at 19:56:24
exit  hi(3, 3), 19:56:25
b is: 3-3
main await at 19:56:25
b is: 4-1
main() end at 19:56:25
"""