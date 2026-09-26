import os
import shutil

base = "/Users/njasm/Njasm/AI/engineering-guide/Tool-Kit/RabbitMQ"
examples_py_dir = os.path.join(base, "examples")
examples_go_dir = os.path.join(base, "examples_go")

if os.path.exists(examples_py_dir):
    shutil.rmtree(examples_py_dir)
if os.path.exists(examples_go_dir):
    shutil.rmtree(examples_go_dir)

files = {}

# Python Examples
files["examples/01_basic_queue/README.md"] = '''
# 01 Basic Queue (Python)

**Goal:** Demonstrates the simplest form of RabbitMQ messaging with a single producer and consumer.
**Concepts:** Default exchange, named queue.
'''
files["examples/01_basic_queue/producer.py"] = '''
import pika
connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
channel = connection.channel()
channel.queue_declare(queue='hello')
channel.basic_publish(exchange='', routing_key='hello', body='Hello World!')
print(" [x] Sent 'Hello World!'")
connection.close()
'''
files["examples/01_basic_queue/consumer.py"] = '''
import pika, sys, os
def main():
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    channel = connection.channel()
    channel.queue_declare(queue='hello')
    def callback(ch, method, properties, body):
        print(f" [x] Received {body}")
    channel.basic_consume(queue='hello', on_message_callback=callback, auto_ack=True)
    print(' [*] Waiting for messages. To exit press CTRL+C')
    channel.start_consuming()
if __name__ == '__main__':
    main()
'''

files["examples/02_worker_queue/README.md"] = '''
# 02 Worker Queue (Python)

**Goal:** Distributes time-consuming tasks among multiple workers.
'''
files["examples/02_worker_queue/worker.py"] = '''print("Worker")'''
files["examples/02_worker_queue/new_task.py"] = '''print("Task")'''

files["examples/03_pubsub_fanout/README.md"] = '''# 03 PubSub Fanout (Python)'''
files["examples/03_pubsub_fanout/main.py"] = '''print("PubSub")'''

files["examples/04_routing_direct/README.md"] = '''# 04 Routing Direct (Python)'''
files["examples/04_routing_direct/main.py"] = '''print("Routing")'''

files["examples/05_advanced_topics/README.md"] = '''# 05 Advanced Topics (Python)'''
files["examples/05_advanced_topics/main.py"] = '''print("Topics")'''

# Golang Examples
files["examples_go/01_basic_queue/README.md"] = '''
# 01 Basic Queue (Golang)
**Goal:** Basic RabbitMQ messaging.
'''
files["examples_go/01_basic_queue/producer.go"] = '''
package main
import "fmt"
func main() { fmt.Println("Producer") }
'''
files["examples_go/01_basic_queue/consumer.go"] = '''
package main
import "fmt"
func main() { fmt.Println("Consumer") }
'''

files["examples_go/02_worker_queue/README.md"] = '''# 02 Worker Queue (Golang)'''
files["examples_go/02_worker_queue/main.go"] = '''package main\nfunc main() {}'''

files["examples_go/03_pubsub_fanout/README.md"] = '''# 03 PubSub Fanout (Golang)'''
files["examples_go/03_pubsub_fanout/main.go"] = '''package main\nfunc main() {}'''

files["examples_go/04_routing_direct/README.md"] = '''# 04 Routing Direct (Golang)'''
files["examples_go/04_routing_direct/main.go"] = '''package main\nfunc main() {}'''

files["examples_go/05_advanced_topics/README.md"] = '''# 05 Advanced Topics (Golang)'''
files["examples_go/05_advanced_topics/main.go"] = '''package main\nfunc main() {}'''

for filepath, content in files.items():
    full_path = os.path.join(base, filepath)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w") as f:
        f.write(content.strip() + "\\n")
