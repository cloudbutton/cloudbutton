"""
Simple Cloudbutton example using the map method
of the raw API.

In this example the map() method will launch one
map function for each entry in 'iterdata'. Finally
it will print the results for each invocation with
pw.get_result()
"""
from cloudbutton.engine.executor import FunctionExecutor


def my_map_function(id, x):
    print("I'm activation number {}".format(id))
    return x + 7


if __name__ == "__main__":
    iterdata = [1, 2, 3, 4]
    cb_exc = FunctionExecutor()
    cb_exc.map(my_map_function, iterdata)
    print(cb_exc.get_result())
    cb_exc.clean()
