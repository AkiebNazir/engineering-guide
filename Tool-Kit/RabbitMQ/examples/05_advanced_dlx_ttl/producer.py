import pika

credentials = pika.PlainCredentials('user', 'password')
connection = pika.BlockingConnection(pika.ConnectionParameters('localhost', credentials=credentials))
channel = connection.channel()

# Declare the DLX
channel.exchange_declare(exchange='dlx', exchange_type='direct')

# Declare the DLQ and bind it to DLX
channel.queue_declare(queue='dlq')
channel.queue_bind(queue='dlq', exchange='dlx', routing_key='dlx_routing_key')

# Declare the main queue with TTL and DLX arguments
args = {
    'x-message-ttl': 3000, # 3 seconds
    'x-dead-letter-exchange': 'dlx',
    'x-dead-letter-routing-key': 'dlx_routing_key'
}
channel.queue_declare(queue='main_queue', arguments=args)

channel.basic_publish(exchange='', routing_key='main_queue', body='This message will expire in 3 seconds')
print(" [x] Sent message with 3s TTL")

connection.close()
