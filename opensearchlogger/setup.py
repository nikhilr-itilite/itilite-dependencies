import setuptools

setuptools.setup(
    name="opensearchlogger",
    version="0.0.1",
    author="Madhu",
    author_email="madhusudhan.padmanabhan@itilite.com",
    description="Logger library 1",
    packages=setuptools.find_packages(),
    license="ITILITE",
    install_requires=["opensearch-py", "pydantic==1.10.11"],
)
