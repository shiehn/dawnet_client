from setuptools import setup, find_packages

setup(
    name='dawnet-client',
    version='0.0.16',
    packages=find_packages(),
    install_requires=[
        'websockets',
        'nest_asyncio',
    ],
    python_requires='>=3.6',
    entry_points={
        'console_scripts': [
            'dawnet-client=dawnet_client.core:main',
        ],
    },
    # Additional metadata about your package
    author="Steve Hiehn",
    author_email="stevehiehn@gmail.com",
    description="DAWNet client enables remote execution of python code triggered from a DAW.",
    long_description=open('README.md').read(),
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/byoca",
)
