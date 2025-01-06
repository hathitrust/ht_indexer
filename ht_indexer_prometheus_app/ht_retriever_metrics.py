from prometheus_client import Counter, Histogram, CollectorRegistry

# Script to define the metrics for the retriever

# Create a registry for the metrics of document retriever
registry_retriever = CollectorRegistry()

# Define a counter for the number of documents processed
RETRIEVER_DOCUMENTS = Counter('documents_retriever_total',
                              'Total number of documents retrieved',
                              registry=registry_retriever)

# Define a histogram for the time taken to process documents
RETRIEVER_PROCESSING_TIME = Histogram('document_retriever_seconds',
                                      'Time taken to retrieve documents',
                                      registry=registry_retriever)
