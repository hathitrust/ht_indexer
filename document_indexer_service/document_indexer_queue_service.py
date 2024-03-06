# Read from a folder, index documents to solr and delete the content of the sercer

import argparse
import inspect
import os
import sys
import json

from ht_queue_service.queue_consumer import QueueConsumer
from ht_utils.ht_logger import get_ht_logger
from ht_indexer_api.ht_indexer_api import HTSolrAPI

logger = get_ht_logger(name=__name__)

current = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parent = os.path.dirname(current)
sys.path.insert(0, parent)

CHUNK_SIZE = 500
DOCUMENT_LOCAL_PATH = "/tmp/indexing_data/"


class DocumentIndexerQueueService:
    def __init__(self, solr_api_full_text: HTSolrAPI = None, queue_user: str = None, queue_password: str = None,
                 queue_host: str = None, queue_name: str = None):
        self.solr_api_full_text = solr_api_full_text
        # self.solr_api_full_text = solr_api_full_text
        self.queue_consumer = QueueConsumer(queue_user, queue_password, queue_host, queue_name, "retriever")

    def storage_document(self, json_object: dict = None):
        # xml_data = create_solr_string(json_object)
        # Call API
        response = self.solr_api_full_text.index_document(content_type="application/json", xml_data=json_object)
        return response


def main():
    parser = argparse.ArgumentParser()

    # Using queue or local machine
    queue_name = os.environ["QUEUE_NAME"]
    queue_host = os.environ["QUEUE_HOST"]
    queue_user = os.environ["QUEUE_USER"]
    queue_password = os.environ["QUEUE_PASS"]

    parser.add_argument(
        "--solr_indexing_api",
        help="",
        required=True,
        default="http://solr-lss-dev:8983/solr/#/core-x/",
    )

    # Path to the folder where the documents are stored. This parameter is useful for runing the script locally
    parser.add_argument(
        "--document_local_path",
        help="Path of the folder where the documents are stored.",
        required=False,
        default=None
    )

    args = parser.parse_args()

    solr_api_full_text = HTSolrAPI(url=args.solr_indexing_api)
    document_indexer_queue_service = DocumentIndexerQueueService(solr_api_full_text, queue_user, queue_password,
                                                                 queue_host,
                                                                 queue_name)

    # Get ten messages and break out
    for method_frame, properties, body in document_indexer_queue_service.queue_consumer.ht_channel.consume(
            'retriever_queue'):

        # Display the message parts
        print(method_frame)
        print(properties)

        message = json.loads(body.decode('utf-8'))
        print(message)

        try:
            response = document_indexer_queue_service.storage_document(json_object=message)
            logger.info(f"Index operation status: {response.status_code}")
        # print(message)
        except Exception as e:
            logger.info(f"Something went wrong with Solr {e}")

        # Acknowledge the message
        document_indexer_queue_service.queue_consumer.ht_channel.basic_ack(method_frame.delivery_tag)

        # Escape out of the loop after 10 messages
        if method_frame.delivery_tag == 10:
            break

    # Cancel the consumer and return any pending messages
    requeued_messages = document_indexer_queue_service.queue_consumer.ht_channel.cancel()
    print('Requeued %i messages' % requeued_messages)

    # while True:
    #    try:

    #        logger.info(' [*] Waiting for messages. To exit press CTRL+C')
    #        document_indexer_queue_service.queue_consumer.consume_message()
    #        logger.info("Indexing documents")

    #        message = document_indexer_queue_service.queue_consumer.ht_channel.start_consuming()
    #

    #    logger.info("Processing ended, sleeping for 5 minutes")
    #    sleep(3)

    # Close the channel and the connection
    document_indexer_queue_service.queue_consumer.ht_channel.close()
    document_indexer_queue_service.queue_consumer.queue_connection.close()


if __name__ == "__main__":
    main()
