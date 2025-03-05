import pytest
import time

from ht_queue_service.queue_connection import QueueConnection
from ht_queue_service.queue_multiple_consumer import QueueMultipleConsumer, positive_acknowledge

from ht_utils.ht_logger import get_ht_logger

logger = get_ht_logger(name=__name__)

class TestHTMultipleConsumerServiceConcrete(QueueMultipleConsumer):

    def __init__(self, user: str, password: str, host: str, queue_name: str, requeue_message: bool = False,
                 batch_size: int = 1, shutdown_on_empty_queue: bool = True):
        super().__init__(user, password, host, queue_name, requeue_message, batch_size)
        self.consume_one_message = None
        self.shutdown_on_empty_queue = shutdown_on_empty_queue

    def process_batch(self):

        start_time = time.time()
        try:
            list_id = [doc.get("ht_id") for doc in self.batch]
            received_messages = self.batch.copy()
            if "5" in list_id:
                try:
                    print(1 / 0)
                except Exception as e:
                    logger.error(f"Error in indexing document: {e}")
                    raise e

            # Acknowledge the message if the message is processed successfully
            for tag in self.delivery_tags:
                positive_acknowledge(self.conn.ht_channel, tag)
            self.consume_one_message = received_messages
        except Exception as e:
                logger.info(
                    f"Message failed with error: {e}")
                failed_messages = self.batch.copy()
                failed_messages_tags = self.delivery_tags.copy()

                # Reject the message
                for delivery_tag in failed_messages_tags:
                    self.reject_message(self.conn.ht_channel, delivery_tag)
                current_time = time.time()
                logger.info(f"Time to process the batch: {current_time - start_time}")

        # Stop consuming if the flag is set
        if self.shutdown_on_empty_queue and self.conn.get_total_messages() == 0:
            logger.info("Stopping consumer...")
            self.conn.ht_channel.stop_consuming()



@pytest.fixture
def one_message():
    """
    This function is used to create a message
    """
    message = {"ht_id": "1234", "ht_title": "Hello World", "ht_author": "John Doe"}
    return message


@pytest.fixture
def list_messages():
    """
    This function is used to create a list of messages
    """

    messages = []
    for i in range(10):
        messages.append({"ht_id": f"{i}", "ht_title": f"Hello World {i}", "ht_author": f"John Doe {i}"})
    return messages

@pytest.fixture
def multiple_consumer_instance():
    return TestHTMultipleConsumerServiceConcrete(user="guest", password="guest", host="localhost",
                                                 queue_name="test_producer_queue", requeue_message=False, batch_size=1)

@pytest.fixture
def multiple_consumer_instance_requeueTrue_sizeN():
    return TestHTMultipleConsumerServiceConcrete(user="guest", password="guest", host="localhost",
                                                 queue_name="test_producer_queue", requeue_message=True, batch_size=10)

@pytest.fixture
def multiple_consumer_instance_requeueFalse_sizeN():
    return TestHTMultipleConsumerServiceConcrete(user="guest", password="guest", host="localhost",
                                                 queue_name="test_producer_queue", requeue_message=False, batch_size=10)

@pytest.fixture
def populate_queue(list_messages, producer_instance, multiple_consumer_instance_requeueFalse_sizeN, retriever_parameters):
    """ Test for re-queueing a message from the queue, an error is raised, and the message is routed
            to the dead letter queue and discarded from the main queue"""

    # Clean up the queue
    multiple_consumer_instance_requeueFalse_sizeN.conn.ht_channel.queue_purge(multiple_consumer_instance_requeueFalse_sizeN.queue_name)

    for message in list_messages:
        # Publish the message
        producer_instance.publish_messages(message)

    multiple_consumer_instance_requeueFalse_sizeN.start_consuming()

@pytest.fixture
def populate_queue_requeueTrue(list_messages, producer_instance, multiple_consumer_instance_requeueTrue_sizeN, retriever_parameters):
    """ Test for re-queueing a message from the queue, an error is raised, and the message is routed
            to the dead letter queue and discarded from the main queue"""

    # Clean up the queue
    multiple_consumer_instance_requeueTrue_sizeN.conn.ht_channel.queue_purge(multiple_consumer_instance_requeueTrue_sizeN.queue_name)

    for message in list_messages:
        # Publish the message
        producer_instance.publish_messages(message)

    multiple_consumer_instance_requeueTrue_sizeN.start_consuming()

class TestHTMultipleConsumerService:

    @pytest.mark.parametrize("retriever_parameters", [{"user": "guest", "password": "guest", "host": "localhost",
                                                       "queue_name": "test_producer_queue",
                                                       "requeue_message": False,
                                                       "batch_size": 1}])
    def test_queue_consume_message(self, one_message, producer_instance, multiple_consumer_instance):
        """ Test for consuming a message from the queue
        One message is published and consumed, then at the end of the test the queue is empty
        """

        # Clean up the queue
        multiple_consumer_instance.conn.ht_channel.queue_purge(multiple_consumer_instance.queue_name)

        # Publish the message
        producer_instance.publish_messages(one_message)

        multiple_consumer_instance.start_consuming()

        output_message = multiple_consumer_instance.consume_one_message
        assert output_message[0] == one_message

        # Queue is empty
        assert 0 == multiple_consumer_instance.conn.get_total_messages()

        multiple_consumer_instance.conn.ht_channel.queue_purge(multiple_consumer_instance.queue_name)

    def test_queue_consume_message_empty(self, multiple_consumer_instance):
        """ Test for consuming a message from an empty queue"""

        # Clean up the queue
        multiple_consumer_instance.conn.ht_channel.queue_purge(multiple_consumer_instance.queue_name)

        assert 0 == multiple_consumer_instance.conn.get_total_messages()
        multiple_consumer_instance.conn.ht_channel.queue_purge(multiple_consumer_instance.queue_name)

    @pytest.mark.parametrize("retriever_parameters",
                             [{"user": "guest", "password": "guest", "host": "localhost",
                               "queue_name": "test_producer_queue",
                               "requeue_message": False, "batch_size": 10}])
    def test_queue_requeue_message_requeue_false(self, populate_queue, multiple_consumer_instance_requeueFalse_sizeN):
        """ Test for re-queueing a message from the queue, an error is raised, and the message is routed
        to the dead letter queue and discarded from the main queue"""

        check_queue = QueueConnection("guest", "guest", "localhost",
                                      "test_producer_queue_dead_letter_queue")

        assert 0 == multiple_consumer_instance_requeueFalse_sizeN.conn.get_total_messages()
        # All the messages are back into the dead letter queue
        assert 10 == check_queue.get_total_messages()

        check_queue.ht_channel.queue_purge(check_queue.queue_name)

    @pytest.mark.parametrize("retriever_parameters",
                             [{"user": "guest", "password": "guest", "host": "localhost",
                               "queue_name": "test_producer_queue",
                               "requeue_message": True, "batch_size": 1}])
    def test_queue_requeue_message_requeue_true(self, populate_queue_requeueTrue, multiple_consumer_instance_requeueTrue_sizeN):
        """ Test for re-queueing a message from the queue, an error is raised, and instead of routing the message
        to the dead letter queue, it is requeue to the main queue """

        check_queue = QueueConnection("guest", "guest", "localhost",
                                      "test_producer_queue_dead_letter_queue", batch_size=1)

        assert multiple_consumer_instance_requeueTrue_sizeN.conn.get_total_messages() > 0
        assert 0 == check_queue.get_total_messages()

        check_queue.ht_channel.queue_purge(check_queue.queue_name)
        multiple_consumer_instance_requeueTrue_sizeN.conn.ht_channel.queue_purge(multiple_consumer_instance_requeueTrue_sizeN.queue_name)



