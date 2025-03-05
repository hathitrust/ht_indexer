# consumer
from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor

from ht_queue_service.queue_connection_dead_letter import QueueConnectionDeadLetter
from ht_utils.ht_logger import get_ht_logger
import json

logger = get_ht_logger(name=__name__)


def positive_acknowledge(used_channel, delivery_tag):
    used_channel.basic_ack(delivery_tag=delivery_tag)

class QueueMultipleConsumer(ABC):
    def __init__(self, user: str, password: str, host: str, queue_name: str,
                 requeue_message: bool = False, batch_size: int = 1):

        """
        This class is used to consume a batch of messages from the queue
        :param user: username for the RabbitMQ
        :param password: password for the RabbitMQ
        :param host: host for the RabbitMQ
        :param queue_name: name of the queue
        :param requeue_message: boolean to requeue the message to the queue
        :param batch_size: size of the batch to be consumed
        """

        # Credentials (user/password) are defined as environment variables
        # declaring the credentials needed for connection like host, port, username, password, exchange etc.
        self.user = user
        self.host = host
        self.queue_name = queue_name
        self.password = password
        self.requeue_message = requeue_message
        self.batch_size = batch_size
        self.batch = [] # It stores messages for batch processing
        self.delivery_tags = [] # It stores delivery tags for acknowledging messages
        self.executor = ThreadPoolExecutor(max_workers=batch_size)

        try:
            self.conn = QueueConnectionDeadLetter(self.user, self.password, self.host, self.queue_name, batch_size)
        except Exception as e:
            raise e

    def process_message(self, message: dict):
        """Abstract method for processing one message. Must be implemented by subclasses."""
        if "error" in message:
            raise Exception(message["error"])
        logger.info(f"Processing message: {message}")

    @abstractmethod
    def process_batch(self):
        """ Abstract method for processing a batch of messages. Must be implemented by subclasses.

        Seudo code: Process the batch of messages.
        If the processing is successful, acknowledge all the messages in the batch.
        If the processing fails, requeue all the failed messages to the Dead Letter Queue.
        Clear the batch and the delivery tags lists.
        """
        pass

    def _callback(self, ch, method, properties, body):
        """Internal callback function that collects messages into batches."""

        self.batch.append(json.loads(body))
        self.delivery_tags.append(method.delivery_tag)

        # Process the batch if it reaches the desired size
        if len(self.batch) >= self.batch_size:
            self.process_batch()

        # TODO - Implement the logic to stop consuming messages if the queue is empty
        #if self.shutdown_on_empty_queue and self.conn.get_total_messages() == 0:
        #    logger.info("Stopping consumer...")
        #    self.conn.ht_channel.stop_consuming()

    def start_consuming(self):
        """Starts consuming messages from the queue."""
        self.conn.ht_channel.basic_consume(queue=self.queue_name, on_message_callback=self._callback, auto_ack=False)
        logger.info(f"[*] Waiting for messages on {self.queue_name}...")

        try:
            self.conn.ht_channel.start_consuming()
        except Exception as e:
            logger.error(f"Something went wrong while consuming messages. {e}")

        if self.batch:
            self.process_batch()  # Process the remaining messages in the batch

    def reject_message(self, used_channel, basic_deliver):
        used_channel.basic_reject(delivery_tag=basic_deliver, requeue=self.requeue_message)

    def stop(self):
        """Stop consuming messages
        Use this function for testing purposes only.
        """
        logger.info("Time's up! Stopping consumer...")
        shutdown_on_empty_queue = True
        self.conn.ht_channel.close()




