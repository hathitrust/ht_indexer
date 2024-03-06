# producer
import json

import pika
import ssl
from pika.exceptions import ConnectionClosedByBroker, AMQPConnectionError

from ht_utils.ht_logger import get_ht_logger

logger = get_ht_logger(name=__name__)


# queue_name
# channel_name
# create connection

# Create a class to sent messages to a rabbitMQ
def ht_queue_connection(queue_connection: pika.BlockingConnection,
                        ht_channel_name: str, queue_name: str):
    # queue a name is important when you want to share the queue between producers and consumers
    ht_channel = queue_connection.channel()

    # exchange - this can be assumed as a bridge name which needed to be declared so that queues can be accessed
    ht_channel.exchange_declare(ht_channel_name, durable=True, exchange_type="topic")

    # Check if the queue exist
    ht_channel.queue_declare(queue=queue_name, durable=True)

    # Tell the exchange to send messages to our queue.
    # The relationship between exchange and a queue is called a binding.
    ht_channel.queue_bind(exchange=ht_channel_name, queue=queue_name, routing_key=queue_name)
    return ht_channel


class QueueProducer:

    def __init__(self, user: str, password: str, host: str, queue_name: str, channel_name: str):
        # Define credentials (user/password) as environment variables
        # declaring the credentials needed for connection like host, port, username, password, exchange etc
        self.credentials = pika.PlainCredentials(username=user, password=password)

        self.host = host
        self.queue_name = queue_name
        self.channel_name = channel_name

        self.queue_connection = pika.BlockingConnection(pika.ConnectionParameters(host=self.host,
                                                                                  credentials=self.credentials))
        self.ht_channel = ht_queue_connection(self.queue_connection, self.channel_name, self.queue_name)

    def publish_messages(self, queue_message: bytes) -> None:

        print(type(json.dumps(queue_message)))
        print(queue_message)
        logger.info(f"Sending message to queue {queue_message}")
        while True:
            try:
                # method used which we call to send message to specific queue
                # Do we need to create a new exchange our we could use the default
                # routing_key is the name of the queue
                self.ht_channel.basic_publish(exchange=self.channel_name,
                                              routing_key=self.queue_name,
                                              body=json.dumps(queue_message))
                self.ht_channel.close()
                break
            except (ConnectionClosedByBroker, AMQPConnectionError, ssl.SSLEOFError) as err:
                logger.error('Could not publish message to RabbitMQ: %s', err)
            # Reconnect to RabbitMQ
            self.queue_connection = pika.BlockingConnection(pika.ConnectionParameters(host=self.host,
                                                                                      credentials=self.credentials))
            self.ht_channel = ht_queue_connection(self.queue_connection, self.channel_name, self.queue_name)
            self.ht_channel.queue_declare(queue=self.queue_name, durable=True)

# channel.close()
