from setuptools import setup, find_packages

exec(open('cloudbutton/version.py').read())

setup(
    name='cloudbutton',
    version=__version__,
    url='https://github.com/cloudbutton/cloudbutton',
    author='Cloudbutton Team',
    description='Run multiprocessing-like applications in the Cloud',
    long_description="A python framewrok for transparently running multiprocessing-like applications in any Cloud",
    author_email='cloudlab@urv.cat',
    packages=find_packages(),
    install_requires=[
        'lithops',
        'wheel',
        'Click',
        'pandas',
        'PyYAML',
        'python-dateutil',
        'pika==0.13.1',
        'glob2',
        'tqdm',
        'lxml',
        'tblib',
        'docker',
        'requests',
        'seaborn',
        'paramiko',
        'matplotlib',
        'kubernetes',
        'ibm-cos-sdk',
        'redis',
        'boto3',
        'google-cloud-storage==1.20.0',
        'google-cloud-pubsub==1.0.0',
        'google-api-python-client==1.7.11',
        'google-auth>=1.19.1',
        'aliyun-fc2',
        'oss2',
        'azure-storage-blob==2.1.0',
        'azure-storage-queue==2.1.0'
    ],
    include_package_data=True,
    entry_points='''
        [console_scripts]
        cloudbutton=cloudbutton.cli.cli:cli
    ''',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Operating System :: OS Independent',
        'Natural Language :: English',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
    ],
    python_requires='>=3.5',
)
