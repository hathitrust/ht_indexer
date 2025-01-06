"""
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

"""

import http.server
from prometheus_client import start_http_server, push_to_gateway
from prometheus_client import Counter
from ht_indexer_prometheus_app.ht_retriever_metrics import RETRIEVER_DOCUMENTS, RETRIEVER_PROCESSING_TIME
import requests
import time

# Create a metric to track the number of hello world requests
REQUESTS = Counter('hello_worlds_total', 'Hello Worlds requested.')

class MyHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        REQUESTS.inc() # The inc method increments the counter by 1
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Hello World")

    #def scrape_document_retriever_metrics(self):
    #    try:
    #        run_retriever_service_by_file.main()
    #    except Exception as e:
    #        print(f"Error: {e}")


def scrape_metrics():
    try:
        response = requests.get('http://localhost:8000/metrics')
        if response.status_code == 200:
            for line in response.text.splitlines():
                if line.startswith('documents_retriever_total'):
                    RETRIEVER_DOCUMENTS.set(float(line.split()[-1]))
                elif line.startswith('document_retriever_seconds'):
                    RETRIEVER_PROCESSING_TIME.set(float(line.split()[-1]))
    except Exception as e:
        print(f"Error scraping metrics: {e}")

def ht_push_to_gateway(registry, job='hello_world', grouping_key={'instance': 'hello_world'}):
    try:
        push_to_gateway('prometheus_pushgateway:9091', job=job, registry=registry, grouping_key=grouping_key)
    except Exception as e:
        print(f"Error pushing to gateway: {e}")

if __name__ == "__main__":
    start_http_server(8000)
    server = http.server.HTTPServer(('localhost', 8001), MyHandler)
    while True:
        server.handle_request()
        scrape_metrics()
        time.sleep(10)
    #server.serve_forever()