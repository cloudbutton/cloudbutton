# Cloudbutton Toolkit

#### The Cloudbutton Toolkit is a Python multicloud library for running serverless jobs.  
It currently supports AWS Lambda, IBM Cloud Functions, Google Cloud Functions, Azure Functions, Aliyun Function Compute, and Knative.

### Getting started
Map Python functions using a pool of workers  

   ```python
    from cloudbutton import Pool
    from random import random

    SAMPLES = int(1e6)

    def is_in(p):
        x, y = random(), random()
        return x * x + y * y < 1

    if __name__ == '__main__':
        pool = Pool(processes=4)
        res = pool.map(is_in, range(SAMPLES))
        pi = 4.0 * sum(res) / SAMPLES
        print(f'Pi is roughly {pi}')
   ```

Use cloud storage as a filesystem for shared memory  

   ```python
    from cloudbutton import Pool, os, open
    from random import choice

    TEXT_LENGTH = int(1e6)

    def count_char(char, filename):
        with open(filename, 'r') as f:
            text = f.read()
        count = text.count(char)
        return (char, count)

    if __name__ == "__main__":
        alphabet = 'abcdefghijklmnopqrstuvwxyz'
        text = ''.join([choice(alphabet) for _ in range(TEXT_LENGTH)])
        
        filename = 'random_text.txt'
        with open(filename, 'w') as f:
            f.write(text)

        pool = Pool()
        res = pool.map(count_char, [(char, filename) for char in alphabet])
        print(res)
        os.remove(filename)
   ```

Use remote in-memory cache for fast IPC and synchronization  

   ```python
    from cloudbutton import Pool, Manager, Lock
    from random import choice

    def count_multiples(num, sequence, record, lock):
        count = 0
        for x in sequence:
            if x % num == 0:
                count += 1
        record[num] = count
        with lock:
            record['total'] += count 

    if __name__ == "__main__":
        pool = Pool()
        record = Manager().dict()
        lock = Lock()

        sequence = range(1, 1000001)
        record['total'] = 0

        pool.map(count_multiples, [(i, sequence, record, lock) for i in range(1, 11)])
        print(record.todict())
   ```

## Documentation
- [Website](https://cloudbutton.github.io)
- [API Examples](/examples)
- [Toolkit Examples](https://github.com/cloudbutton/examples)

## Plugins
- [AWS Lambda](https://github.com/cloudbutton/aws-plugin)
- [Google Cloud Functions](https://github.com/cloudbutton/gcp-plugin)
- [Microsoft Azure Functions](https://github.com/cloudbutton/azure-plugin)
- [Aliyun Function Compute](https://github.com/cloudbutton/aliyun-plugin)

## Use cases
- [Serverless benchmarks](https://github.com/cloudbutton/benchmarks)
- [Moments in Time video prediction](https://github.com/cloudbutton/examples/blob/master/momentsintime/example_mit.ipynb)
