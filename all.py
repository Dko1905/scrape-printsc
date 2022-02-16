#!/usr/bin/env python3
from threading import Thread, Lock
from html.parser import HTMLParser
from rich.console import Console, escape
import requests
import random
from time import sleep

# Generate string names
def generate_names(start, stop, max_depth):
    # Geneartor returns complete string
    def rec(depth):
        if depth == 0:
            yield ""
        elif depth < 0:
            return
        for x in range(start, stop):
            for ch in rec(depth - 1):
                yield chr(x) + ch
    return rec(max_depth)

# Create slice of generator output
def take(start, stop, gen):
    for x in range(0, start):
        gen.__next__()
    for x in range(start, stop):
        yield gen.__next__()

class WarnException(Exception):
    pass

class ErrorCodeException(Exception):
    def __init__(self, code, message):
        self.code = code
        self.message = message
        super().__init__(self.message)

class MyHTMLParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.src = None

    def handle_starttag(self, tag, attrs):
        if (tag == 'meta'):
            # src = attrs[0][1]
            attrs = dict(attrs)
            if 'name' not in attrs:
                return
            if not attrs['name'] == 'twitter:image:src':
                return
            self.src = attrs['content']

class ThreadProcess(Thread):
    def __init__(self, thread_ID, gen, gen_lock, req, console):
        Thread.__init__(self)
        self.thread_ID = thread_ID
        # Custom input
        self.gen = gen
        self.gen_lock = gen_lock
        self.req = req
        self.console = console
        self.parser = MyHTMLParser()

    def processOne(self, name, url):
        # Get page
        res = self.req.get(url)
        if res.status_code != 200:
            raise ErrorCodeException(res.status_code, f'Page returned error code: {res.status_code}')

        # Parse page and retrieve image url
        self.parser.feed(res.text)
        src = self.parser.src
        if not src:
            raise ErrorCodeException(res.status_code, f'No image in page')
        if src == "//st.prntscr.com/2022/01/07/0148/img/0_173a7b_211be8ff.png":
            raise WarnException(f'Received 404 image')
            return

        # Download image
        res = self.req.get(src)
        if res.status_code != 200:
            raise ErrorCodeException(res.status_code, f'Image returned error code: {res.status_code}')
        # Save image
        with open(f'imgs/{name}.png', 'wb') as f:
            f.write(res.content)
        # Done :D


    def process(self):
        while True:
            self.gen_lock.acquire()
            try:
                name = self.gen.__next__()
            except:
                break
            finally:
                self.gen_lock.release()
            try:
                n = 5
                while n > 0:
                    try:
                        self.processOne(name, f"https://prnt.sc/{name}")
                    except ErrorCodeException as e:
                        console.print(f"{name} : [bold #f04a00]Retrying: {e.code}[/bold #f04a00]")
                        n -= 1
                        sleep(1)
                        continue
                    break
                console.print(f"{name} : [bold green]Done[/bold green]")
            except WarnException as we:
                console.print(f"{name} : [bold #f04a00]{we}[/bold #f04a00]")
            except Exception as e:
                console.print(f"{name} : [bold red]{e}[/bold red]")

    def run(self):
        console.print(f"Started thread {self.thread_ID}")
        sleep(1)
        self.process()

# 7000 - 7010
names = take(7000, 7100, generate_names(97, 122, 6))
names_lock = Lock()
cookies = requests.cookies.RequestsCookieJar()
cookies.set("euconsent-v2", "CPUf5p0PUf5p0AKAnAENCCCsAP_AAH_AAAwIIltf_X__bX9j-_5_f_t0eY1P9_r3v-QzjhfNt-8F3L_W_L0X42E7NF36pq4KuR4Eu3LBIQNlHMHUTUmwaokVrzHsak2cpyNKJ7LEmnMZO2dYGHtPn9lDuYKY7_7___fz3j-v_t_-39T378X_3_d5_2---vCfV599zLv9____39nP___9v-_9_____4IhgEmGpeQBdmWODJtGlUKIEYVhIVAKACigGFoisAHBwU7KwCfUELABCagIwIgQYgowYBAAIJAEhEQEgBYIBEARAIAAQAoQEIACJgEFgBYGAQACgGhYgBQACBIQZHBUcpgQFSLRQS2ViCUFexphAGWeBFAojIqABGs0QLAyEhYOY4AkBLxZIHmKF8gAAAAA.YAAAAAAAAAAA")
req = requests.Session()
req.headers['User-Agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:83.0) Gecko/20100101 Firefox/83.0'
req.cookies = cookies
console = Console()

tp_arr = []
thread_id = 1
for x in range(0, 1):
    tp = ThreadProcess(thread_id, names, names_lock, req, console)
    tp.start()
    tp_arr.append(tp)
    thread_id += 1

for tp in tp_arr:
    tp.join()
