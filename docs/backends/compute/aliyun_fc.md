# CloudButton on Alibaba Cloud (Aliyun)

Cloudbutton toolkit with Aliyun Function Compute as compute backend.

### Configuration

1. Edit your cloudbutton config file and add the following keys:

```yaml
  cloudbutton:
    compute_backend : aliyun_fc

  aliyun_fc:
    public_endpoint : <PUBLIC_ENDPOINT>
    access_key_id : <ACCESS_KEY_ID>
    access_key_secret : <ACCESS_KEY_SECRET>
```
   - `public_endpoint`: public endpoint (URL) to the service. OSS and FC endpoints are different.
   - `access_key_id`: Access Key Id.
   - `access_key_secret`: Access Key Secret. 


### Verify

2. Test if Cloudbutton on Aliyun is working properly:

   Run the next command:
   
   ```bash
   $ cloudbutton test
   ```
   
   or run the next Python code:
   
   ```python
   from cloudbutton.engine.executor import FunctionExecutor
   
   def hello_world(name):
       return 'Hello {}!'.format(name)
    
   if __name__ == '__main__':
        cb_exec = FunctionExecutor()
        cb_exec.call_async(hello_world, 'World')
        print("Response from function: ", cb_exec.get_result())
   ```

*Note: if you are having troubles when executing for the first time (which triggers the installation of the runtime) try updating your ```pip```*

### Custom runtime
The Cloudbutton agent (handler) uses a default runtime with some common modules to run your code (see [requirements.txt](/compute/backends/aliyun_fc/requirements.txt)). However, if your code often requires a module that is not already included in the runtime, it will be convinient to build your custom runtime.\
The process is very simple. You only have to install your modules into a separate folder (via `pip install -t <CUSTOM_MODULES_DIR>`) and then provide it to Cloudbutton by specifing it in the config file:
```yaml
  cloudbutton:
    ...
    runtime : <CUSTOM_MODULES_DIR>
```
Or in your code:
```python
  pool = Pool(initargs={'runtime': '<CUSTOM_MODULES_DIR>'})
```

Note that the actual folder name in which you installed your modules will be used from now on to identify this runtime, thus after the first execution (which will install it to Aliyun FC) you can use that name to refer to it instead of the full path. For example, with */home/me/mycustomruntime* as the directory of your custom modules, you will be able to use *mycustomruntime* to refer to it:
```yaml
  cloudbutton:
    ...
    runtime : mycustomruntime
```
Or:
```python
  pool = Pool(initargs={'runtime': 'mycustomruntime'})
```

Finally, remember that Aliyun Function Compute has [limits](https://www.alibabacloud.com/help/doc-detail/51907.htm?spm=a2c63.l28256.b99.152.1dd43c94NMby9d) regarding runtimes.
