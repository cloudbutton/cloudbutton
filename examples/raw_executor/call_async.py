"""
Simple Cloudbutton example using the map_reduce method
of the raw API.
"""
from cloudbutton.engine.executor import FunctionExecutor


def my_function(x):
    return x + 7


if __name__ == '__main__':
    cb_exc = FunctionExecutor()
    cb_exc.call_async(my_function, 3)
    print(cb_exc.get_result())
