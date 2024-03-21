# producer
import json

import pika

from ht_queue_service import ht_queue_connection
from ht_utils.ht_logger import get_ht_logger

logger = get_ht_logger(name=__name__)


class QueueProducer:
    """ Create a class to sent messages to a rabbitMQ """

    def __init__(self, user: str, password: str, host: str, queue_name: str, channel_name: str):
        # Define credentials (user/password) as environment variables
        # declaring the credentials needed for connection like host, port, username, password, exchange etc
        self.credentials = pika.PlainCredentials(username=user, password=password)

        self.host = host
        self.queue_name = queue_name
        self.channel_name = channel_name

        # Open a connection to RabbitMQ
        self.queue_connection = pika.BlockingConnection(pika.ConnectionParameters(host=self.host,
                                                                                  credentials=self.credentials))
        self.ht_channel = ht_queue_connection(self.queue_connection, self.channel_name, self.queue_name)

    def queue_reconnect(self):
        # Reconnect to RabbitMQ
        self.queue_connection = pika.BlockingConnection(pika.ConnectionParameters(host=self.host,
                                                                                  credentials=self.credentials))
        self.ht_channel = ht_queue_connection(self.queue_connection, self.channel_name, self.queue_name)
        self.ht_channel.queue_declare(queue=self.queue_name, durable=True)

    def publish_messages(self, queue_message: dict) -> None:

        logger.info(f"Sending message to queue {self.queue_name}")
        try:
            # method used which we call to send message to specific queue
            # Do we need to create a new exchange our we could use the default
            # routing_key is the name of the queue
            self.ht_channel.basic_publish(exchange=self.channel_name,
                                          routing_key=self.queue_name,
                                          body=json.dumps(queue_message),
                                          # properties=pika.BasicProperties(delivery_mode=2,  # make message persistent
                                          #                                ), mandatory=True
                                          )
            # self.ht_channel.close()
            logger.info("Message was confirmed in the queue")
            # break
        # TODO - Add a better exception handling
        # pika.exceptions.ChannelWrongStateError add the method on_open_callback to check if the channel is oppened
        # https://github.com/pika/pika/issues/1240
        # pika examples: https://github.com/pika/pika/blob/main/examples/asynchronous_publisher_example.py
        except Exception as err:
            e_name = type(err).__name__
            logger.debug(f"Message {queue_message.get('ht_id')} could not be confirmed: exception = {e_name} e = {err}")
            logger.debug('Trying to reconnect to RabbitMQ in 5 seconds: %s', err)
            # logger.error('Could not publish message to RabbitMQ: %s', err)
            # time.sleep(5)
            # self.queue_reconnect()
        finally:
            if self.queue_connection:
                self.queue_connection.close()
                logger.info("Connection to RabbitMQ closed")
        self.queue_reconnect()
