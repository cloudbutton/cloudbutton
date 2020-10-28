from cloudbutton.multiprocessing import Process


def f(name):
    import os
    print(os.environ)
    print('hello', name)


if __name__ == '__main__':
    p = Process(target=f, args=('bob',))
    p.start()
    p.join()
