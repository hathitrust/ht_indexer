# consumer

import pika
import json

from ht_queue_service import ht_queue_connection
from ht_utils.ht_logger import get_ht_logger

logger = get_ht_logger(name=__name__)


# os.environ['RABBITMQ_HOST'] = 'localhost'
# os.environ['RABBITMQ_PORT'] = '5672'
# os.environ['RABBITMQ_USERNAME'] = 'guest'
# os.environ['RABBITMQ_PASSWORD'] = 'guest'


# To get message from the queue you have to define a callback functions that is subscribed to a queue
#
# make a class to connect to the rabbitMQ
# create a channel
# create a queue
# create a callback function
# start consuming the queue
# create a thread to start consuming the queue

class QueueConsumer:
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

    def consume_message(self) -> dict:

        # TODO: Add a batch size parameter to limit the number of messages to be fetched. That is a usefull feature
        # if we want to add multiprocessing to the consumer to limit the number of messages for each worker
        # message_limit = total_messages

        try:
            for method_frame, properties, body in self.ht_channel.consume(self.queue_name,
                                                                          auto_ack=False,
                                                                          inactivity_timeout=3):

                if method_frame:
                    self.ht_channel.basic_ack(method_frame.delivery_tag)
                    output_message = json.loads(body.decode('utf-8'))
                    yield output_message
                else:
                    # Escape out of the loop when desired msgs are fetched
                    # TODO A different alternative to scape out the loop is
                    #  checking the delivery_tag for each message if method_frame.delivery_tag == total_messages:
                    # Cancel the consumer and return any pending messages
                    requeued_messages = self.ht_channel.cancel()
                    print('Requeued %i messages' % requeued_messages)
                    break
        except Exception as e:
            print(f'Connection Interrupted: {e}')

    def get_total_messages(self):
        # durable: Survive reboots of the broker
        # passive: Only check to see if the queue exists and raise `ChannelClosed` if it doesn't
        status = self.ht_channel.queue_declare(queue=self.queue_name, durable=True, passive=True)
        return status.method.message_count
