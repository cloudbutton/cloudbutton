# This repo has been merged to the official [Lithops repo](https://github.com/lithops-cloud/lithops)

-------

<p align="center"> <h1> Cloudbutton Toolkit </h1> </p>

The Cloudbutton toolkit is a multicloud framework that enables the transparent execution of unmodified, regular Python code against disaggregated cloud resources. With the Cloudbutton toolkit, there is no new API to learn. It provides the same API as the Python's standard [**multiprocessing**](https://docs.python.org/3/library/multiprocessing.html) library. Any program built on top of this library can be run on any of the major serverless computing services. Its multicloud-agnostic architecture ensures portability across Clouds and overcomes vendor lock-in.

The Cloudbutton toolkit is built on top of the [Lithops framework](https://github.com/lithops-cloud/lithops), and currently, it supports all these Clouds and backends:

<table>

<tr>
<th align="center">
<img width="441" height="1">
<p> 
<small>
Cloud
</small>
</p>
</th>

<th align="center">
<img width="441" height="1px">
<p> 
<small>
Compute Backends
</small>
</p>
</th>

<th align="center">
<img width="441" height="1">
<p> 
<small>
Storage Backends
</small>
</p>
</th>
</tr>

<tr>
<td align='center'>
IBM Cloud
</td>
<td align='center'>
IBM Cloud Functions <br>
IBM Code Engine
</td>
<td align='center'>
IBM Cloud Object Storage
</td>
</tr>

<tr>
<td align='center'>
AWS
</td>
<td align='center'>
AWS Lambda  
</td>
<td align='center'>
AWS S3
</td>
</tr>

<tr>
<td align='center'>
Google Cloud
</td>
<td align='center'>
Google Cloud Functions <br>
Google Cloud Run
</td>
<td align='center'>
Google Cloud Storage
</td>
</tr>

<tr>
<td align='center'>
Microsoft Azure
</td>
<td align='center'>
Azure Functions
</td>
<td align='center'>
Azure Blob Storage
</td>
</tr>

<tr>
<td align='center'>
Alibaba Aliyun
</td>
<td align='center'>
Aliyun functions
</td>
<td align='center'>
Aliyun Object Storage Service
</td>
</tr>

<tr>
<td align='center'>
   <i>Generic</i>
</td>
<td align='center'>
Knative <br>
OpenWhisk
</td>
<td align='center'>
Ceph, Redis <br>
Openstack Swift
</td>
</tr>

</table>


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
- [Website](https://lithops-cloud.github.io)
- [API Examples](examples)
- [Toolkit Examples](https://github.com/cloudbutton/examples)

## Use cases
- [Serverless benchmarks](https://cloudbutton.github.io/benchmarks)
- [Moments in Time video prediction](https://cloudbutton.github.io/examples/example_mit)
