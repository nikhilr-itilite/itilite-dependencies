import setuptools


setuptools.setup(
    name="opensearch_connector",
    version="0.0.1",
    author="Mamtha K",
    author_email="mamta.kumari@itilite.com",
    description="Open Search library 1",
    packages=setuptools.find_packages(),
    install_requires=[
        "opensearch-py",
    ],
)
