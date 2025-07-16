import redis
import os


r = redis.Redis.from_url("rediss://default:ASkwAAIjcDFiOWRiYmRmZTQ2YTM0YWRjYTE4MmE3OTkxMDQzNjYzMnAxMA@worthy-cat-10544.upstash.io:6379")

r.set('foo', 'bar')
value = r.get('foo')