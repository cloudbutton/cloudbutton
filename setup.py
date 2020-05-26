from setuptools import setup, find_packages

setup(
    name='cloudbutton',
    version='0.1.0',
    url='https://github.com/cloudbutton/cloudbutton',
    author='Cloudbutton Team',
    description='Run many jobs over the Cloud',
    long_description="Cloudbutton toolkit lets you transparently run your Python functions on any Cloud",
    author_email='cloudlab@urv.cat',
    packages=find_packages(),
    install_requires=[
        'pywren-ibm-cloud>=1.5.2', 'redis'
    ],
    include_package_data=True,
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.5',
)
