import time
import os
import argparse
import json

from document_generator.full_text_document_generator import DocumentGenerator
from ht_document.ht_document import HtDocument
from document_generator.generator_arguments import GeneratorServiceArguments
from ht_queue_service.queue_consumer import QueueConsumer, positive_acknowledge, reject_message
from ht_queue_service.queue_producer import QueueProducer

from ht_utils.ht_logger import get_ht_logger

logger = get_ht_logger(name=__name__)


class DocumentGeneratorService:
    def __init__(self, db_conn, src_queue_consumer: QueueConsumer,
                 tgt_queue_producer: QueueProducer,
                 document_repository: str = None,
                 not_required_tgt_queue: bool = False
                 ):

        """
        This class is responsible to retrieve from the queue a message with metadata at item level and generate
        the full text search entry and publish the document in a queue

        :param db_conn: Mysql connection
        :param src_queue_consumer: Connection of the queue to read the messages
        :param tgt_queue_producer: Connection of the queue to publish the messages
        :param not_required_tgt_queue: Parameter to define if the generated documents will be published in a queue
        :param document_repository: Parameter to know if the plain text of the items is in the local or remote
        repository
        """

        self.document_generator = DocumentGenerator(db_conn)

        self.src_queue_consumer = src_queue_consumer

        self.document_repository = document_repository

        if not not_required_tgt_queue:
            self.tgt_queue_producer = tgt_queue_producer

    def generate_full_text_entry(self, item_id: str, record: dict, document_repository: str):

        start_time = time.time()
        logger.info(f"Generating document {item_id}")

        # Instantiate each document
        ht_document = HtDocument(document_id=item_id, document_repository=document_repository)

        logger.info(f"Checking path {ht_document.source_path}")

        # TODO: Temporal local for testing using a sample of files
        #  Checking if the file exist, otherwise go to the next
        if os.path.isfile(f"{ht_document.source_path}.zip"):
            logger.info(f"Processing item {ht_document.document_id}")
            # try:
            entry = self.document_generator.make_full_text_search_document(ht_document, record)
            # except Exception as e:
            #    raise Exception(f"Document {ht_document.document_id} could not be generated: Error - {e}")
            if not entry:
                raise Exception(f"Document {ht_document.document_id} could not be generated")
            logger.info(
                f"Time to generate full-text search {ht_document.document_id} document {time.time() - start_time:.10f}")
        else:
            logger.info(f"{ht_document.document_id} does not exist")

        return entry

    def publish_document(self, content: dict = None):
        """
        Publish the document in a queue
        """
        message = content
        logger.info(f"Sending message to queue {content.get('id')}")
        self.tgt_queue_producer.publish_messages(message)

    def generate_document(self):

        for method_frame, properties, body in self.src_queue_consumer.consume_message():

            # TODO: Return the message to the queue if the process fails for any reason, for example,
            #  if the document does not exist
            try:
                message = json.loads(body.decode('utf-8'))

                item_id = message.get("ht_id")

                full_text_document = self.generate_full_text_entry(item_id, message, self.document_repository)

                try:
                    self.publish_document(full_text_document)
                    # Acknowledge the message to src_queue if the message is processed successfully and published in
                    # the other queue
                    positive_acknowledge(self.src_queue_consumer.conn.ht_channel,
                                         method_frame.delivery_tag)
                except Exception as e:
                    logger.error(f"Something wrong sending {item_id} to the queue {e}")
                    reject_message(self.src_queue_consumer.conn.ht_channel,
                                   method_frame.delivery_tag, requeue_message=False)
                    continue
            except Exception as e:
                logger.error(f"Document {item_id} failed {e}")
                reject_message(self.src_queue_consumer.conn.ht_channel,
                               method_frame.delivery_tag, requeue_message=False)
                continue


def main():
    parser = argparse.ArgumentParser()
    init_args_obj = GeneratorServiceArguments(parser)

    document_generator_service = DocumentGeneratorService(init_args_obj.db_conn,
                                                          init_args_obj.src_queue_consumer,
                                                          init_args_obj.tgt_queue_producer,
                                                          init_args_obj.document_repository,
                                                          not_required_tgt_queue=init_args_obj.not_required_tgt_queue
                                                          )
    document_generator_service.generate_document()


if __name__ == "__main__":
    main()
