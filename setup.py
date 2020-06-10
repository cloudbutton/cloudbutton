from setuptools import setup, find_packages

exec(open('cloudbutton/version.py').read())

setup(
    name='cloudbutton',
    version=__version__,
    url='https://github.com/cloudbutton/cloudbutton',
    author='Cloudbutton Team',
    description='Run multiprocessing-like applications in the Cloud',
    long_description="A multicloud python framewrok for transparently running multiprocessing-like applications",
    author_email='cloudlab@urv.cat',
    packages=find_packages(),
    install_requires=['redis'],
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
