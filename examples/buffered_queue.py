from cloudbutton import Process, Queue
from cloudbutton import getpid


def f(q):
    print("I'm process", getpid())
    q.put([42, None, 'hello'])


if __name__ == '__main__':
    q = Queue()
    p = Process(target=f, args=(q,))
    p.start()
    print(q.get())    # prints "[42, None, 'hello']"
    p.join()
