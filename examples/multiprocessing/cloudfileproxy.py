from cloudbutton import CloudFileProxy

if __name__ == "__main__":
    proxy = CloudFileProxy()
    os = proxy
    open = proxy.open

    filepath = 'bar/foo.txt'
    with open(filepath, 'wb') as f:
        f.write('Hello world!')

    dirname = os.path.dirname(filepath)
    print(os.listdir(dirname))

    with open(filepath, 'rb') as f:
        print(f.read(6))
        print(f.read())

    os.remove(filepath)
    print(os.listdir(dirname))
    