import setuptools

setuptools.setup(
    name="mongo_connector",
    version="0.0.1",
    author="Mamtha K",
    author_email="mamta.kumari@itilite.com",
    description="Mongo Search library 1",
    packages=setuptools.find_packages(),
    license="ITILITE",
    install_requires=["pymongo==4.7.2", "pydantic==1.10.11"],
)
