from cloudbutton import Process, JoinableQueue, getpid
import time

def worker(q):
    print("I'm process", getpid())
    q.get()
    time.sleep(10)
    q.task_done()

if __name__ == '__main__':
    q = JoinableQueue()
    p = Process(target=worker, args=(q,))
    p.start()

    q.put('work')

    print('Waiting until all tasks are completed...')
    q.join()
    print('All tasks have been confirmed')

    p.join()