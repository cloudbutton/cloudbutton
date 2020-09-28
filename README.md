
# Cloudbutton Toolkit

The Cloudbutton toolkit is a multicloud framework that enables the transparent execution of unmodified, regular Python code against disaggregated cloud resources. With the Cloudbutton toolkit, there is no new API to learn. It provides the same API as the Python's standard [**multiprocessing**](https://docs.python.org/3/library/multiprocessing.html) library. Any program built on top of this library can be run on any of the major serverless computing services. Its multicloud-agnostic architecture ensures portability across Clouds and overcomes vendor lock-in.

The Cloudbutton toolkit is built on top of the [Lithops framework](https://github.com/lithops-cloud/lithops), and currently, it supports all these backends:

|Cloud|Compute Backend|Storage Backend|
|---|---|---|
|IBM Cloud| IBM Cloud Functions <br> IBM Code Engine| IBM Cloud Object Storage|
|AWS | AWS Lambda|  AWS S3 |
|Google Cloud | Google Cloud Functions <br> Google Cloud Run| Google Cloud Storage|
|Microsoft Azure| Microsoft Azure Functions | Microsoft Azure Blob |
|Alibaba Aliyun| Aliyun Function Compute | Aliyun Object Storage Service |
|Generic| Knative | Ceph, Redis, Swift |


## Quick start

1. Install the cloudbutton toolkit package:

   ```
   git clone https://github.com/cloudbutton/cloudbutton
   cd cloudbutton
   python setup.py install
   ```

2. [Configure your desired compute and storage backends in Lithops](https://github.com/lithops-cloud/lithops/tree/master/config).


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

## Use cases
- [Serverless benchmarks](https://cloudbutton.github.io/benchmarks)
- [Moments in Time video prediction](https://cloudbutton.github.io/examples/example_mit)
