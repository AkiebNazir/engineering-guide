import multiprocessing
import re
from collections import Counter

def mapper(chunk):
    words = re.findall(r'\b\w+\b', chunk.lower())
    return Counter(words)

def reducer(counters):
    total = Counter()
    for c in counters:
        total.update(c)
    return total

def mapreduce(text, num_workers=4):
    chunk_size = len(text) // num_workers
    chunks = [text[i:i + chunk_size] for i in range(0, len(text), chunk_size)]
    
    with multiprocessing.Pool(num_workers) as pool:
        mapped = pool.map(mapper, chunks)
        
    reduced = reducer(mapped)
    return reduced

if __name__ == "__main__":
    text = "Hello world! This is a test. Hello again. World of MapReduce. " * 1000
    result = mapreduce(text)
    print("Top 5 words:", result.most_common(5))
