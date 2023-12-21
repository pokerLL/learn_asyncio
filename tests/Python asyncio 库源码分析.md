# Python asyncio 库源码分析

## 原文

* [https://www.cnblogs.com/hanabi-cnblogs/p/17494522.html](https://www.cnblogs.com/hanabi-cnblogs/p/17494522.html)

‍

## 前言

本着 「路漫漫其修远兮, 吾将上下而求索」 的精神。终于要开始深入研究 Python 中 asyncio 的源码实现啦。

本文章可能篇幅较长，因为是逐行分析 asyncio 的实现，也需要读者具有一定的 asyncio 编码经验和功底，推荐刚开始踏上 Python 异步编程之旅的朋友们可以先从官方文档入手，由浅入深步步为营。

若在读的你对此感兴趣，那么很开心能与你分享我的学习成果。

本次源码分析将在 Python 3.11.3 的版本上进行探索。

> PS: 笔者功力有限，若有不足之处还望及时指正，因为是逐行分析所以过程稍显枯燥。  
> 更建议屏幕前的你打开 source code 跟随整篇文章花费一定的时间一起研究，尽信书不如无书，对此文持以质疑的态度去阅读将有更大的收获。

‍

## 全局代码

在 Python 中，当一个模块被导入时，Python 解释器会执行该模块中的全局代码。

而全局代码则是指在模块中未被封装在函数或类中的代码，它们会在模块被导入时率先执行。

这意味着全局代码可以包括变量的初始化、函数的定义、类的定义、条件语句、循环等。这些代码在模块被导入时执行，用于设置模块的初始状态或执行一些必要的操作。

查看源码时，一定不要忽略全局代码。

> PS: 一个小技巧，查看全局代码最好的办法就是将所有的 fold 都先收起来，vim 中使用 zM 快捷键即可。

‍

### 导入模块

研究任何一个模块，我们需先从 import 开始，因为那里的代码会率先执行：

```python
import asyncio
```

点进 asyncio 模块之后，可以发现它的入口文件 __init__ 篇幅是较为简短的：

```python
import sys

from .base_events import *
from .coroutines import *
from .events import *
from .exceptions import *
from .futures import *
from .locks import *
from .protocols import *
from .runners import *
from .queues import *
from .streams import *
from .subprocess import *
from .tasks import *
from .taskgroups import *       # 没有被放到 __all__ 中
from .timeouts import *
from .threads import *
from .transports import *

# __all__ 指的是 from asyncio import *
# 时 * 所包含的资源
__all__ = (base_events.__all__ +
           coroutines.__all__ +
           events.__all__ +
           exceptions.__all__ +
           futures.__all__ +
           locks.__all__ +
           protocols.__all__ +
           runners.__all__ +
           queues.__all__ +
           streams.__all__ +
           subprocess.__all__ +
           tasks.__all__ +
           threads.__all__ +
           timeouts.__all__ +
           transports.__all__)

# 添加所在平台的IO复用实现
# 若是 win32 平台, 则添加 windows_events 中的 __all__
if sys.platform == 'win32':
    from .windows_events import *
    __all__ += windows_events.__all__
# 若是 unix 平台, 则添加 unix_events 中的 __all__
else:
    from .unix_events import *
    __all__ += unix_events.__all__
```

### base_events

base_events 是在 asyncio 入口文件中第一个被 import 的模块，提供了一些基本的类和设置项，如 BaseEventLoop 以及 Server 等等 ...

base_events 中全局执行的代码不多，以下是其导入的 build-in package:

```python
import collections
import collections.abc
import concurrent.futures
import functools
import heapq
import itertools
import os
import socket
import stat
import subprocess
import threading
import time
import traceback
import sys
import warnings
import weakref
try:
    import ssl
except ImportError:  # pragma: no cover
    ssl = None
```

自定义的 package：

```python
from . import constants
from . import coroutines
from . import events
from . import exceptions
from . import futures
from . import protocols
from . import sslproto
from . import staggered
from . import tasks
from . import transports
from . import trsock
from .log import logger
```

关注几个有用的信息点:

```python
# 该模块只允许通过 * 导入 BaseEventLoop 以及 Server 类
__all__ = 'BaseEventLoop','Server',


# 定义异步事件循环中允许的最小计划定时器句柄数
# loop.call_later() 以及 loop.call_at() 都是在创建定时器句柄
# 当计划定时器句柄的数量低于该值，事件循环可能会采取一些优化措施
# 例如减少时间片的分配或合并定时器句柄，以提高性能和效率
# 注意这个优化 在每一次事件循环的开始时都会进行判断
_MIN_SCHEDULED_TIMER_HANDLES = 100

# 定义了被取消的定时器句柄数量与总计划定时器句柄数量之间的最小比例
# 如果取消的定时器句柄数量超过了计划定时器句柄数量的这个比例
# 事件循环可能会采取一些优化措施，例如重新分配或重新排序定时器句柄列表，以提高性能和效率
# 同上 在每一次事件循环的开始时都会进行判断
_MIN_CANCELLED_TIMER_HANDLES_FRACTION = 0.5

# 一个布尔值, 用来判断当前 socket 是否支持 IPV6
_HAS_IPv6 = hasattr(socket, 'AF_INET6')

# 事件循环 SELECT 时的最长等待时间
MAXIMUM_SELECT_TIMEOUT = 24 * 3600
```

除此之外，还有关于 socket 部分的:

> Socket 的非延迟特性是指 TCP 协议中的一种设置，通常用于优化数据传输的效率。在网络通信中，TCP 使用 Nagle 算法来优化小数据包的传输，该算法会在发送数据时进行缓冲，等待数据充满缓冲区再统一发送，以减少网络中的小数据包数量，提高网络利用率。然而，对于某些实时性要求较高的应用程序（如实时游戏、视频流等），这种缓冲机制可能会引入延迟。
> 
> TCP_NODELAY 是一个 socket 选项，允许禁用 Nagle 算法，从而达到非延迟的效果。当设置 TCP_NODELAY 选项后，TCP 连接将不会等待数据填充满发送缓冲区，而是立即发送数据，从而降低传输延迟，提高实时性。
> 
> 给定的 Python 代码中，首先通过检查 socket 模块是否具有 TCP_NODELAY 这一属性来确定当前环境是否支持该非延迟特性。如果支持，就定义了一个名为 _set_nodelay 的函数，该函数通过 setsockopt 方法启用了 TCP_NODELAY 选项，从而禁用了 Nagle 算法。这个函数会应用于指定条件的 TCP 连接，以提高数据传输的实时性和效率。
> 
> 对于不支持 TCP_NODELAY 的情况，代码定义了一个什么也不做的 _set_nodelay 函数，以确保代码在不支持该选项的环境下不会引发错误。
> 
> 这段代码的主要目的是在可用时启用 TCP_NODELAY 选项，以实现非延迟特性，但在不支持该选项的情况下提供兼容性 - 不做任何操作，以确保代码不会引发错误。

```python
# 当前的 socket 模块是否具有非延迟特性
if hasattr(socket, 'TCP_NODELAY'):
    def _set_nodelay(sock):
        if (sock.family in {socket.AF_INET, socket.AF_INET6} and
                sock.type == socket.SOCK_STREAM and
                sock.proto == socket.IPPROTO_TCP):
            # 启用 tcp 协议非延迟特性，即禁用 Nagle 算法
            sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
else:
    def _set_nodelay(sock):
        pass
```

### constants

constants 是在 base_events 中第一个被 import 的。其作用是定义一些通过 asyncio 进行网络编程时的常量数据。

它的源码虽然简单但涉及知识面较广，基本是与网络编程相关的，若想深入研究还需下一阵苦功夫:

```python
import enum

# 在使用 asyncio 进行网络编程时
# 写入操作多次失败（如链接丢失的情况下）记录一条 warning 日志
LOG_THRESHOLD_FOR_CONNLOST_WRITES = 5

# 在使用 asyncio 进行网络编程时
# 若对方断联、则在重试 accept 之前等待的秒数
# 参见 selector_events._accept_connection() 具体实现
ACCEPT_RETRY_DELAY = 1

# 在 asyncio debug 模式下需捕获的堆栈条目数量（数量越大，运行越慢）
# 旨在方便的为开发人员追踪问题，例如找出事件循环中的协程或回调的调用路径
DEBUG_STACK_DEPTH = 10

# 在使用 asyncio 进行网络编程时
# SSL/TSL 加密通信握手时可能会产生断联或失败
# 而该常量是指等待 SSL 握手完成的秒数，他和 Nginx 的 timeout 匹配
SSL_HANDSHAKE_TIMEOUT = 60.0

# 在使用 asyncio 进行网络编程时
# 等待 SSL 关闭完成的秒数
# 如 asyncio.start_server() 方法以及 asyncio.start_tls() 方法
# 在链接关闭后，会使用 n 秒来进行确认对方已经成功关闭了链接
# 若在 n 秒内未得到确认，则引发 TimeoutError
SSL_SHUTDOWN_TIMEOUT = 30.0

# 在使用 loop.sendfile() 方法传输文件时
# 后备缓冲区的大小（有些文件系统不支持零拷贝，因此需要一个缓冲区）
SENDFILE_FALLBACK_READBUFFER_SIZE = 1024 * 256

# 当在 SSL/TSL 握手期间，若 read 的内核缓冲区数据大小
# 超过了下面设定的值，则会等待其内核缓冲区大小降低后
# 再次进行 read
FLOW_CONTROL_HIGH_WATER_SSL_READ = 256  # KiB

# 同上，只不过这个是写入的上限流量阈值
FLOW_CONTROL_HIGH_WATER_SSL_WRITE = 512  # KiB

class _SendfileMode(enum.Enum):
    UNSUPPORTED = enum.auto()
    TRY_NATIVE = enum.auto()
    FALLBACK = enum.auto()
```

### coroutines

coroutines 是在 base_events 中第二个被 import 的。其作用是提供一些布尔的判定接口，如判断对象是否是 coroutine、当前是否是 debug 模式等等。

其全局代码不多，暂可不必太过关注:

```python
# 该模块只允许通过 * 导入 iscoroutinefunction 以及 iscoroutine 函数
__all__ = 'iscoroutinefunction', 'iscoroutine'


# ...
_is_coroutine = object()

# 优先检查原生协程以加快速度
# asyncio.iscoroutine
_COROUTINE_TYPES = (types.CoroutineType, types.GeneratorType,
                    collections.abc.Coroutine)
_iscoroutine_typecache = set()
```

### events

events 是在 base_events 中第三个被 import 的。其作为是定义一些与事件循环相关的高级接口或定义一些事件循环的抽象基类供内部或开发者使用。

注意他在这里还 import 了自定义模块 format_helpers，但是 format_helpers 中并未有任何运行的全局代码，所以后面直接略过了：

```python
from . import format_helpers
```

以下是它的全局代码：

```python
# __all__ 中难免会看到一些熟悉的身影
# 比如 get_event_loop get_running_loop 等等
__all__ = (
    'AbstractEventLoopPolicy',
    'AbstractEventLoop', 'AbstractServer',
    'Handle', 'TimerHandle',
    'get_event_loop_policy', 'set_event_loop_policy',
    'get_event_loop', 'set_event_loop', 'new_event_loop',
    'get_child_watcher', 'set_child_watcher',
    '_set_running_loop', 'get_running_loop',
    '_get_running_loop',
)

# ...

# 该变量有 2 个作用
# 分别是决定如何创建和获取事件循环对象
#   - 比如一个线程一个事件循环
#   - 或者一个任务一个事件循环
# 再者就是获取事件循环，通过 get_event_loop_policy 方法即可拿到该变量
_event_loop_policy = None

# 一把线程锁、用于保护事件循环策略的实例化
_lock = threading.Lock()

# ...

class _RunningLoop(threading.local):
    loop_pid = (None, None)

# 这个好像是获取以及设置当前的 running loop，由 _get_running_loop 使用。
# 它将 loop 和 pid 进行绑定
_running_loop = _RunningLoop()

# 为了一些测试而取的以 _py 开始的别名
_py__get_running_loop = _get_running_loop
_py__set_running_loop = _set_running_loop
_py_get_running_loop = get_running_loop
_py_get_event_loop = get_event_loop
_py__get_event_loop = _get_event_loop


try:
    # 纯注释翻译:
    # get_event_loop() 是最常调用的方法之一
    # 异步函数。纯 Python 实现是
    # 大约比 C 加速慢 4 倍。
    # PS: C 语言的部分就先暂时不看了
    from _asyncio import (_get_running_loop, _set_running_loop,
                          get_running_loop, get_event_loop, _get_event_loop)
except ImportError:
    pass
else:
    # 为了一些测试而取的以 _c 开始的别名
    _c__get_running_loop = _get_running_loop
    _c__set_running_loop = _set_running_loop
    _c_get_running_loop = get_running_loop
    _c_get_event_loop = get_event_loop
    _c__get_event_loop = _get_event_loop
```

### exceptions

exceptions 是在 base_events 中第四个被 import 的。其主要作用是定义了一些异常类：

```python
__all__ = ('BrokenBarrierError',
           'CancelledError', 'InvalidStateError', 'TimeoutError',
           'IncompleteReadError', 'LimitOverrunError',
           'SendfileNotAvailableError')
```

有些异常类中实现了 __reduce__() 方法。该方法允许自定义对象在被序列化或持久化过程中的状态和重建方式。

示例：

```python
import pickle
from typing import Any


def ser_fn(name):
    return name


class Example:

    def __init__(self, name) -> None:
        self.name = name

    def __reduce__(self) -> str | tuple[Any, ...]:
        """
        反序列化时，将调用 ser_fn 并且传入参数
        下面注释的第一个例子是重新实例化一下
        第二个例子是更直观的演示该方法的作用
        """
        # return (__class__, (self.name, ))
        return (ser_fn, ("反序列化结果", ))


if __name__ == "__main__":
    obj = Example("instance")

    serializer = pickle.dumps(obj)
    deserializer = pickle.loads(serializer)

    print(deserializer)

# 反序列化结果
```

### futures

futures 是在 base_events 中第五个被 import 的。其作用是定义了 asyncio 中未来对象的实现方式。

在看其全局代码之前，首先推荐阅读官方文档：

[asyncio futures 介绍](https://docs.python.org/3/library/asyncio-future.html#future-object)

该 futures 和 collections 的 futures 有些许区别，futures 也算是 Python 异步编程中比较难以理解的一个点，后续有机会再和大家详细探讨。

futures 文件中导入了 base_futures 自定义模块，但 base_futures 中暂时没有值得关注的点，所以先在此略过：

```python
from . import base_futures

# 下面 3 个都已经粗略看过一次
from . import events
from . import exceptions
from . import format_helpers
```

其全局代码如下：

```python

# 一个函数，用于判断对象是否是一个未来对象
isfuture = base_futures.isfuture


# 用于表明未来对象的当前一些状态的标志
# 分别是 等待执行、取消执行、完成执行
_PENDING = base_futures._PENDING
_CANCELLED = base_futures._CANCELLED
_FINISHED = base_futures._FINISHED


# 栈的调试 LOG 级别
STACK_DEBUG = logging.DEBUG - 1  # heavy-duty debugging

# ...

class Future:
    pass

_PyFuture = Future


# ...
try:
    import _asyncio
except ImportError:
    pass
else:
    Future = _CFuture = _asyncio.Future
```

### protocols

protocols 是在 base_events 中第六个被 import 的。其作用主要是定义一些内部协议。

如 '缓冲区控制流协议'、'接口数据报协议'、'子进程调用接口协议' 等等。

暂先关注其 `__all__` 即可：

```python
__all__ = (
    'BaseProtocol', 'Protocol', 'DatagramProtocol',
    'SubprocessProtocol', 'BufferedProtocol',
)
```

### sslproto

sslproto 是在 base_events 中第七个被 import 的。其作用是定义和具体实现 SSL/TLS 协议。

同默认的 socket 模块不同，asyncio 所提供的流式传输是已经实现好了 SSL/TLS 协议功能的。

下面先对 SSL/TLS 做一个简短的介绍。

> SSL/TLS 是一个独立的协议，其功能主要用于网络通信的加密和安全，如数据加密、身份认证等等。  
> TLS 的前身为 SSL 协议，是 SSL 的现代版和改进版。

在 sslproto 中也导入了一些标准库以及自定义的模块：

```python
import collections
import enum
import warnings
try:
    import ssl
except ImportError:  # pragma: no cover
    ssl = None

# 自定义模块
from . import constants
from . import exceptions
from . import protocols

# 下面 2 个还没看过，transports 可以大概瞅瞅，但 log 没必要看
# 他本质就是使用 logging 模块获得一个 log 对象
# 名字就是当前的 package name，即为 asyncio
from . import transports
from .log import logger
```

其全局代码如下：

```python

# ...
if ssl is not None:
    SSLAgainErrors = (ssl.SSLWantReadError, ssl.SSLSyscallError)
```

除此之外，它还定义了一些类，如 'SSL 协议'、'应用协议状态' 等等，这里不做细述。

### transports

transports 在 sslproto 文件中被导入，主要定义一些传输类。

如 '读传输'、'写传输'、'数据报传输'、'子进程接口传输' 等等，和 protocols 中的协议类关系较为密切。

**一般来说若要基于 asyncio 进行二次开发，如开发 http 协议的 web 服务程序等等，就需要关注到这里。**

> 例如aiohhttp

其下很多代码看不到具体实现，直接看其 `__all__` 变量吧：

```python
__all__ = (
    'BaseTransport', 'ReadTransport', 'WriteTransport',
    'Transport', 'DatagramTransport', 'SubprocessTransport',
)
```

### staggered

staggered 是在 base_events 中第八个被 import 的。其作用是如何支持正在运行的协程在时间点中错开（主要针对 socket 网络编程）。

他实现了一个协程函数 staggered_race 以及导入了一些内部或自定义模块：

```python

__all__ = 'staggered_race',

import contextlib
import typing

from . import events
from . import exceptions as exceptions_mod

from . import locks
from . import tasks

async def staggered_race(...):
    pass
```

### locks

locks 在 staggered 中被导入，其作用是实现了一些协程锁。

官方文档：[协程同步](https://docs.python.org/3/library/asyncio-sync.html)

具体有 '同步锁'、'事件锁'、'条件锁'、'信号量锁'、'有界信号量锁'、'屏障锁'。相比于 threading 少了 '递归锁' 和一些其他的锁。

```python
__all__ = ('Lock', 'Event', 'Condition', 'Semaphore',
           'BoundedSemaphore', 'Barrier')
```

### mixins

mixins 在 locks 中被导入，其作用是提供一些工具集功能。

代码量较少：

```python
import threading
from . import events

# 实现一把全局的线程同步锁
_global_lock = threading.Lock()

class _LoopBoundMixin:
    _loop = None

    def _get_loop(self):
        loop = events._get_running_loop()

        if self._loop is None:
            with _global_lock:
                if self._loop is None:
                    self._loop = loop
        if loop is not self._loop:
            raise RuntimeError(f'{self!r} is bound to a different event loop')
        return loop
```

### tasks

tasks 在 locks 中被导入，其作用是定义 Task 对象、提供一些管理 Task 对象的**高级接口**。

```python

# 有很多熟悉的高级接口，均来自于 tasks 模块
__all__ = (
    'Task', 'create_task',
    'FIRST_COMPLETED', 'FIRST_EXCEPTION', 'ALL_COMPLETED',
    'wait', 'wait_for', 'as_completed', 'sleep',
    'gather', 'shield', 'ensure_future', 'run_coroutine_threadsafe',
    'current_task', 'all_tasks',
    '_register_task', '_unregister_task', '_enter_task', '_leave_task',
)
```

下面是它导入的内置模块和第三方模块：

```python
import concurrent.futures
import contextvars
import functools
import inspect
import itertools
import types
import warnings
import weakref
from types import GenericAlias

# 除了 base_tasks 其他都已经全部 load 掉了
from . import base_tasks
from . import coroutines
from . import events
from . import exceptions
from . import futures
from .coroutines import _is_coroutine
```

其全局代码有：

```python
# 生成新的 task 时的命名计数器
# 这里不采用 +=1 的操作是因为协程并非线程安全
# 通过迭代器不断的向后计数，可以完美的保证线程安全（Ps: GET 新技能）
_task_name_counter = itertools.count(1).__next__

# ...

_PyTask = Task


FIRST_COMPLETED = concurrent.futures.FIRST_COMPLETED
FIRST_EXCEPTION = concurrent.futures.FIRST_EXCEPTION
ALL_COMPLETED = concurrent.futures.ALL_COMPLETED


# 包含所有正在活动的任务
_all_tasks = weakref.WeakSet()

# 一个字典，包含当前正在活动的任务 {loop: task}
_current_tasks = {}

# ...

_py_register_task = _register_task
_py_unregister_task = _unregister_task
_py_enter_task = _enter_task
_py_leave_task = _leave_task


try:
    from _asyncio import (_register_task, _unregister_task,
                          _enter_task, _leave_task,
                          _all_tasks, _current_tasks)
except ImportError:
    pass
else:
    _c_register_task = _register_task
    _c_unregister_task = _unregister_task
    _c_enter_task = _enter_task
    _c_leave_task = _leave_task
```

### trsock

trsock 是在 base_events 中第九个被 import 的。其作用是实现了一个 '传输套接字' 的类。

具体是对模块内的，暂不深究。

### runners

runners 是在 asyncio 入口文件中第八个被 import 的。

其作用为**定义 asyncio 的入口方法 run** 以及定义管理事件循环声明周期类的 'Runner'。

```python
__all__ = ('Runner', 'run')
```

Runner 功能为 Python 3.11 新功能。

### queues

queues 是在 asyncio 入口文件中第九个被 import 的。其作用是定义一些用于协程信息同步的队列。

```python
__all__ = ('Queue', 'PriorityQueue', 'LifoQueue', 'QueueFull', 'QueueEmpty')
```

### streams

streams 是在 asyncio 入口文件中第十个被 import 的。其作用是定义流式传输相关的具体实现类，如 '可读流'、'可写流' 等等。

```python
__all__ = (
    'StreamReader', 'StreamWriter', 'StreamReaderProtocol',
    'open_connection', 'start_server')
```

如果是在 Unix 平台下，则 `__all__` 会新增一些内容：

```python
if hasattr(socket, 'AF_UNIX'):
    __all__ += ('open_unix_connection', 'start_unix_server')

# 读写流操作的缓冲区大小为 64kb
_DEFAULT_LIMIT = 2 ** 16
```

该文件与 transports 关系较为密切。

### subprocess

subprocess 是在 asyncio 入口文件中第十一个被 import 的。其作用是定义子进程通信相关的类，如 'SubprocessProtocol' 和 'Protocol' 等等。

```python
__all__ = 'create_subprocess_exec', 'create_subprocess_shell'

# ...

PIPE = subprocess.PIPE
STDOUT = subprocess.STDOUT
DEVNULL = subprocess.DEVNULL
```

### taskgroups

taskgroups 是在 asyncio 入口文件中中第十二个被 import 的。其作用是定义了任务组。

```python
__all__ = ["TaskGroup"]
```

此功能为 Python 3.11 新功能。

### timeouts

timeouts 是在 asyncio 入口文件中中第十三个被 import 的。其作用是定义了超时相关的类和函数。

```python
__all__ = (
    "Timeout",
    "timeout",
    "timeout_at",
)


class _State(enum.Enum):
    CREATED = "created"
    ENTERED = "active"
    EXPIRING = "expiring"
    EXPIRED = "expired"
    EXITED = "finished"
```

### threads

threads 是在 asyncio 入口文件中第十四个被 import 的。其作用是定义了函数 to_thread。

```python
__all__ = "to_thread",


async def to_thread(func, /, *args, **kwargs):
    pass
```

### 模块导入关系图

整个 asyncio 模块的初始化模块导入关系图如下：

​![](assets/net-img-asyncio%20源码导入关系图(1)-20231107115038-s1z9xlg.png)​

## 由 asyncio.run 引发的故事

asyncio.run() 作为目前 Python 较为推崇的协程起始方式。研究其内部启动顺序及执行顺序是十分有必要的。

在 Python 3.11 版本后 asyncio 新增了多种协程起始方式，但 asyncio.run 的地位依旧不容置疑。

如果后续有机会，我们可以再继续探讨研究 Python 3.7 之前的协程起始方式。

### 事件循环的初始化过程

#### 函数基本介绍

asyncio.run() 位于 asyncio.runners 文件中，其函数签名如下：

```python
def run(main, *, debug=None):
    pass
```

如同官方文档所说，该方法如果在没有 Runner 参与的情况下，应当只调用一次。

在 Python 3.11 版本后，新加入的 Runner 类使其源码发生了一定的变化，但其内部逻辑总是万变不离其宗的。

```python
def run(main, *, debug=None):
    # 若当前的线程已经存在一个正在运行的事件循环、则抛出异常
    if events._get_running_loop() is not None:
        raise RuntimeError(
            "asyncio.run() cannot be called from a running event loop")

    with Runner(debug=debug) as runner:
        return runner.run(main)
```

#### _get_running_loop

源码如下：

```python
# ...
class _RunningLoop(threading.local):
    loop_pid = (None, None)

# ...
_running_loop = _RunningLoop()

# ...
def _get_running_loop():
    running_loop, pid = _running_loop.loop_pid
    # 这里条件不满足，所以返回的必然是 None
    if running_loop is not None and pid == os.getpid():
        return running_loop
```

对于了解过 threading.local 源代码的同学这里应该比较好理解。

> Ps: threading.local 所实现的功能是让每一个线程能够存储自己独有的数据，其原理大致是维护一个 global dict，其结构为 { thread_id: {} }，然后对其__getitem__方法做魔改, 每个线程去获取数据时实际都是从 dict[thread_id] 中获取

#### Runner 类

继续回到 asyncio.run() 函数中，可以发现它 with 了 Runner 类：

```python
def run(main, *, debug=None):
    # ...
    with Runner(debug=debug) as runner:
        return runner.run(main)
```

先看 Runner 的 `__init__` 方法，再看其 `__enter__` 方法。

```python
class _State(enum.Enum):
    CREATED = "created"
    INITIALIZED = "initialized"
    CLOSED = "closed"

class Runner:
    def __init__(self, *, debug=None, loop_factory=None):
        self._state = _State.CREATED
        self._debug = debug
        self._loop_factory = loop_factory
        self._loop = None
        self._context = None
        self._interrupt_count = 0
        self._set_event_loop = False

    def __enter__(self):
        self._lazy_init()
        return self

    def _lazy_init(self):
        # 如果是关闭状态，则抛出异常
        if self._state is _State.CLOSED:
            raise RuntimeError("Runner is closed")
        # 如果是初始化状态，则返回
        if self._state is _State.INITIALIZED:
            return
        # 如果 loop 工厂函数是 None
        if self._loop_factory is None:
            # 创建一个新的 loop
            self._loop = events.new_event_loop()
            if not self._set_event_loop:
                events.set_event_loop(self._loop)
                self._set_event_loop = True
        else:
            self._loop = self._loop_factory()

        if self._debug is not None:
            self._loop.set_debug(self._debug)

        self._context = contextvars.copy_context()
        self._state = _State.INITIALIZED
```

#### events.new_event_loop

events.new_event_loop 的源码如下，他通过拿到当前事件循环策略来得到一个新的事件循环：

```python

# ...
_event_loop_policy = None
_lock = threading.Lock()

# ...
def new_event_loop():
    return get_event_loop_policy().new_event_loop()

# ...
def get_event_loop_policy():
    if _event_loop_policy is None:
        _init_event_loop_policy()
    return _event_loop_policy

# ...
def _init_event_loop_policy():
    global _event_loop_policy
    # 思考点:
    #  这里为何要加线程锁？
    #  是为了避免多线程多事件循环状态下 _event_loop_policy 的
    #  数据同步问题吗？防止同时多次运行 DefaultEventLoopPolicy 实例化吗？
    with _lock:
        if _event_loop_policy is None:
            from . import DefaultEventLoopPolicy
            _event_loop_policy = DefaultEventLoopPolicy()
```

#### _UnixDefaultEventLoopPolicy

接下来我们要继续看 DefaultEventLoopPolicy 的代码实现，它位于 unix_events 文件中。

```python
class BaseDefaultEventLoopPolicy(AbstractEventLoopPolicy):

    _loop_factory = None

    class _Local(threading.local):
        _loop = None
        _set_called = False

    def __init__(self):
        # 2. 为当前线程生成了一个独立的 threading location
        self._local = self._Local()

    def new_event_loop(self):
        # 3. 实例化 _UnixSelectorEventLoop
        return self._loop_factory()

class _UnixDefaultEventLoopPolicy(events.BaseDefaultEventLoopPolicy):
    _loop_factory = _UnixSelectorEventLoop

    # 1. 初始化类
    def __init__(self):
        super().__init__()
        self._watcher = None

DefaultEventLoopPolicy = _UnixDefaultEventLoopPolicy
```

#### _UnixSelectorEventLoop

继续看 _UnixSelectorEventLoop 的实例化过程：

```python

# ---- coroutines ----

def _is_debug_mode():
    return sys.flags.dev_mode or (not sys.flags.ignore_environment and
                                  bool(os.environ.get('PYTHONASYNCIODEBUG')))

# ---- base_events ----

class BaseEventLoop(events.AbstractEventLoop):
    def __init__(self):
        # 3. 实例化对象字典填充
        self._timer_cancelled_count = 0
        self._closed = False
        self._stopping = False
        # deque 双端队列
        self._ready = collections.deque()
        self._scheduled = []
        # 默认执行器
        self._default_executor = None
        self._internal_fds = 0
        self._thread_id = None
        # 1e-09
        self._clock_resolution = time.get_clock_info('monotonic').resolution
        # 默认异常处理程序
        self._exception_handler = None
        self.set_debug(coroutines._is_debug_mode())
        self.slow_callback_duration = 0.1
        self._current_handle = None
        self._task_factory = None
        self._coroutine_origin_tracking_enabled = False
        self._coroutine_origin_tracking_saved_depth = None

        self._asyncgens = weakref.WeakSet()
        self._asyncgens_shutdown_called = False
        self._executor_shutdown_called = False

# ---- selector_events ----

class BaseSelectorEventLoop(base_events.BaseEventLoop):
    def __init__(self, selector=None):
        # 2. 继续调用父类 __init__ 方法，填充实例化对象的 __dict__ 字典
        super().__init__()
        # 3. 判断 selector 是否为 None
        if selector is None:
            # 得到一个默认的 io 复用选择器
            # select poll epoll
            selector = selectors.DefaultSelector()
        logger.debug('Using selector: %s', selector.__class__.__name__)
        self._selector = selector
        # 4. 调用 _make_self_pipe 方法
        self._make_self_pipe()
        # 10. 通过 weakref 创建出 1 个弱引用映射类
        self._transports = weakref.WeakValueDictionary()


    def _make_self_pipe(self):
        # 5. 创建 1 个非阻塞的 socket 对象
        self._ssock, self._csock = socket.socketpair()
        self._ssock.setblocking(False)
        self._csock.setblocking(False)
        self._internal_fds += 1
        # 6. 调用 address，传入当前 sock 对象的文件描述符
        self._add_reader(self._ssock.fileno(), self._read_from_self)


    def _add_reader(self, fd, callback, *args):
        # 7. 检查当前类是否是关闭状态
        self._check_closed()
        # 9. 实例化注册一个 handle，注意这里的 callback 是
        # self._read_from_self, args 为 ()
        handle = events.Handle(callback, args, self, None)
        try:
            # 第一次运行这里会报错,返回当前文件对象注册的 SelectorKey
            key = self._selector.get_key(fd)
        except KeyError:
            # 若报错则注册一个读事件，将 handle 放入
            self._selector.register(fd, selectors.EVENT_READ,
                                    (handle, None))
        else:
            # 如果是第二次运行这个方法，则拿到 event
            # 疑问点（register 时放入的是 handle 和 None）
            # 为何出来就成了可读流和可写流？其实是事件循环开启后的一系列处理
            # 可参照 事件循环的 sele._selector.select 以及 BaseSelectorEventLoop._process_events() 方法
            # 结果中的 reader 表示可读流的事件处理器对象，而 writer 为 None
            mask, (reader, writer) = key.events, key.data
            # 修改 fd 的注册事件
            # select 中 1 是读事件，2 是写事件。按位或后的结果总是较大值
            # 或两者的和
            self._selector.modify(fd, mask | selectors.EVENT_READ,
                                  (handle, writer))
            # 如果没有可读流，则关闭，说明 except 那里没有注册好 handle 或者被 unregister 掉了
            if reader is not None:
                reader.cancel()
        return handle

    def _check_closed(self):
        # 8. 若是关闭状态则直接抛出异常
        if self._closed:
            raise RuntimeError('Event loop is closed')


# ---- unix_events ----

class _UnixSelectorEventLoop(selector_events.BaseSelectorEventLoop):
    def __init__(self, selector=None):
        # 1. 调用父类进行实例化数据填充，构建 __dict__ 字典
        super().__init__(selector)
        self._signal_handlers = {}
```

#### events.Handle

events.Handle 类的源码如下，这个 Handle 类是 asyncio 中各类任务的上层封装，十分重要：

```python

# handle = events.Handle(callback, args, self, None)
# callback = BaseSelectorEventLoop._read_from_self
# self = _UnixSelectorEventLoop instance

class Handle:
    __slots__ = ('_callback', '_args', '_cancelled', '_loop',
                 '_source_traceback', '_repr', '__weakref__',
                 '_context')

    def __init__(self, callback, args, loop, context=None):
        # 若当前上下文为空，则 copy 当前上下文
        if context is None:
            context = contextvars.copy_context()
        self._context = context
        # loop 就是 _UnixSelectorEventLoop 的实例化对象
        self._loop = loop
        self._callback = callback
        # ()
        self._args = args
        self._cancelled = False
        self._repr = None
        # 先不看 debug 模式
        if self._loop.get_debug():
            self._source_traceback = format_helpers.extract_stack(
                sys._getframe(1))
        else:
            self._source_traceback = None
```

#### event.set_event_loop

至此，_loop_factory 已经全部走完了。实际上也没干太特别的事情，就创建了一个 DefaultSelector 以及实例化了一个 socket 对象并注册进了 DefaultSelector 中。

我们要接着看 Runner：

```python
class _State(enum.Enum):
    CREATED = "created"
    INITIALIZED = "initialized"
    CLOSED = "closed"

class Runner:
    def __init__(self, *, debug=None, loop_factory=None):
        self._state = _State.CREATED
        self._debug = debug
        self._loop_factory = loop_factory
        self._loop = None
        self._context = None
        self._interrupt_count = 0
        self._set_event_loop = False

    def __enter__(self):
        self._lazy_init()
        return self

    def _lazy_init(self):
        # 如果是关闭状态，则抛出异常
        if self._state is _State.CLOSED:
            raise RuntimeError("Runner is closed")
        # 如果是初始化状态，则返回
        if self._state is _State.INITIALIZED:
            return
        # 如果 loop 工厂函数是 None
        if self._loop_factory is None:
            # 创建一个新的 loop，这里的返回对象就是 _UnixSelectorEventLoop 的实例化对象
            self._loop = events.new_event_loop()
            if not self._set_event_loop:
                events.set_event_loop(self._loop)
                self._set_event_loop = True
        else:
            self._loop = self._loop_factory()

        if self._debug is not None:
            self._loop.set_debug(self._debug)

        self._context = contextvars.copy_context()
        self._state = _State.INITIALIZED
```

events.set_event_loop 源码：

```python
def get_event_loop_policy():
    if _event_loop_policy is None:
        _init_event_loop_policy()
    # 1. 应该走这里，实际上 _event_loop_policy 就是 _UnixDefaultEventLoopPolicy 的实例对象
    return _event_loop_policy

def set_event_loop(loop):
    # 2. 运行 _UnixDefaultEventLoopPolicy 实例对象的 set_event_loop
    get_event_loop_policy().set_event_loop(loop)
```

_UnixDefaultEventLoopPolicy 的 set_event_loop 方法：

```python
# ---- events ----

class BaseDefaultEventLoopPolicy(AbstractEventLoopPolicy):
    _loop_factory = None

    class _Local(threading.local):
        _loop = None
        _set_called = False

    def __init__(self):
        self._local = self._Local()

    def set_event_loop(self, loop):
        # 2. 通过 threading lock 设置标志位置
        self._local._set_called = True
        if loop is not None and not isinstance(loop, AbstractEventLoop):
            raise TypeError(f"loop must be an instance of AbstractEventLoop or None, not '{type(loop).__name__}'")
        self._local._loop = loop

# ---- unix_events ----

class _UnixDefaultEventLoopPolicy(events.BaseDefaultEventLoopPolicy):
    _loop_factory = _UnixSelectorEventLoop

    # ...
    def set_event_loop(self, loop):
        # 这个 loop 是 _UnixSelectorEventLoop 的实例化对象

        # 1. super 父类的同名方法
        super().set_event_loop(loop)

        # 3. 实例化的时候这里的_watcher是 None, 不会运行下面的条件
        if (self._watcher is not None and
                threading.current_thread() is threading.main_thread()):
            self._watcher.attach_loop(loop)
```

至此 Runner._lazy_init 应该全部走完了：

```python
class _State(enum.Enum):
    CREATED = "created"
    INITIALIZED = "initialized"
    CLOSED = "closed"

class Runner:
    def __init__(self, *, debug=None, loop_factory=None):
        self._state = _State.CREATED
        self._debug = debug
        self._loop_factory = loop_factory
        self._loop = None
        self._context = None
        self._interrupt_count = 0
        self._set_event_loop = False

    def __enter__(self):
        self._lazy_init()
        return self

    def _lazy_init(self):
        # 如果是关闭状态，则抛出异常
        if self._state is _State.CLOSED:
            raise RuntimeError("Runner is closed")
        # 如果是初始化状态，则返回
        if self._state is _State.INITIALIZED:
            return

        # 如果 loop 工厂函数是 None
        if self._loop_factory is None:
            # 创建一个新的 loop，这里的返回对象就是 _UnixSelectorEventLoop 的实例化对象
            self._loop = events.new_event_loop()
            # 设置新的标志位，代表事件循环已经初始化成功
            if not self._set_event_loop:
                events.set_event_loop(self._loop)
                self._set_event_loop = True

        # 不会走这里
        else:
            self._loop = self._loop_factory()

        if self._debug is not None:
            self._loop.set_debug(self._debug)


        # copy 当前上下文
        self._context = contextvars.copy_context()
        # 修改状态
        self._state = _State.INITIALIZED
```

注意，此时事件循环已经初始化完成了，但还没有正式启动。

#### 事件循环初始化流程图

以下是事件循环的初始化流程图：

​![](assets/net-img-未命名文件(2)-20231107115039-g9sj5is.png)​

### 事件循环的启动和任务的执行

在上面我们大概看了一下事件循环的初始化。接下来应该走到 runner.run() 方法中看他如何运行事件循环。

```python
def run(main, *, debug=None):
    # ...
    with Runner(debug=debug) as runner:
        return runner.run(main)
```

#### runner.run

源代码如下：

```python

class _RunningLoop(threading.local):
    loop_pid = (None, None)

# ...
_running_loop = _RunningLoop()

# ...
def _get_running_loop():
    running_loop, pid = _running_loop.loop_pid
    if running_loop is not None and pid == os.getpid():
        return running_loop

# -------------

class Runner:
    def __init__(self, *, debug=None, loop_factory=None):
        self._state = _State.CREATED # INITIALIZED
        self._debug = debug
        self._loop_factory = loop_factory  # _UnixSelectorEventLoop 实例对象
        self._loop = None
        self._context = None          # dict
        self._interrupt_count = 0
        self._set_event_loop = False  # True

    def _lazy_init(self):
        if self._state is _State.CLOSED:
            raise RuntimeError("Runner is closed")

        # 2. 直接返回
        if self._state is _State.INITIALIZED:
            return

        # ...

    def run(self, coro, *, context=None):

        # 若不是一个协程函数，则抛出异常
        if not coroutines.iscoroutine(coro):
            raise ValueError("a coroutine was expected, got {!r}".format(coro))

        # 若 event loop 已经运行了，则抛出异常
        # 这里还没有运行
        if events._get_running_loop() is not None:
            raise RuntimeError(
                "Runner.run() cannot be called from a running event loop")

        # 1. 运行 _lazy_init
        self._lazy_init()

        # 3. 不是 None
        if context is None:
            context = self._context

        # 4. 创建协程并发任务
        task = self._loop.create_task(coro, context=context)


        # .. 后面再看
        if (threading.current_thread() is threading.main_thread()
            and signal.getsignal(signal.SIGINT) is signal.default_int_handler
        ):
            sigint_handler = functools.partial(self._on_sigint, main_task=task)
            try:
                signal.signal(signal.SIGINT, sigint_handler)
            except ValueError:
                sigint_handler = None
        else:
            sigint_handler = None

        self._interrupt_count = 0
        try:
            return self._loop.run_until_complete(task)
        except exceptions.CancelledError:
            if self._interrupt_count > 0:
                uncancel = getattr(task, "uncancel", None)
                if uncancel is not None and uncancel() == 0:
                    raise KeyboardInterrupt()
            raise  # CancelledError
        finally:
            if (sigint_handler is not None
                and signal.getsignal(signal.SIGINT) is sigint_handler
            ):
                signal.signal(signal.SIGINT, signal.default_int_handler)
```

#### self._loop.create_task

_UnixSelectorEventLoop 和其父类 BaseSelectorEventLoop 本身没有实现 create_task() 方法，是在其超类 BaseEventLoop 所实现。

BaseEventLoop.create_task() 实际上就是 asyncio.create_task() 方法的底层。

```python

class BaseEventLoop(events.AbstractEventLoop):

    def __init__(self):
        self._timer_cancelled_count = 0
        self._closed = False
        self._stopping = False
        self._ready = collections.deque()
        self._scheduled = []
        self._default_executor = None
        self._internal_fds = 0
        self._thread_id = None
        self._clock_resolution = time.get_clock_info('monotonic').resolution
        self._exception_handler = None
        self.set_debug(coroutines._is_debug_mode())
        self.slow_callback_duration = 0.1
        self._current_handle = None
        self._task_factory = None
        self._coroutine_origin_tracking_enabled = False
        self._coroutine_origin_tracking_saved_depth = None

        self._asyncgens = weakref.WeakSet()
        self._asyncgens_shutdown_called = False
        self._executor_shutdown_called = False

    def create_task(self, coro, *, name=None, context=None):
        """Schedule a coroutine object.

        Return a task object.
        """
        # 先检查是否关闭，返回的结果必定是 False
        self._check_closed()

        # 任务工厂为 None
        if self._task_factory is None:
            task = tasks.Task(coro, loop=self, name=name, context=context)
            if task._source_traceback:
                del task._source_traceback[-1]

        # 若通过 asyncio.get_running_loop().set_task_factory() 设置了任务工厂函数的话
        # 那么就运行 else 的代码块
        else:
            if context is None:
                # Use legacy API if context is not needed
                task = self._task_factory(self, coro)
            else:
                task = self._task_factory(self, coro, context=context)

            tasks._set_task_name(task, name)

        return task

    def _check_closed(self):
        # 若是关闭状态则直接抛出异常
        if self._closed:
            raise RuntimeError('Event loop is closed')


    def set_task_factory(self, factory):
        if factory is not None and not callable(factory):
            raise TypeError('task factory must be a callable or None')
        self._task_factory = factory
```

#### tasks.Task

tasks.Task 的源码如下：

```python

# ----- futures -----

class Future:
    _state = _PENDING
    _result = None
    _exception = None
    _loop = None
    _source_traceback = None
    _cancel_message = None
    _cancelled_exc = None

    _asyncio_future_blocking = False

    __log_traceback = False

    def __init__(self, *, loop=None):
        # 2. loop 传入的不是 None、所以这里直接走 else
        if loop is None:
            self._loop = events._get_event_loop()
        else:
            self._loop = loop
        self._callbacks = []
        if self._loop.get_debug():
            self._source_traceback = format_helpers.extract_stack(
                sys._getframe(1))


# ...
_PyFuture = Future

# ----- tasks -----

_task_name_counter = itertools.count(1).__next__

# ...
class Task(futures._PyFuture):

    _log_destroy_pending = True

    def __init__(self, coro, *, loop=None, name=None, context=None):
        # 1. 运行 super 也就是 Future 的 __init__ 方法
        super().__init__(loop=loop)
        if self._source_traceback:
            del self._source_traceback[-1]

        # 若不是一个 coroutine 则抛出异常
        if not coroutines.iscoroutine(coro):
            self._log_destroy_pending = False
            raise TypeError(f"a coroutine was expected, got {coro!r}")

        # 若没有指定 name 则生成一个 name
        if name is None:
            self._name = f'Task-{_task_name_counter()}'
        else:
            self._name = str(name)

        self._num_cancels_requested = 0
        self._must_cancel = False
        self._fut_waiter = None
        self._coro = coro
        if context is None:
            self._context = contextvars.copy_context()
        else:
            self._context = context

        # 运行 _UnixSelectorEventLoop 的 call_soon 方法
        # 注意: Task init时就会把自己的 step 方法注册到事件循环中
        self._loop.call_soon(self.__step, context=self._context)
        _register_task(self)
```

#### BaseEventLoop.call_soon

_UnixSelectorEventLoop 未实现 call_soon() 方法，而是在其超类 BaseEventLoop 中实现：

将Task的step包装成Handle对象，然后将其放入到_ready中，等待下一次事件循环时执行。

> 学习一下 call_soon , _call_soon 这种写法,真正核心逻辑写在 _call_soon 中,call_soon 只是一个包装,可以在其中做一些非核心逻辑的处理,比如这里的 debug

```python
class BaseEventLoop(events.AbstractEventLoop):
    def __init__(self):
        # ...
        # deque 双端队列
        self._ready = collections.deque()

    def _call_soon(self, callback, args, context):
        # handle 的源码可参照上面初始化 event loop 时的操作
        handle = events.Handle(callback, args, self, context)
        if handle._source_traceback:
            del handle._source_traceback[-1]
        # 将 handle 放入 _ready 中
        self._ready.append(handle)
        return handle

    def call_soon(self, callback, *args, context=None):
        # callback: Task.__step 方法
        # args: ()
        # context: dict
        self._check_closed()
        # 不走 debug，没必要细看
        if self._debug:
            self._check_thread()
            self._check_callback(callback, 'call_soon')
        handle = self._call_soon(callback, args, context)
        if handle._source_traceback:
            del handle._source_traceback[-1]
        return handle
```

#### _register_task

在 loop.call_soon() 执行执行完毕后，Task 的 `__init__` 方法最后会运行 _register_task() 方法。

```python

# 包含所有活动任务的 WeakSet。
_all_tasks = weakref.WeakSet()

def _register_task(task):
    """在 asyncio 中注册一个由循环执行的新任务。"""
    _all_tasks.add(task)
```

#### runner.run

现在，让我们继续回到 runner.run() 方法中。

```python
class Runner:
    def __init__(self, *, debug=None, loop_factory=None):
        self._state = _State.CREATED # INITIALIZED
        self._debug = debug
        self._loop_factory = loop_factory  # _UnixSelectorEventLoop 实例对象
        self._loop = None
        self._context = None          # dict
        self._interrupt_count = 0
        self._set_event_loop = False  # True

    def run(self, coro, *, context=None):

        if not coroutines.iscoroutine(coro):
            raise ValueError("a coroutine was expected, got {!r}".format(coro))

        if events._get_running_loop() is not None:
            raise RuntimeError(
                "Runner.run() cannot be called from a running event loop")

        self._lazy_init()

        if context is None:
            context = self._context

        task = self._loop.create_task(coro, context=context)

        # 如果当前线程是主线程并且当前使用了 SIGNAL 的默认处理程序结果是 True
        # 这里是 ctrl + c 终止程序的信号
        if (threading.current_thread() is threading.main_thread()
            and signal.getsignal(signal.SIGINT) is signal.default_int_handler
        ):
            # 则信号处理程序设置为 self._on_sigint 程序, 并将主任务传递进去
            sigint_handler = functools.partial(self._on_sigint, main_task=task)

            # 尝试设置当前的信号处理程序
            try:
                signal.signal(signal.SIGINT, sigint_handler)
            except ValueError:
                sigint_handler = None
        else:
            sigint_handler = None

        self._interrupt_count = 0

        try:
            # 核心代码
            return self._loop.run_until_complete(task)
        except exceptions.CancelledError:
                # 异常处理逻辑
                uncancel = getattr(task, "uncancel", None)
                if uncancel is not None and uncancel() == 0:
                    raise KeyboardInterrupt()
            raise  # CancelledError
        finally:
            # 解绑 ctrl+c 的信号处理
            if (sigint_handler is not None
                and signal.getsignal(signal.SIGINT) is sigint_handler
            ):
                signal.signal(signal.SIGINT, signal.default_int_handler)


    def _on_sigint(self, signum, frame, main_task):
        # 主线程里 +1
        self._interrupt_count += 1
        if self._interrupt_count == 1 and not main_task.done():
            # 取消主任务
            main_task.cancel()
            self._loop.call_soon_threadsafe(lambda: None)
            return
        raise KeyboardInterrupt()
```

#### BaseEventLoop.run_until_complete

_UnixSelectorEventLoop 并未实现 run_until_complete() 方法。而是由其超类 BaseEventLoop 所实现。

BaseEventLoop.run_until_complete() 源码如下：

```python
class BaseEventLoop(events.AbstractEventLoop):

    def __init__(self):
        self._timer_cancelled_count = 0
        self._closed = False
        self._stopping = False
        self._ready = collections.deque()  # 应该塞了一个 handle
        self._scheduled = []
        self._default_executor = None
        self._internal_fds = 0

    def _check_closed(self):
        if self._closed:
            raise RuntimeError('Event loop is closed')

    def is_running(self):
        """Returns True if the event loop is running."""
        return (self._thread_id is not None)

    def _check_running(self):
        if self.is_running():
            raise RuntimeError('This event loop is already running')
        if events._get_running_loop() is not None:
            raise RuntimeError(
                'Cannot run the event loop while another loop is running')

    def run_until_complete(self, future):
        # future 就是 main coroutine 的入口函数的 task

        # 1. 未关闭
        self._check_closed()

        # 2. self._thread_id 现在是 None,所以这里不会报错
        self._check_running()

        # False
        new_task = not futures.isfuture(future)

        # 3. 将 task 传入，返回一个 future 对象
        future = tasks.ensure_future(future, loop=self)

        if new_task:
            future._log_destroy_pending = False

        # 5. 给 main coroutine 的入口函数的 task 添加一个回调函数
        future.add_done_callback(_run_until_complete_cb)

        try:
            # 6. 开始运行
            self.run_forever()
        except:
            if new_task and future.done() and not future.cancelled():
                future.exception()
            raise
        finally:
            # 执行完成后，解绑毁回调函数
            future.remove_done_callback(_run_until_complete_cb)
        # 若报错，则代表事件循环关闭了
        if not future.done():
            raise RuntimeError('Event loop stopped before Future completed.')
        # 返回未来对象的结果
        return future.result()

# ---- tasks ----

def ensure_future(coro_or_future, *, loop=None):
    return _ensure_future(coro_or_future, loop=loop)

def _ensure_future(coro_or_future, *, loop=None):
    # 4. 保证是 future
    # True
    if futures.isfuture(coro_or_future):
        # False
        if loop is not None and loop is not futures._get_loop(coro_or_future):
            raise ValueError('The future belongs to a different loop than '
                            'the one specified as the loop argument')
        # 直接 return
        return coro_or_future

    # 如果不是一个 coro 或者 future、则进行其他处理
    called_wrap_awaitable = False
    if not coroutines.iscoroutine(coro_or_future):
        if inspect.isawaitable(coro_or_future):
            coro_or_future = _wrap_awaitable(coro_or_future)
            called_wrap_awaitable = True
        else:
            raise TypeError('An asyncio.Future, a coroutine or an awaitable '
                            'is required')

    if loop is None:
        loop = events._get_event_loop(stacklevel=4)
    try:
        return loop.create_task(coro_or_future)
    except RuntimeError:
        if not called_wrap_awaitable:
            coro_or_future.close()
        raise
```

#### BaseEventLoop.run_forever

BaseEventLoop.run_forever() 的源码如下：

```python
class BaseEventLoop(events.AbstractEventLoop):
    def __init__(self):
        self._timer_cancelled_count = 0
        self._closed = False
        self._stopping = False
        self._ready = collections.deque()  # 应该塞了一个 handle
        self._scheduled = []
        self._default_executor = None
        self._internal_fds = 0
        self._thread_id = 111   # 当前线程 id

    def _check_closed(self):
        if self._closed:
            raise RuntimeError('Event loop is closed')

    def is_running(self):
        """Returns True if the event loop is running."""
        return (self._thread_id is not None)

    def _check_running(self):
        if self.is_running():
            raise RuntimeError('This event loop is already running')
        if events._get_running_loop() is not None:
            raise RuntimeError(
                'Cannot run the event loop while another loop is running')

    def run_forever(self):
        """Run until stop() is called."""

        # 1. 未关闭
        self._check_closed()
        # 2. 未运行
        self._check_running()
        # 3. 不重要
        self._set_coroutine_origin_tracking(self._debug)

        # 4. 获取旧的异步生成器钩子
        old_agen_hooks = sys.get_asyncgen_hooks()
        try:
            # 5. 将当前事件循环的 _thread_id 给赋值
            self._thread_id = threading.get_ident()
            # 6. 设置异步生成器的钩子函数
            sys.set_asyncgen_hooks(firstiter=self._asyncgen_firstiter_hook,
                                   finalizer=self._asyncgen_finalizer_hook)

            # 7. 设置正在运行的 loop
            events._set_running_loop(self)

            # 8. 调用 _run_once
            while True:
                self._run_once()
                # 9. 如果 _stopping 为 True、则跳出
                if self._stopping:
                    break
        finally:
            # 恢复标志位、恢复生成器钩子函数
            self._stopping = False
            self._thread_id = None
            events._set_running_loop(None)
            self._set_coroutine_origin_tracking(False)
            sys.set_asyncgen_hooks(*old_agen_hooks)


    def _asyncgen_firstiter_hook(self, agen):
        # 在之前调用
        if self._asyncgens_shutdown_called:
            warnings.warn(
                f"asynchronous generator {agen!r} was scheduled after "
                f"loop.shutdown_asyncgens() call",
                ResourceWarning, source=self)

        self._asyncgens.add(agen)


    def _asyncgen_finalizer_hook(self, agen):
        # 在之后调用
        self._asyncgens.discard(agen)
        if not self.is_closed():
            self.call_soon_threadsafe(self.create_task, agen.aclose())


# ---- events ----

def _set_running_loop(loop):
    _running_loop.loop_pid = (loop, os.getpid())
```

#### BaseEventLoop._run_once

BaseEventLoop._run_once() 方法源码如下：

```python
class BaseEventLoop(events.AbstractEventLoop):
    def __init__(self):
        self._timer_cancelled_count = 0
        self._closed = False
        self._stopping = False
        self._ready = collections.deque()  # 应该塞了 1 个 handle
        self._scheduled = []
        self._default_executor = None
        self._internal_fds = 0
        self._thread_id = 111   # 当前线程 id

    def _run_once(self):
        sched_count = len(self._scheduled)

        # 1. 判断当前需要调度的数量，是否大于 _MIN_SCHEDULED_TIMER_HANDLES
        # 并且已取消的计时器句柄数量除以需要调度的数量大于 _MIN_SCHEDULED_TIMER_HANDLES
        # 这里的条件肯定是不满足的
        if (sched_count > _MIN_SCHEDULED_TIMER_HANDLES and
            self._timer_cancelled_count / sched_count >
                _MIN_CANCELLED_TIMER_HANDLES_FRACTION):
            new_scheduled = []
            for handle in self._scheduled:
                if handle._cancelled:
                    handle._scheduled = False
                else:
                    new_scheduled.append(handle)

            heapq.heapify(new_scheduled)
            self._scheduled = new_scheduled
            self._timer_cancelled_count = 0
        else:
            # 2. 这里的 while 循环也跑不起来的，因为 self._scheduled 是 []
            # self._scheduled 中存放的是定时任务-例如asyncio.sleep(1)
            while self._scheduled and self._scheduled[0]._cancelled:
                self._timer_cancelled_count -= 1
                handle = heapq.heappop(self._scheduled)
                handle._scheduled = False

        # 3. timeout 这里应该是满足条件的，置 0
        timeout = None
        if self._ready or self._stopping:
            timeout = 0

        elif self._scheduled:
            when = self._scheduled[0]._when
            timeout = min(max(0, when - self.time()), MAXIMUM_SELECT_TIMEOUT)

        # 4. BaseSelectorEventLoop 子类中有这个 _selector，这里直接开启监听。
        # 这里监听的对象只有 1 个 socket 对象，由于没有事件触发，所以这里会直接跳过
        event_list = self._selector.select(timeout)
        # BaseEventLoop._process_events
        self._process_events(event_list)
        event_list = None

        end_time = self.time() + self._clock_resolution

        # 5. 不会进行循环
        while self._scheduled:
            handle = self._scheduled[0]
            if handle._when >= end_time:
                break
            handle = heapq.heappop(self._scheduled)
            handle._scheduled = False
            self._ready.append(handle)

        # 6. self._ready 的长度应该为 1，里面放了一个 handle
        ntodo = len(self._ready)

        for i in range(ntodo):
            # 弹出第一个 handle，若没取消则运行其 _run 方法
            handle = self._ready.popleft()
            if handle._cancelled:
                continue
            # 若开启了调试模式，则还需要记录时间
            if self._debug:
                try:
                    self._current_handle = handle
                    t0 = self.time()
                    handle._run()
                    dt = self.time() - t0
                    if dt >= self.slow_callback_duration:
                        logger.warning('Executing %s took %.3f seconds',
                                       _format_handle(handle), dt)
                finally:
                    self._current_handle = None
            else:
                # 运行其 _run 方法
                handle._run()
        handle = None
```

#### handle._run

handle 对象是用户所创建的任务对象的抽象层。

因为 Task 内部实际上是调用了 loop.call_soon() 方法将 coroutine 放在 Task 对象中，而 Task 对象的 __step() 方法又将作为 callback 封装给 handle. 并 register task 至 _all_tasks 这个 WeakSet 中。

换而言之、事件循环总是通过 _ready 队列拿到不同的 handle，并通过 handle 来执行最初的 coroutine 任务。

以下是 handle._run() 方法的源码：

```python

class Handle:

    def __init__(self, callback, args, loop, context=None):

        if context is None:
            context = contextvars.copy_context()

        self._context = context  # Task 对象创建时的上下文环境
        self._loop = loop  # 当前的 event loop
        self._callback = callback  # 就是 Task 对象的 __step
        self._args = args
        self._cancelled = False
        self._repr = None
        if self._loop.get_debug():
            self._source_traceback = format_helpers.extract_stack(
                sys._getframe(1))
        else:
            self._source_traceback = None


    def cancel(self):
        if not self._cancelled:
            self._cancelled = True
            if self._loop.get_debug():
                self._repr = repr(self)
            self._callback = None
            self._args = None

    def cancelled(self):
        return self._cancelled

    def _run(self):
        try:
            # 运行 Task 对象的 __step 方法
            self._context.run(self._callback, *self._args)
        # 若有异常，则交由默认的异常处理函数进行处理
        except (SystemExit, KeyboardInterrupt):
            raise
        except BaseException as exc:
            cb = format_helpers._format_callback_source(
                self._callback, self._args)
            msg = f'Exception in callback {cb}'
            context = {
                'message': msg,
                'exception': exc,
                'handle': self,
            }
            if self._source_traceback:
                context['source_traceback'] = self._source_traceback
            self._loop.call_exception_handler(context)
        self = None  # 发生异常时需要中断循环。
```

#### Task.__step

Task.__step() 中的逻辑是如何运行传入的协程函数：

```python

# 包含所有正在活动的任务
_all_tasks = weakref.WeakSet()

# 一个字典，包含当前正在活动的任务 {loop: task}
_current_tasks = {}

def _enter_task(loop, task):
    # 4. 为当前的 loop 添加活动任务
    # 若当前 loop 已经有一个活动任务，则抛出 RuntimeError
    current_task = _current_tasks.get(loop)
    if current_task is not None:
        raise RuntimeError(f"Cannot enter into task {task!r} while another "
                           f"task {current_task!r} is being executed.")

    _current_tasks[loop] = task


def _leave_task(loop, task):
    # 10. 取消活动任务
    current_task = _current_tasks.get(loop)
    if current_task is not task:
        raise RuntimeError(f"Leaving task {task!r} does not match "
                           f"the current task {current_task!r}.")
    del _current_tasks[loop]

class Task(futures._PyFuture):

    _log_destroy_pending = True

    def __init__(self, coro, *, loop=None, name=None, context=None):
        super().__init__(loop=loop)
        if self._source_traceback:
            del self._source_traceback[-1]

        if not coroutines.iscoroutine(coro):
            self._log_destroy_pending = False
            raise TypeError(f"a coroutine was expected, got {coro!r}")

        if name is None:
            self._name = f'Task-{_task_name_counter()}'
        else:
            self._name = str(name)

        self._num_cancels_requested = 0
        self._must_cancel = False
        self._fut_waiter = None
        # 当前运行时来看，这里应该是入口函数的 coroutine
        # 即为 asyncio.run(main()) 的 main()
        self._coro = coro
        if context is None:
            self._context = contextvars.copy_context()
        else:
            self._context = context

        self._loop.call_soon(self.__step, context=self._context)
        _register_task(self)



    def __step(self, exc=None):
        # 1. 若当前任务已经 done 掉则抛出异常（这里的异常会被 handle._run 捕获的）
        if self.done():
            raise exceptions.InvalidStateError(
                f'_step(): already done: {self!r}, {exc!r}')

        # 2. 若需要取消，且 exc 不是 CancelledError 类型的异常，则创建一个取消任务
        # 实际上就是将 exc 赋值成一个 CancelledError 的对象
        if self._must_cancel:
            if not isinstance(exc, exceptions.CancelledError):
                exc = self._make_cancelled_error()
            self._must_cancel = False
        coro = self._coro
        self._fut_waiter = None

        # 3. 调用 _enter_task() 函数
        _enter_task(self._loop, self)

        # Call either coro.throw(exc) or coro.send(None).
        try:
            # 主动启动协程对象 - 激活
            if exc is None:
                # 我们直接使用 `send` 方法，因为协程
                # 没有 __iter__ 和 __next__ 方法。
                result = coro.send(None)
            else:
                # 如果有 exc 则通过 throw 向协程函数内部抛出异常
                result = coro.throw(exc)

        except StopIteration as exc:
            # 4. 若协程函数执行完毕则判断是否需要取消
            if self._must_cancel:
                # 通过调度后尝试取消任务（下次事件循环过程中触发）
                self._must_cancel = False
                super().cancel(msg=self._cancel_message)
            else:
                # 设置结果
                super().set_result(exc.value)

        except exceptions.CancelledError as exc:
            # 5. 保存原始异常，以便我们稍后将其链接起来
            self._cancelled_exc = exc
            # 通过调度后尝试取消任务（下次事件循环过程中触发）
            super().cancel()  # I.e., Future.cancel(self).

        except (KeyboardInterrupt, SystemExit) as exc:
            # 6. 如果是 <c-c> 或者系统推出，则设置异常任务，立即触发
            super().set_exception(exc)
            raise

        except BaseException as exc:
            # 7. 若是其他基本异常，则设置异常任务，立即触发
            super().set_exception(exc)

        else:
            # 8. 没有异常，对协程结果开始进行判定
            # 首先，查看 result 是否具有 _asyncio_future_blocking 属性
            blocking = getattr(result, '_asyncio_future_blocking', None)
            if blocking is not None:
                # 如果 result 对象所属的事件循环与当前任务的事件循环不一致
                # 则抛出 RuntimeError 异常（下次事件循环过程中触发）
                if futures._get_loop(result) is not self._loop:
                    new_exc = RuntimeError(
                        f'Task {self!r} got Future '
                        f'{result!r} attached to a different loop')
                    self._loop.call_soon(
                        self.__step, new_exc, context=self._context)

                # 如果 blocking 为 True
                elif blocking:

                    # 如果返回的结果就是 Task 本身, 则引发 RuntimeError
                    # （下次事件循环过程中触发）
                    if result is self:
                        new_exc = RuntimeError(
                            f'Task cannot await on itself: {self!r}')
                        self._loop.call_soon(
                            self.__step, new_exc, context=self._context)
                    
                    # 如果不是则说明 当前Task 有需要 等待 的任务 (注意这里是asyncio的精华)
                    # 将 self.__wakeup 设置为 result 对象(当前Task需要等待的任务)的回调函数
                    # 并将 result 对象作为等待者保存在 _fut_waiter 属性中
                    # 如果此时任务需要取消，并且成功取消了等待者，则将 _must_cancel 标志设置为 False。
                    else:

                        result._asyncio_future_blocking = False
                        result.add_done_callback(
                            self.__wakeup, context=self._context)

                        self._fut_waiter = result
                        if self._must_cancel:
                            if self._fut_waiter.cancel(
                                    msg=self._cancel_message):
                                self._must_cancel = False

                # 如果 blocking 值为 False
                # 则抛出 RuntimeError 异常（下次事件循环过程中触发）
                else:
                    new_exc = RuntimeError(
                        f'yield was used instead of yield from '
                        f'in task {self!r} with {result!r}')
                    self._loop.call_soon(
                        self.__step, new_exc, context=self._context)

            # 如果结果对象 result 为 None
            # 表示协程使用了 yield 语句，它调度一个新的事件循环迭代，即再次调用 __step 方法。
            # 直到 StopIteration 被触发后，协程函数才真正运行完毕
            elif result is None:
                self._loop.call_soon(self.__step, context=self._context)

            # 如果结果对象 result 是一个生成器对象
            # 则抛出 RuntimeError 异常，表示协程在生成器中使用了错误的语法。
            # （下次事件循环过程中触发）
            elif inspect.isgenerator(result):
                # Yielding a generator is just wrong.
                new_exc = RuntimeError(
                    f'yield was used instead of yield from for '
                    f'generator in task {self!r} with {result!r}')
                self._loop.call_soon(
                    self.__step, new_exc, context=self._context)
            else:
                # 对于其他类型的结果对象，抛出 RuntimeError 异常，表示协程产生了无效的
                # 结果（下次事件循环过程中触发）
                new_exc = RuntimeError(f'Task got bad yield: {result!r}')
                self._loop.call_soon(
                    self.__step, new_exc, context=self._context)

        finally:
            # 9. 最后，使用 _leave_task 取消活动任务
            _leave_task(self._loop, self)
            # 发生异常，需要中断循环
            self = None
```

#### 关于回调函数的处理

众所周知，无论是 task 对象还是 future 未来对象，我们都可以通过 add_done_callback() 方法来为其新增一个回调函数。

那么在上面 task.__step() 方法运行的过程中，回调函数是在何时运行呢？

先从 add_done_callback() 方法看起，它其实是由 Task 类的父类 Future 实现：

```python
class Future:
    _state = _PENDING
    _result = None
    _exception = None
    _loop = None
    _source_traceback = None
    _cancel_message = None
    _cancelled_exc = None


    def __init__(self, *, loop=None):
        """
        if loop is None:
            self._loop = events._get_event_loop()
        else:
            self._loop = loop
        self._callbacks = []
        if self._loop.get_debug():
            self._source_traceback = format_helpers.extract_stack(
                sys._getframe(1))

    # ...

    def add_done_callback(self, fn, *, context=None):
        # 若当前对象的状态不是 peding
        # 则将 callback 放在下次事件循环中运行
        if self._state != _PENDING:
            self._loop.call_soon(fn, self, context=context)
        else:
            # 否则，将回调函数放在列表中
            if context is None:
                context = contextvars.copy_context()
            self._callbacks.append((fn, context))
```

调用 callback 的方法是由 Future 实现，方法名为 __schedule_callbacks，源码如下：

```python

    def __schedule_callbacks(self):
        callbacks = self._callbacks[:]
        if not callbacks:
            return

        self._callbacks[:] = []
        # 循环所有回调函数、统一将其安排在下一次循环中按顺序执行
        for callback, ctx in callbacks:
            self._loop.call_soon(callback, self, context=ctx)
```

接下来我们只需要找到在那些方法中会调用 __schedule_callbacks 就知道了其执行时机，以下方法均为 Future 类提供：

```python
    def set_result(self, result):
        if self._state != _PENDING:
            raise exceptions.InvalidStateError(f'{self._state}: {self!r}')
        self._result = result
        self._state = _FINISHED         # 修改任务状态
        self.__schedule_callbacks()

    def set_exception(self, exception):
        if self._state != _PENDING:
            raise exceptions.InvalidStateError(f'{self._state}: {self!r}')
        if isinstance(exception, type):
            exception = exception()
        if type(exception) is StopIteration:
            raise TypeError("StopIteration interacts badly with generators "
                            "and cannot be raised into a Future")
        self._exception = exception
        self._exception_tb = exception.__traceback__
        self._state = _FINISHED         # 修改任务状态
        self.__schedule_callbacks()
        self.__log_traceback = True

    def cancel(self, msg=None):
        self.__log_traceback = False
        if self._state != _PENDING:
            return False
        self._state = _CANCELLED       # 修改任务状态
        self._cancel_message = msg
        self.__schedule_callbacks()
        return True
```

以此可见，回调函数的执行会放在事件循环的就绪队列中，如果 task 或者 future 的 callback 在执行过程中拥有较长的阻塞时长时，将会阻塞整个事件循环！- 会导致调度的不公平

除此之外，每一次 callback 的执行必须是在当前主任务运行完毕后执行。举个例子：

```python
ready = [task1, task2, task3]
```

若第一个 task 有 callback, 则其 callback 会放在最后：

```python
ready = [task2, task3, task1_cb]
```

callback 运行前必须先运行 task2 和 task3。

#### 主协程任务的结束

当主协程任务结束后，所有的子协程任务也会结束掉。这是为什么呢？我们继续从源码角度进行分析。

首先在 BaseEventLoop.run_until_complete() 方法中，_ready 队列会在下次循环中添加 1 个 callback：

```python
future.add_done_callback(_run_until_complete_cb)


def add_done_callback(self, fn, *, context=None):
    if self._state != _PENDING:
        self._loop.call_soon(fn, self, context=context)
    else:
        # 主协程任务的状态此时应该是 peding
        # 所以他只会在主协程任务结束后将回调添加到 ready 队列中
        if context is None:
            context = contextvars.copy_context()
        self._callbacks.append((fn, context))
```

当主协程任务在 BaseEventLoop.__step() 方法中被运行 set_result()、set_exception()、或者 cancel() 任意一个时，base_events._run_until_complete_cb() 都会被添加进 _ready 队列中。

而 base_events._run_until_complete_cb() 方法的实现如下：

```python
def _run_until_complete_cb(fut):
    if not fut.cancelled():
        exc = fut.exception()
        if isinstance(exc, (SystemExit, KeyboardInterrupt)):
            # Issue #22429: run_forever() already finished, no need to
            # stop it.
            return
    futures._get_loop(fut).stop()
```

事件循环的 stop() 方法实现、直接看 BaseEventLoop.stop() 即可，因为 _UnixSelectorEventLoop 包括 BaseSelectorEventLoop 都未实现该方法：

```python
    def stop(self):
        self._stopping = True
```

最后再回过头看 BaseEventLoop.run_forever() 方法，是不是明了了些？：

```python
    def run_forever(self):
        # ...
        try:
            self._thread_id = threading.get_ident()
            sys.set_asyncgen_hooks(firstiter=self._asyncgen_firstiter_hook,
                                   finalizer=self._asyncgen_finalizer_hook)

            events._set_running_loop(self)
            while True:
                self._run_once()
                if self._stopping:
                    break
        # ...
```

总结、在主协程任务运行时，其 callback 方法 base_events._run_until_complete_cb() 并不会马上添加至 ready 队列中。

一但主协程任务运行完毕（调用 cancel()、set_result()、set_exception()）时，callback 会立即添加到 ready 队列中。

这意味着事件循环即将结束，但在 callback 之前的子任务还可以继续运行，一旦当 callback 执行完毕，那么就意味着事件循环被关闭掉了。BaseEventLoop._run_once() 方法也不会继续运行。至此整个事件循环的生命周期才真正结束。

#### 事件循环启动和任务执行流程图

基本的事件循环启动和任务执行流程图如下：

​![](assets/net-img-未命名文件(1)-20231107115039-72v5y3h.png)​

## 本章结语

由于平时要忙工作什么的，算下来这篇文章总共花了我大概小半个月时间，不过算起来收获颇丰。

至少笔者在读完 asyncio 事件循环后，也有了一些新的感悟：

* 每一个事件循环都有一个 sock 对象和一个系统选择器，这也是 loop.create_server() 方法的基础，在每次运行 BaseEventLoop._run_once() 方法时都会去检测一遍系统选择器有没有准备好的事件描述符，若有则运行其他逻辑（当然这部分还没有深入研究，但大体上是不会错的）
* 事件循环中有很多对 loop 的操作，如 new_event_loop()、set_event_loop()、get_event_loop()、get_running_loop() 等等，通过源码阅读可以更好的清楚他们的作用
* 清楚了 create_task() 以及 call_soon() 方法的关系，明白了 Task 对象和 Future 对象以及 Handle 对象的关系
* 知道了事件循环是定序执行子任务的，也知道了回调函数的添加以及执行时机，更重要的是明白了事件循环是如何实现的
* 知晓了一些钩子函数的真实作用，如 set_task_factory() 等等

其实 asyncio 不止单单一个事件循环、除此之外还有 socket、流式传输、各种锁的应用等等，事件循环只能说是 asyncio 中的基础。

最后的最后，希望大家继续努力，保持学习，不忘初心。

还是开篇那句话 「路漫漫其修远兮, 吾将上下而求索」与诸君共勉之。
