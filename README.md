
# Cloudbutton Toolkit

The Cloudbutton toolkit is a multicloud framework that enables the transparent execution of unmodified, regular Python code against disaggregated cloud resources. With the Cloudbutton toolkit, there is no new API to learn. It provides the same API as Python's standard [**multiprocessing**](https://docs.python.org/3/library/multiprocessing.html) and [**concurrent.futures**](https://docs.python.org/3/library/concurrent.futures.html) libraries. Any program built on top of these libraries can be run on any of the major serverless computing services. Its multicloud-agnostic architecture ensures portability across Clouds and overcomes vendor lock-in. Altogether, this represents a significant step forward in the programmability of  the cloud.


### Quick start

1. Install cloudbutton toolkit package:

   ```
   # pip install cloudbutton
   ```

2. Configure your desired storage and compute backends following the instructions in [config/](config/).


3. Run functions in the Cloud using the **multiprocessing** API:

   ```python
    # from multiprocessing import Pool
    from cloudbutton.multiprocessing import Pool
    
    def incr(x):
        return x + 1

    pool = Pool()
    res = pool.map(incr, range(10))
    print(res)
   ```

## Documentation
- [Website](https://cloudbutton.github.io)
- [API Examples](https://github.com/cloudbutton/cloudbutton/tree/master/examples)
- [Toolkit Examples](https://github.com/cloudbutton/examples)


## Backends

Compute backends:

- [IBM Cloud Functions](config/backends/compute/ibm_cf.md)
- [IBM Coligo](config/backends/compute/ibm_cf.md)
- [AWS Lambda](config/backends/compute/aws_lambda.md)
- [Microsoft Azure Functions](config/backends/compute/azure_fa.md)
- [Google Cloud Functions](config/backends/compute/gcp_functions.md)
- [Google Cloud Run](config/backends/compute/gcp_run.md)
- [Alibaba Aliyun Function Compute](config/backends/compute/aliyun_fc.md)
- [Knative](config/backends/compute/knative.md)

Storage backends:

- [IBM Cloud Object Storage](config/backends/storage/ibm_cos.md)
- [AWS S3](config/backends/storage/aws_s3.md)
- [Microsoft Azure Blob](config/backends/storage/azure_blob.md)
- [Google Storage](config/backends/storage/google_storage.md)
- [Alibaba Aliyun Object Storage Service](config/backends/storage/aliyun_oss.md)
- [Ceph](config/backends/storage/ceph.md)
- [Redis](config/backends/storage/redis.md)
- [Swift](config/backends/storage/swift.md)

## Use cases
- [Serverless benchmarks](https://cloudbutton.github.io/benchmarks)
- [Moments in Time video prediction](https://cloudbutton.github.io/examples/example_mit)
