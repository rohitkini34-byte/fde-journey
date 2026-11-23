"""A fake headless CMS for Day 30 (given: you do not need to change this).

It behaves like a small Contentstack-style Delivery API, but runs inside your
test process through httpx.MockTransport, so no network or account is needed.

    GET /v3/content_types/{content_type}/entries?limit=N[&cursor=C]
    header  access_token: <token>
    200 ->  {"items": [...up to N raw entries...], "next_cursor": "c2" | null}

Extra switches let tests script trouble: fail the first few calls with a
status code (503, 429 ...) or a timeout, or return a broken cursor.
"""

import httpx


class FakeCMS:
    """Holds the fake data and records every request it receives."""

    def __init__(
        self,
        items: list[dict],
        token: str = "test-token",
        fail_first: int = 0,
        fail_status: int = 503,
        retry_after: str | None = None,
        timeout_first: int = 0,
        loop_cursor: bool = False,
    ) -> None:
        self.items = items
        self.token = token
        self.fail_first = fail_first  # how many calls fail with fail_status
        self.fail_status = fail_status
        self.retry_after = retry_after  # value of the Retry-After header
        self.timeout_first = timeout_first  # how many calls time out first
        self.loop_cursor = loop_cursor  # True: always send next_cursor "c0"
        self.requests: list[httpx.Request] = []  # every request, in order

    # MockTransport calls this once per request the client sends
    def handle(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        n = len(self.requests)  # 1 for the first call, 2 for the second ...

        if n <= self.timeout_first:
            raise httpx.ReadTimeout("fake timeout", request=request)
        if n <= self.timeout_first + self.fail_first:
            headers = {}
            if self.retry_after is not None:
                headers["Retry-After"] = self.retry_after
            return httpx.Response(self.fail_status, headers=headers,
                                  json={"error": "try again later"})

        if request.headers.get("access_token") != self.token:
            return httpx.Response(401, json={"error": "invalid token"})

        parts = request.url.path.strip("/").split("/")
        # expected: ["v3", "content_types", "<type>", "entries"]
        if len(parts) != 4 or parts[1] != "content_types" \
                or parts[3] != "entries":
            return httpx.Response(404, json={"error": "no such route"})

        try:
            limit = int(request.url.params.get("limit", "100"))
        except ValueError:
            return httpx.Response(422, json={"error": "limit must be int"})
        if not 1 <= limit <= 100:
            return httpx.Response(422, json={"error": "limit 1..100"})

        cursor = request.url.params.get("cursor")
        if cursor is not None and not cursor.startswith("c"):
            return httpx.Response(422, json={"error": "bad cursor"})
        start = int(cursor[1:]) if cursor else 0

        page = self.items[start:start + limit]
        end = start + len(page)
        if self.loop_cursor:
            next_cursor = "c0"  # a buggy CMS that never ends
        else:
            next_cursor = f"c{end}" if end < len(self.items) else None
        return httpx.Response(200, json={"items": page,
                                         "next_cursor": next_cursor})

    @property
    def transport(self) -> httpx.MockTransport:
        """Pass this to httpx.Client(transport=...)."""
        return httpx.MockTransport(self.handle)
