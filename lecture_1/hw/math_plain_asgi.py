import asyncio
from typing import Any, Awaitable, Callable

import math
import json
from urllib.parse import parse_qsl

from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST, push_to_gateway

import uvicorn


REQUEST_COUNT = Counter("app_request_count", "Total number of requests")
METRICS_COUNT = Counter("metrics_request_count", "Num of metrics requests")
FACTORIAL_COUNT = Counter("factorial_request_count", "Num of factorial requests")
FIBONACCI_COUNT = Counter("fibonacci_request_count", "Num of fibonacci requests")
MEAN_COUNT = Counter("min_request_count", "Num of min requests")


PUSHGATEWAY_URL = "http://localhost:9091"
BAD_REQUEST = "Bad request"
NOT_FOUND = "Not found"
UNPROCESSABLE_ENTITY = 'Unprocessable entity'

def push_metrics():
    push_to_gateway(PUSHGATEWAY_URL, job='my_asgi_app', registry=None) 


async def app(scope, receive, send):
    REQUEST_COUNT.inc()
    
    if scope['type'] == 'http' and scope['method'] == 'GET':
        path = scope['path']
        if path == '/factorial':
            await factorial(scope, send)
            FACTORIAL_COUNT.inc()
            return
        elif path.startswith('/fibonacci'):
            FIBONACCI_COUNT.inc()
            await fibonacci(scope, send)
            return
        elif path.startswith('/mean'):
            MEAN_COUNT.inc()
            await mean(receive, send)
            return
        elif path == '/metrics':
            METRICS_COUNT.inc()
            await metrics(send)
            return
 
    await send_error(send=send, status_code=404, error_message=NOT_FOUND)


async def metrics(send):
    await send({
        'type': 'http.response.start',
        'status': 200,
        'headers': [(b'content-type', CONTENT_TYPE_LATEST.encode())],
    })
    await send({
        'type': 'http.response.body',
        'body': generate_latest(),
    })


async def factorial(scope, send):
    try:
        query_dict = dict(parse_qsl(scope['query_string'].decode()))
        
        n = int(query_dict['n'])
        if n < 0:
            await send_error(send=send, status_code=400,error_message=BAD_REQUEST)
            return
        
        await send_json_answer(send=send, answer={"result" : math.factorial(n)})
    except (ValueError, KeyError):
        await send_error(send=send, status_code=422, error_message=UNPROCESSABLE_ENTITY)


async def fibonacci(scope, send):
    try:
        n = int(scope["path"].split("/")[2])
        if n < 0:
            await send_error(send=send, status_code=400, error_message=BAD_REQUEST)
            return

        a, b = 0, 1
        for _ in range(n):
            a, b = b, a + b
        await send_json_answer(send=send,answer={"result" : b})

    except (ValueError, IndexError):
        await send_error(send=send, status_code=422, error_message=UNPROCESSABLE_ENTITY)


async def mean(receive, send):
    try:
        message = await receive()
        body = message['body']
        body_data = json.loads(body.decode("utf-8"))
        if not isinstance(body_data, list) :
            await send_error(send=send, status_code=422, error_message=UNPROCESSABLE_ENTITY)
            return
        
        if not body_data or not all(isinstance(x, (int, float)) for x in body_data):
                await send_error(send=send, status_code=400, error_message=BAD_REQUEST)
                return
        
        await send_json_answer(send=send, answer={"result" : sum(body_data) / len(body_data)})
    except json.JSONDecodeError:
        await send_error(send=send, status_code=422,error_message=UNPROCESSABLE_ENTITY)



async def send_error(send, status_code, error_message):
    await send({
        'type': 'http.response.start',
        'status': status_code,
        'headers': [(b'content-type', b'plain/text')],
    })

    await send({
        'type': 'http.response.body',
        'body': error_message.encode(),
    })




async def send_json_answer(send, answer):
    await send({
        'type': 'http.response.start',
        'status': 200,
        'headers': [(b'content-type', b'application/json')],
    })

    await send({
        'type': 'http.response.body',
        'body': json.dumps(answer).encode(),
    })
