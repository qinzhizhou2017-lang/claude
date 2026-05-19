#!/usr/bin/env python3
"""stocki-financial-reader diagnose: 2-check connectivity smoke test.

[1/2] Reachability   GET $STOCKI_GATEWAY_URL/api/v3/market/status?area=all (10s)
[2/2] Auth + read    POST /api/v3/quotes/get_latest_quotes for 600519
                     verify response contains `symbol` and `close` fields

Exit codes: 0 success / 1 auth / 2 unreachable / 3 unavailable / 4 rate.
stdlib-only.
"""

import json
import os
import sys
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

SAMPLE_SYMBOL = "600519"   # Kweichow Moutai (cn:stock); stable + always-trading
EXPECTED_FIELDS = ("symbol", "close")


def check_reachability(base, key, timeout=10):
    url = f"{base.rstrip('/')}/api/v3/market/status?area=all"
    req = Request(url, headers={"Authorization": f"Bearer {key}"}, method="GET")
    try:
        with urlopen(req, timeout=timeout) as resp:
            resp.read()
            return True, "200 OK"
    except HTTPError as e:
        if e.code == 401:
            return False, ("auth_invalid", "401 from gateway")
        if e.code == 429:
            return False, ("rate_limited", "429 from gateway")
        if e.code >= 500:
            return False, ("stocki_unavailable", f"HTTP {e.code}")
        return False, ("unknown", f"HTTP {e.code}")
    except (URLError, TimeoutError, OSError) as e:
        return False, ("unreachable", str(e))


def check_auth_read(base, key, timeout=15):
    url = f"{base.rstrip('/')}/api/v3/quotes/get_latest_quotes"
    body = json.dumps({
        "assets": [{"symbols": [SAMPLE_SYMBOL], "area": "cn", "asset_type": "stock"}],
        "include_fundamentals": False,
        "timeout": 5.0,
    }).encode("utf-8")
    req = Request(
        url,
        data=body,
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except HTTPError as e:
        if e.code == 401:
            return False, ("auth_invalid", "401")
        if e.code == 429:
            return False, ("rate_limited", "429")
        if e.code >= 500:
            return False, ("stocki_unavailable", f"HTTP {e.code}")
        return False, ("unknown", f"HTTP {e.code}")
    except (URLError, TimeoutError, OSError) as e:
        return False, ("unreachable", str(e))

    records = data.get("data") or []
    if not records:
        return False, ("shape_invalid", "response.data empty")
    sample = records[0]
    missing = [f for f in EXPECTED_FIELDS if f not in sample]
    if missing:
        return False, ("shape_invalid", f"missing fields: {missing}")
    return True, f"{SAMPLE_SYMBOL} -> symbol+close"


def main():
    print("stocki-financial-reader Diagnose")
    print("=" * 48)
    base = os.environ.get("STOCKI_GATEWAY_URL", "")
    key = os.environ.get("STOCKI_API_KEY", "")
    if not base or not key:
        print("[ERROR] STOCKI_GATEWAY_URL or STOCKI_API_KEY missing", file=sys.stderr)
        sys.exit(1)

    passed = 0
    error_class = None

    # 1/2 Reachability
    ok, info = check_reachability(base, key)
    if ok:
        print(f"[1/2] Reachability   OK    {info}")
        passed += 1
    else:
        cls, detail = info
        print(f"[1/2] Reachability   FAIL  {cls}: {detail}")
        error_class = cls

    # 2/2 Auth + read (only if reachable)
    if ok:
        ok2, info2 = check_auth_read(base, key)
        if ok2:
            print(f"[2/2] Auth + read    OK    {info2}")
            passed += 1
        else:
            cls, detail = info2
            print(f"[2/2] Auth + read    FAIL  {cls}: {detail}")
            error_class = cls
    else:
        print("[2/2] Auth + read    SKIP  (reachability failed)")

    print("=" * 48)
    print(f"Result: {passed}/2 passed")

    code_map = {
        "auth_invalid": 1,
        "unreachable": 2,
        "stocki_unavailable": 3,
        "rate_limited": 4,
        "unknown": 3,        # unrecognized upstream 4xx → treat as service-side anomaly, not auth (review I-2)
        "shape_invalid": 3,  # response missing expected fields → upstream contract drift, same class
    }
    sys.exit(code_map.get(error_class, 0 if passed == 2 else 1))


if __name__ == "__main__":
    main()
