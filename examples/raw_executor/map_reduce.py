"""
Simple Cloudbutton example using the map_reduce method
of the raw API.

In this example the map_reduce() method will launch one
map function for each entry in 'iterdata', and then it will
wait locally for the results. Once the results be ready, it
will launch the reduce function.
"""
from cloudbutton.engine.executor import FunctionExecutor

iterdata = [1, 2, 3, 4]


def my_map_function(x):
    return x + 7


def my_reduce_function(results):
    total = 0
    for map_result in results:
        total = total + map_result
    return total


if __name__ == "__main__":
    """
    By default the reducer will be launched within a Cloud Function
    when the local PyWren have all the results from the mappers.
    """
    cb_exc = FunctionExecutor()
    cb_exc.map_reduce(my_map_function, iterdata, my_reduce_function)
    print(cb_exc.get_result())

    """
    Set 'reducer_wait_local=True' to wait for the results locally.
    """
    cb_exc = FunctionExecutor()
    cb_exc.map_reduce(my_map_function, iterdata, my_reduce_function,
                      reducer_wait_local=True)
    print(cb_exc.get_result())
