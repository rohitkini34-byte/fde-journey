"""Day 13 lesson examples, in lesson order (rebuilt from the master doc).
Run one section at a time: some need Postgres, a server or files from the original starter zip."""

# ===== section: Concept 1: Waiting is the bottleneck, and the event loop =====
# Waiting one by one vs waiting together: three slow "API calls".
import asyncio
import time


def fetch_blocking(page: int) -> str:
    time.sleep(1)  # pretend the CMS takes 1 s to answer
    return f"page {page}"


async def fetch_async(page: int) -> str:
    await asyncio.sleep(1)  # same 1 s wait, but the loop can run others
    return f"page {page}"


async def main() -> None:
    start = time.perf_counter()
    results = await asyncio.gather(fetch_async(1), fetch_async(2),
                                   fetch_async(3))
    print(results, f"{time.perf_counter() - start:.1f}s")


start = time.perf_counter()
print([fetch_blocking(p) for p in (1, 2, 3)],
      f"{time.perf_counter() - start:.1f}s")
# -> ['page 1', 'page 2', 'page 3'] 3.0s   (1 + 1 + 1)
asyncio.run(main())
# -> ['page 1', 'page 2', 'page 3'] 1.0s   (the three waits overlap)

# ===== section: Concept 2: Coroutines, async def and await =====
# A coroutine function returns a coroutine object; await runs it.
import asyncio


async def get_title(uid: str) -> str:
    print(f"  fetching {uid}")
    await asyncio.sleep(0.1)
    return f"title of {uid}"


async def main() -> None:
    c = get_title("blt001")  # nothing runs yet, no "fetching" line
    print(type(c).__name__)  # -> coroutine
    title = await c  # NOW it runs
    # -> "  fetching blt001" is printed at this point
    print(title)  # -> title of blt001


asyncio.run(main())

# ===== section: Concept 2: Coroutines, async def and await =====
# Forgetting await: no error at the call, just a warning and no work done.
import asyncio


async def save_entry(uid: str) -> None:
    await asyncio.sleep(0.1)
    print(f"saved {uid}")


async def main() -> None:
    save_entry("blt001")  # GOTCHA: missing await, the entry is NOT saved
    # -> RuntimeWarning: coroutine 'save_entry' was never awaited
    await save_entry("blt002")  # -> saved blt002


asyncio.run(main())
# Only blt002 is saved. Python warns, but the program does not crash.

# ===== section: Concept 2: Coroutines, async def and await =====
# Two awaits in a row still run one after the other.
import asyncio
import time


async def fetch(page: int) -> int:
    await asyncio.sleep(1)
    return page


async def main() -> None:
    start = time.perf_counter()
    a = await fetch(1)  # waits 1 s here...
    b = await fetch(2)  # ...then another 1 s here
    print(a, b, f"{time.perf_counter() - start:.1f}s")  # -> 1 2 2.0s


asyncio.run(main())

# ===== section: Concept 3: Running coroutines together: gather, create_task and TaskGroup =====
# gather() returns results in the order you passed them, not finish order.
import asyncio
import time


async def fetch(page: int, seconds: float) -> str:
    await asyncio.sleep(seconds)
    print(f"  finished page {page}")
    return f"page {page}"


async def main() -> None:
    start = time.perf_counter()
    results = await asyncio.gather(fetch(1, 0.3), fetch(2, 0.1),
                                   fetch(3, 0.2))
    # -> finished page 2, then page 3, then page 1 (fastest first)
    print(results)  # -> ['page 1', 'page 2', 'page 3']  (argument order)
    print(f"{time.perf_counter() - start:.1f}s")  # -> 0.3s (the slowest)


asyncio.run(main())

# ===== section: Concept 3: Running coroutines together: gather, create_task and TaskGroup =====
# create_task starts work now; await collects the result later.
import asyncio
import time


async def fetch(page: int) -> str:
    await asyncio.sleep(1)
    return f"page {page}"


async def main() -> None:
    start = time.perf_counter()
    t1 = asyncio.create_task(fetch(1))  # scheduled, starts at next await
    t2 = asyncio.create_task(fetch(2))
    print("both started")  # -> both started   (printed immediately)
    a = await t1  # both run while we wait here
    b = await t2  # already done, returns at once
    print(a, b, f"{time.perf_counter() - start:.1f}s")
    # -> page 1 page 2 1.0s


asyncio.run(main())

# ===== section: Concept 3: Running coroutines together: gather, create_task and TaskGroup =====
# TaskGroup: start many tasks; leaving the block waits for all of them.
import asyncio


async def fetch(skip: int) -> list[str]:
    if skip == 6:
        raise ValueError(f"bad page at skip={skip}")  # fails at once
    await asyncio.sleep(0.1)
    print(f"  done skip={skip}")
    return [f"e{skip}", f"e{skip + 1}", f"e{skip + 2}"]


async def main(skips: list[int]) -> None:
    try:
        async with asyncio.TaskGroup() as tg:
            tasks = [tg.create_task(fetch(s)) for s in skips]
        # here every task has finished successfully
        print([t.result() for t in tasks])
    except* ValueError as group:  # except* handles an ExceptionGroup
        for err in group.exceptions:
            print("failed:", err)


asyncio.run(main([0, 3]))
# ->   done skip=0
# ->   done skip=3
# -> [['e0', 'e1', 'e2'], ['e3', 'e4', 'e5']]
asyncio.run(main([0, 3, 6]))
# -> failed: bad page at skip=6
# no "done" lines: the group cancelled skip=0 and skip=3 for you

# ===== section: Concept 4: Limits: Semaphore and timeouts =====
# A Semaphore lets at most N coroutines into a block at the same time.
import asyncio
import time

stats = {"now": 0, "peak": 0}  # a dict, so the function can update it


async def fetch(sem: asyncio.Semaphore, page: int) -> int:
    async with sem:  # wait here until one of the N slots is free
        stats["now"] += 1
        stats["peak"] = max(stats["peak"], stats["now"])
        await asyncio.sleep(0.5)  # the request itself
        stats["now"] -= 1
    return page  # the slot is released when the "async with" block ends


async def main() -> None:
    sem = asyncio.Semaphore(3)  # the customer's limit: 3 at a time
    start = time.perf_counter()
    pages = await asyncio.gather(*(fetch(sem, p) for p in range(1, 11)))
    print(pages)  # -> [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    print(stats["peak"], f"{time.perf_counter() - start:.1f}s")
    # -> 3 2.0s   (10 pages through 3 slots = 4 rounds of 0.5 s)


asyncio.run(main())

# ===== section: Concept 4: Limits: Semaphore and timeouts =====
# asyncio.timeout(): give up on a slow step instead of hanging forever.
import asyncio


async def slow_cms() -> str:
    await asyncio.sleep(2)  # the customer's server is stuck
    return "data"


async def main() -> None:
    try:
        async with asyncio.timeout(0.5):  # Python 3.11+
            print(await slow_cms())
    except TimeoutError:
        print("gave up after 0.5 s")  # -> gave up after 0.5 s


asyncio.run(main())

# ===== section: Concept 5: httpx.AsyncClient, async HTTP =====
# httpx.AsyncClient: one client, three page requests at the same time.
# Start day13/mock_cms.py in another terminal first.
import asyncio
import time

import httpx


async def main() -> None:
    async with httpx.AsyncClient(
        base_url="http://127.0.0.1:8013",  # every URL below is relative
        headers={"api_key": "demo-key-123"},  # sent with every request
        timeout=5.0,  # FDE TIP: always set one; never wait forever
    ) as client:
        start = time.perf_counter()
        url = "/v3/content_types/article/entries"
        responses = await asyncio.gather(
            *(client.get(url, params={"skip": s, "limit": 3})
              for s in (0, 3, 6)))
        for r in responses:
            uids = [e["uid"] for e in r.json()["entries"]]
            print(r.status_code, uids)
        print(f"{time.perf_counter() - start:.1f}s")


asyncio.run(main())
# -> 200 ['art001', 'art002', 'art003']
# -> 200 ['art004', 'art005', 'art006']
# -> 200 ['art007', 'art008', 'art009']
# -> 0.5s   (three 0.5 s requests, overlapped)

# ===== section: Concept 5: httpx.AsyncClient, async HTTP =====
# No limit on our side: 6 requests at once, the CMS answers 429.
import asyncio

import httpx


async def main() -> None:
    async with httpx.AsyncClient(base_url="http://127.0.0.1:8013",
                                 headers={"api_key": "demo-key-123"},
                                 timeout=5.0) as client:
        url = "/v3/content_types/article/entries"
        rs = await asyncio.gather(
            *(client.get(url, params={"skip": s, "limit": 3})
              for s in range(0, 18, 3)))
        print([r.status_code for r in rs])
        print(rs[-1].headers.get("Retry-After"), rs[-1].json())


asyncio.run(main())
# -> [200, 200, 200, 429, 429, 429]   (which ones get 429 can vary)
# -> 1 {'error_message': 'Too many concurrent requests (limit 3)'}

# ===== section: Concept 5: httpx.AsyncClient, async HTTP =====
# Testing async HTTP with no server: httpx.MockTransport.
import asyncio

import httpx


async def fake_cms(request: httpx.Request) -> httpx.Response:
    # every request the client makes arrives here instead of the network
    if request.headers.get("api_key") != "k":
        return httpx.Response(401, json={"error_message": "Invalid API key"})
    return httpx.Response(200, json={"entries": [{"uid": "blt001"}]})


async def main() -> None:
    transport = httpx.MockTransport(fake_cms)
    async with httpx.AsyncClient(transport=transport,
                                 base_url="http://cms.test") as client:
        r = await client.get("/entries", headers={"api_key": "k"})
        print(r.status_code, r.json())
        # -> 200 {'entries': [{'uid': 'blt001'}]}
        r = await client.get("/entries")  # no key
        print(r.status_code, r.json()["error_message"])
        # -> 401 Invalid API key


asyncio.run(main())

# ===== section: Concept 6: Patterns for real async work: fan-out pagination and blocking code =====
# Fan-out pagination: page 1 tells you the count, then ask for the rest.
import asyncio
import random

CMS = [f"art{n:03d}" for n in range(1, 11)]  # 10 fake entries


async def get_page(skip: int, limit: int) -> dict:
    await asyncio.sleep(random.uniform(0.05, 0.2))  # random finish order
    return {"entries": CMS[skip:skip + limit], "count": len(CMS)}


async def main() -> None:
    first = await get_page(0, 3)  # must come first: we need "count"
    skips = list(range(3, first["count"], 3))
    print(skips)  # -> [3, 6, 9]
    rest = await asyncio.gather(*(get_page(s, 3) for s in skips))
    pages = [first, *rest]  # same order as skips, whatever finished first
    print([uid for page in pages for uid in page["entries"]])
    # -> ['art001', 'art002', ..., 'art010']   (CMS order, every time)


asyncio.run(main())

# ===== section: Concept 6: Patterns for real async work: fan-out pagination and blocking code =====
# One blocking call inside async code stops EVERY task, not just its own.
import asyncio
import time


async def bad_fetch(page: int) -> int:
    time.sleep(0.5)  # GOTCHA: blocks the whole event loop
    return page


async def good_fetch(page: int) -> int:
    # run the blocking function in a worker thread, await the result
    await asyncio.to_thread(time.sleep, 0.5)
    return page


async def timed(fetch) -> None:
    start = time.perf_counter()
    await asyncio.gather(*(fetch(p) for p in range(4)))
    print(fetch.__name__, f"{time.perf_counter() - start:.1f}s")


asyncio.run(timed(bad_fetch))  # -> bad_fetch 2.0s   (4 x 0.5 s, in turn)
asyncio.run(timed(good_fetch))  # -> good_fetch 0.5s  (overlapped)

# ===== section: Check your understanding (predict first, then run) =====
# Check your understanding: four snippets. Predict, then run each main.
import asyncio
import time


# Question 1: six 1-second jobs through a Semaphore with 2 slots
async def job(n: int) -> int:
    await asyncio.sleep(1)
    return n


async def q1() -> None:
    sem = asyncio.Semaphore(2)

    async def limited(n: int) -> int:  # a coroutine defined inside q1
        async with sem:
            return await job(n)

    start = time.perf_counter()
    print(await asyncio.gather(*(limited(n) for n in range(6))))
    print(f"{time.perf_counter() - start:.1f}s")


# Question 2: what is x before and after await?
async def hello() -> str:
    return "hi"


async def q2() -> None:
    x = hello()
    print(x == "hi")
    print(await x == "hi")


# Question 3: finish order vs result order
async def worker(name: str, delay: float) -> str:
    await asyncio.sleep(delay)
    print("finished", name)
    return name


async def q3() -> None:
    print(await asyncio.gather(worker("a", 0.3), worker("b", 0.1)))


# Question 4: a task and a sleep at the same time
async def q4() -> None:
    start = time.perf_counter()
    t = asyncio.create_task(asyncio.sleep(1))
    await asyncio.sleep(1)
    await t
    print(f"{time.perf_counter() - start:.1f}s")


for question in (q1, q2, q3, q4):
    asyncio.run(question())
