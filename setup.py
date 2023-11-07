from setuptools import setup, find_packages

setup(
    name='byoca',
    version='0.1.0',
    packages=find_packages(),
    install_requires=[
        'websockets',
        'nest_asyncio',
        'asyncio',
        # Any other dependencies you have
    ],
    python_requires='>=3.6',
    entry_points={
        'console_scripts': [
            'byoca=byoca.core:main',
        ],
    },
    # Additional metadata about your package
    author="Your Name",
    author_email="your.email@example.com",
    description="Package to remotely trigger functions in a Colab environment",
    long_description=open('README.md').read(),
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/byoca",
)
