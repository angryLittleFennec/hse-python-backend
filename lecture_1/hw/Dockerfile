FROM python:3.12 AS base

COPY math_plain_asgi.py ./math_plain_asgi.py

RUN python3 -m pip install uvicorn
RUN python3 -m pip install prometheus-client

CMD ["uvicorn", "math_plain_asgi:app", "--host", "0.0.0.0", "--port", "80"]