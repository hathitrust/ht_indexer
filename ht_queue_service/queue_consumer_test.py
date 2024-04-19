import json
import pytest

from ht_queue_service.queue_consumer import QueueConsumer, positive_acknowledge, reject_message
from ht_queue_service.queue_producer import QueueProducer

from ht_utils.ht_logger import get_ht_logger

logger = get_ht_logger(name=__name__)


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
    This function is used to create a message
    """

    messages = []
    for i in range(10):
        messages.append({"ht_id": f"{i}", "ht_title": f"Hello World {i}", "ht_author": f"John Doe {i}"})
    return messages


@pytest.fixture
def producer_instance():
    """
    This function is used to generate a message
    """
    # Instantiate the producer
    ht_producer = QueueProducer("guest",
                                "guest",
                                "rabbitmq",
                                "test_producer_queue")

    return ht_producer


@pytest.fixture
def consumer_instance():
    """
    This function is used to generate a message
    """
    # Instantiate the consumer
    ht_consumer = QueueConsumer("guest",
                                "guest",
                                "rabbitmq",
                                "test_producer_queue")
    return ht_consumer


class TestHTConsumerService:
    def test_queue_consume_message(self, one_message, consumer_instance, producer_instance):
        """ Test for consuming a message from the queue"""

        # Clean up the queue
        consumer_instance.conn.ht_channel.queue_purge(consumer_instance.queue_name)

        # Publish the message
        producer_instance.publish_messages(one_message)

        for method_frame, properties, body in consumer_instance.consume_message(inactivity_timeout=1):
            output_message = json.loads(body.decode('utf-8'))
            assert output_message == one_message
            break

        assert 0 == consumer_instance.get_total_messages()

    def test_queue_consume_message_empty(self, consumer_instance):
        """ Test for consuming a message from an empty queue"""

        # Clean up the queue
        consumer_instance.conn.ht_channel.queue_purge(consumer_instance.queue_name)

        assert 0 == consumer_instance.get_total_messages()

    def test_queue_requeue_message(self, list_messages, consumer_instance, producer_instance):

        # Clean up the queue
        consumer_instance.conn.ht_channel.queue_purge(consumer_instance.queue_name)

        for message in list_messages:
            # Publish the message
            producer_instance.publish_messages(message)

        for method_frame, properties, body in consumer_instance.consume_message(inactivity_timeout=3):
            if method_frame:
                try:
                    # Process the message
                    output_message = json.loads(body.decode('utf-8'))

                    # Use the message to raise an exception
                    if output_message.get("ht_id") == "5":
                        # This will raise an exception
                        logger.info(f"Message {output_message.get('ht_id')} processed successfully {1 / 0}")
                    # Acknowledge the message if the message is processed successfully
                    positive_acknowledge(consumer_instance.conn.ht_channel, method_frame.delivery_tag)
                except Exception as e:
                    logger.info(
                        f"Message {method_frame.delivery_tag} re-queued to {consumer_instance.queue_name} "
                        f"with error: {e}")
                    # Reject the message
                    reject_message(consumer_instance.conn.ht_channel, method_frame.delivery_tag)
            else:
                logger.info("Empty queue: Test ended")
                break
