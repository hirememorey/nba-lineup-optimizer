from setuptools import setup, find_packages

setup(
    name="nba_stats",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "requests>=2.31.0",
        "aiohttp>=3.9.1",
        "pandas>=2.1.0",
        "numpy>=1.24.0",
    ],
    python_requires=">=3.8",
    author="Harris Gordon",
    author_email="harrisgordon@example.com",
    description="A package for fetching and storing NBA player statistics",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/nba_stats",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
) 