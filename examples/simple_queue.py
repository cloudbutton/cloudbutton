from cloudbutton import Process, SimpleQueue

def f(q):
    q.put([42, None, 'hello'])

if __name__ == '__main__':
    q = SimpleQueue()
    p = Process(target=f, args=(q,))
    p.start()
    print(q.get())    # prints "[42, None, 'hello']"
    p.join()