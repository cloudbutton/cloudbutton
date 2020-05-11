from cloudbutton import Pool, Semaphore, SimpleQueue, getpid
import time

def f(sem, q):
    pid = getpid()
    ts = time.time()
    msg = 'I am process {} and here is my timestamp: {}'.format(pid, ts)
    with sem:
        q.put(msg)

if __name__ == "__main__":
    sem = Semaphore(value=0)
    q = SimpleQueue()

    with Pool() as p:
        p.map_async(f, [[sem, q]] * 3)

        print('\nRight now the queue is empty: {}'.format(q.empty()))

        print('Releasing the semaphore once')
        sem.release()
        print('Got message: {}'.format(q.get()))
        print('Only one process acquired the semaphore: {}'.format(q.empty()))

        print('\nReleasing the semaphore once')
        sem.release()
        print('Got message: {}'.format(q.get()))
        print('Only one process acquired the semaphore: {}'.format(q.empty()))

        print('\nReleasing the semaphore once')
        sem.release()
        print('Got message: {}'.format(q.get()))
        print('Only one process acquired the semaphore: {}'.format(q.empty()))

