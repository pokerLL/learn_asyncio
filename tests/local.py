import multiprocessing
import os
import threading
import time
import random

_local = threading.local()


def task():
    print(f'当前线程名：{threading.current_thread().name}，'\
            f'当前进程名：{os.getpid()}，当前线程id：{threading.get_ident()}')
    _local.x = threading.current_thread().name
    time.sleep(random.randint(1,10))
    print(_local.x)
    time.sleep(random.randint(1,10))
    _local.x =  f"{threading.current_thread().name} - 1000"
    print(_local.x)



if __name__ == '__main__':
    tasks = []
    for i in range(10):
        t = threading.Thread(target=task)
        tasks.append(t)
        t.start()
    for t in tasks:
        t.join()
    print('main thread end.')

"""
当前线程名：Thread-1，当前进程名：5184，当前线程id：6111375360
当前线程名：Thread-2，当前进程名：5184，当前线程id：6128201728
当前线程名：Thread-3，当前进程名：5184，当前线程id：6145028096
当前线程名：Thread-4，当前进程名：5184，当前线程id：6161854464
当前线程名：Thread-5，当前进程名：5184，当前线程id：6178680832
当前线程名：Thread-6，当前进程名：5184，当前线程id：6195507200
当前线程名：Thread-7，当前进程名：5184，当前线程id：6212333568
当前线程名：Thread-8，当前进程名：5184，当前线程id：6229159936
当前线程名：Thread-9，当前进程名：5184，当前线程id：6245986304
当前线程名：Thread-10，当前进程名：5184，当前线程id：6262812672
Thread-4
Thread-9
Thread-4 - 1000
Thread-8
Thread-3
Thread-7
Thread-3 - 1000
Thread-8 - 1000
Thread-1
Thread-2
Thread-7 - 1000
Thread-2 - 1000
Thread-6
Thread-5
Thread-5 - 1000
Thread-10
Thread-9 - 1000
Thread-6 - 1000
Thread-10 - 1000
Thread-1 - 1000
"""