Use cloud storage as a filesystem:  

   ```python
    from cloudbutton.multiprocessing import Pool
    from cloudbutton.cloud_proxy import os, open

    filename = 'bar/foo.txt'
    with open(filename, 'w') as f:
        f.write('Hello world!')

    dirname = os.path.dirname(filename)
    print(os.listdir(dirname))

    def read_file(filename):
        with open(filename, 'r') as f:
            return f.read()

    pool = Pool()
    res = pool.apply(read_file, (filename,))
    print(res)

    os.remove(filename)
    print(os.listdir(dirname))
   ```