import pika
import sys, os

def main():
    credentials = pika.PlainCredentials('user', 'password')
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost', credentials=credentials))
    channel = connection.channel()

    channel.queue_declare(queue='dlq')

    def callback(ch, method, properties, body):
        print(f" [x] DLQ Received: {body.decode()}")

    channel.basic_consume(queue='dlq', on_message_callback=callback, auto_ack=True)

    print(' [*] Waiting for dead-letter messages. To exit press CTRL+C')
    channel.start_consuming()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('Interrupted')
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)
