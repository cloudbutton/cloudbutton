from cloudbutton import Process, JoinableQueue
from cloudbutton import getpid


def worker(q):
    print("I'm process", getpid())
    working = True
    while working:
        x = q.get()

        # Do work that may fail
        assert x < 10

        # Confirm task
        q.task_done()
        
        if x == -1:
            working = False

if __name__ == '__main__':
    q = JoinableQueue()
    p = Process(target=worker, args=(q,))
    p.start()

    for x in range(10): 
        q.put(x)

    # uncomment to hang on the q.join
    #q.put(11)  
    q.join()

    q.put(-1) # end loop
    p.join()