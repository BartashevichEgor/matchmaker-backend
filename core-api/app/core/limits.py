import hashlib
import threading
import time
from collections import OrderedDict

from fastapi import HTTPException
from redis import Redis
from redis.exceptions import RedisError

from app.core.config import get_settings

_lock = threading.Lock()
_local = OrderedDict()
_redis = None


def redis_client():
    global _redis
    url = get_settings().redis_url
    if not url:
        return None
    if _redis is None:
        _redis = Redis.from_url(url, socket_connect_timeout=2, socket_timeout=2)
    return _redis


def limit(key: str, maximum: int, seconds: int):
    key = "matchmaker:limit:" + hashlib.sha256(key.encode()).hexdigest()
    client = redis_client()
    if client is not None:
        try:
            count = client.eval(
                "local n=redis.call('INCR',KEYS[1]); if n==1 then redis.call('EXPIRE',KEYS[1],ARGV[1]) end; return n",
                1,
                key,
                seconds,
            )
        except RedisError:
            raise HTTPException(503, "Rate limit service unavailable") from None
    else:
        with _lock:
            now = time.monotonic()
            count, expires = _local.get(key, (0, now + seconds))
            if expires <= now:
                count, expires = 0, now + seconds
            count += 1
            _local[key] = (count, expires)
            _local.move_to_end(key)
            while len(_local) > 10000:
                _local.popitem(last=False)
    if count > maximum:
        raise HTTPException(429, "Too many requests. Try later.", headers={"Retry-After": str(seconds)})
