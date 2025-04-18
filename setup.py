from setuptools import setup, find_packages

setup(
    name="restaurant_scraper",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        'requests',
        'beautifulsoup4',
        'selenium',
    ]
) 