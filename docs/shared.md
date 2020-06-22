Use remote in-memory cache for fast IPC and synchronization  

   ```python
    from cloudbutton.multiprocessing import Pool, Manager, Lock
    from random import choice

    def count_chars(char, text, record, lock):
        count = text.count(char)
        record[char] = count
        with lock:
            record['total'] += count

    pool = Pool()
    record = Manager().dict()
    lock = Lock()

    # random text
    alphabet = 'abcdefghijklmnopqrstuvwxyz'
    text = ''.join([choice(alphabet) for _ in range(1000)])

    record['total'] = 0
    pool.map(count_chars, [(char, text, record, lock) for char in alphabet])
    print(record.todict())
   ```
