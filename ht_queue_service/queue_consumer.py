# consumer


from ht_queue_service.queue_connection import QueueConnection
from ht_utils.ht_logger import get_ht_logger

logger = get_ht_logger(name=__name__)


def reject_message(used_channel, basic_deliver, requeue_message=False):
    used_channel.basic_reject(delivery_tag=basic_deliver, requeue=requeue_message)


def positive_acknowledge(used_channel, basic_deliver):
    used_channel.basic_ack(delivery_tag=basic_deliver)


class QueueConsumer:
    def __init__(self, user: str, password: str, host: str, queue_name: str, dead_letter_queue: bool = True):

        # Credentials (user/password) are defined as environment variables
        # declaring the credentials needed for connection like host, port, username, password, exchange etc
        self.user = user
        self.host = host
        self.queue_name = queue_name
        self.password = password
        self._is_interrupted = False

        self.conn = QueueConnection(self.user, self.password, self.host, self.queue_name,
                                    dead_letter_queue=dead_letter_queue)

    def queue_stop_consuming(self):
        """Stop consuming messages from the queue"""
        self._is_interrupted = True

    def consume_message(self, inactivity_timeout: int = None) -> dict:

        # Inactivity timeout is the time in seconds to wait for a message before returning None, the consumer will
        try:
            for method_frame, properties, body in self.conn.ht_channel.consume(self.queue_name,
                                                                               auto_ack=False,
                                                                               inactivity_timeout=inactivity_timeout
                                                                               ):
                if method_frame:
                    yield method_frame, properties, body
                else:
                    yield None, None, None
        # Todo: Add a better exception handling, check different parameters at RabbitMQ
        except Exception as e:
            logger.info(f'Connection Interrupted: {e}')

    def get_total_messages(self):
        # durable: Survive reboots of the broker
        # passive: Only check to see if the queue exists and raise `ChannelClosed` if it doesn't
        status = self.conn.ht_channel.queue_declare(queue=self.queue_name, durable=True, passive=True)
        return status.method.message_count
