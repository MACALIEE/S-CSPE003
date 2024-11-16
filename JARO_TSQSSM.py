import threading
from multiprocessing import shared_memory, Lock, Condition
import struct

class SharedMemoryQueue:

    def __init__(self, capacity, item_size=4):

        self.capacity = capacity
        self.item_size = item_size
        self.shm = shared_memory.SharedMemory(create=True, size=capacity * item_size)
        self.buffer = self.shm.buf
        self.head = 0
        self.tail = 0
        self.size = 0
        self.lock = Lock()
        self.not_empty = Condition(self.lock)
        self.not_full = Condition(self.lock)

    def enqueue(self, item):

        with self.not_full:
            while self.size == self.capacity:
                self.not_full.wait()
            
            index = self.tail * self.item_size
            try:
                self.buffer[index:index + self.item_size] = struct.pack('i', item)
                self.tail = (self.tail + 1) % self.capacity
                self.size += 1
                self.not_empty.notify()
            except struct.error as e:
                raise ValueError(f"Failed to enqueue item: {e}")

    def dequeue(self):
  
        with self.not_empty:
            while self.size == 0:
                self.not_empty.wait()
            
            index = self.head * self.item_size
            try:
                item = struct.unpack('i', self.buffer[index:index + self.item_size])[0]
                self.head = (self.head + 1) % self.capacity
                self.size -= 1
                self.not_full.notify()
                return item
            except struct.error as e:
                raise ValueError(f"Failed to dequeue item: {e}")

    def close(self):

        self.shm.close()
        self.shm.unlink()

def producer(queue, items):
  
    for item in items:
        print(f"Producing: {item}")
        queue.enqueue(item)

def consumer(queue, count):
   
    for _ in range(count):
        item = queue.dequeue()
        print(f"Consumed: {item}")

if __name__ == "__main__":
    capacity = 5
    queue = SharedMemoryQueue(capacity)

    items_to_produce = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

    producer_thread = threading.Thread(target=producer, args=(queue, items_to_produce))
    consumer_thread = threading.Thread(target=consumer, args=(queue, len(items_to_produce)))

    try:
        producer_thread.start()
        consumer_thread.start()

        producer_thread.join()
        consumer_thread.join()
    finally:
        queue.close()
