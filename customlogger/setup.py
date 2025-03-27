import setuptools

setuptools.setup(
    name="customlogger",
    version="0.0.1",
    author="Mamtha K",
    author_email="mamta.kumari@itilite.com",
    description="Logger library 1",
    packages=setuptools.find_packages(),
    license="ITILITE",
    install_requires=["opensearch-py", "pydantic"],
)
