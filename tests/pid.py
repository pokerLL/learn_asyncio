import multiprocessing
import os
import threading
import time
import random

_local = threading.local()


def task():
    """
    Return a non-zero integer that uniquely identifies the current thread amongst other threads that exist simultaneously. This may be used to identify per-thread resources. Even though on some platforms threads identities may appear to be allocated consecutive numbers starting at 1, this behavior should not be relied upon, and the number should be seen purely as a magic cookie. A thread's identity may be reused for another thread after it exits.
    需要注意threading.get_ident()的返回值仅仅保证在当前线程的生命周期内是唯一的，不同线程之间的get_ident()可能会返回相同的值。
        - 例如删除了一个线程，然后又创建了一个新的线程，新线程的get_ident()可能会返回被删除线程的get_ident()。 
            -> 直接删掉下面除第一个print之外的语句,会发现很多线程的get_ident()都是一样的。
    """
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
"""