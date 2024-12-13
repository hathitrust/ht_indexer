from prometheus_client import Counter

REQUEST_COUNT = Counter('my_app_requests_total', 'Total number of requests')

from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator

app = FastAPI()

@app.get("/")
def read_root():
    return {"Hello": "World"}

Instrumentator().instrument(app).expose(app)


def handle_request():
    REQUEST_COUNT.inc()
    # ... rest of your request handling logic

if __name__ == '__main__':
    #start_http_server(8000)  # Expose metrics on port 8000
    # ... rest of your application startup logic
    pass