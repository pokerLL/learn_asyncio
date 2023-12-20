import sys
sys.path.insert(0, '/Users/lei/workspace/program/asyncio-src/')

import mini_asyncio
import urllib.parse
import time

def test():
    async def print_http_headers(url):
        url = urllib.parse.urlsplit(url)
        print(f"enter print_http_headers({url}), {time.strftime('%H:%M:%S')}")
        if url.scheme == 'https':
            reader, writer = await mini_asyncio.open_connection(
                url.hostname, 443, ssl=True
            )
        else:
            reader, writer = await mini_asyncio.open_connection(
                url.hostname, 80
            )
        
        print(f"get reader&writer  print_http_headers({url}), {time.strftime('%H:%M:%S')}")

        query = (
            f"HEAD {url.path or '/' } HTTP/1.0\r\n"
            f"Host: {url.hostname}\r\n"
            f"\r\n"
        )

        writer.write(query.encode('latin-1'))
        while True:
            line = await reader.readline()
            if not line:
                break

            line = line.decode('latin1').rstrip()
            if line:
                print(f'HTTP header> {line}')

        writer.close()

    url = 'https://www.baidu.com'
    mini_asyncio.run(print_http_headers(url))


if __name__ == '__main__':
    test()
