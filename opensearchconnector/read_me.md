Steps to install the package
----------------------------------

1. Pull repo from fatsapi
2. In terminal / IDE - Create venv for opensearchconnector
3. Install pip install wheel
   pip install setuptools
   pip install twine
4. Execute python setup.py bdist_wheel -> creates a dist -> whl file
5. Go to terminal, open the desired directory you want the package to be installed and Run
   pip install <absolute-path-of-dist-dir-whl-file>/opensearchconnector/dist/opensearchconnector-0.1-py3-none-any.whl -t
   python
6. To upload as zip file. Run -> zip -r layer.zip python

How to use the connector?
-------------------------------------
Add Env variables in your Lambda:
--------------------------
OPENSEARCH_CONNECTOR_HOST=""
OPENSEARCH_CONNECTOR_USERNAME =""
OPENSEARCH_CONNECTOR_PASSWORD=""
OPENSEARCH_CONNECTOR_INDEXNAME=""

1. Do import of opensearchconnector,
   import opensearchconnector

   **And add below statement right after import,**
   ---------------------------
   opensearch_client = opensearchconnector.OpensearchConnector()
---------------------------

2. To search docs, Pass the query as param,
   q = opensearch_client.find_docs(query)
3. To search docs, Pass the doc and id as param,
   q = opensearch_client.insert_document(doc, id)
ment(doc, id)
