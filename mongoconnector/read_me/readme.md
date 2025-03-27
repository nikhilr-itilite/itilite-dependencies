Steps to install the package
----------------------------------
1. Pull repo from fatsapi
2. In terminal / IDE - Create venv for mongoconnector
3. Install pip install wheel
           pip install setuptools
           pip install twine
4. Execute python setup.py bdist_wheel -> creates a dist -> whl file
5. Go to terminal, open the disired directory you want the package to be installed and Run
    pip install <absolute-path-of-dist-dir-whl-file>/mongoconnector/dist/mongoconnector-0.1-py3-none-any.whl -t python
6. To upload as zip file. Run -> zip -r layer.zip python


How to use the connector?
-------------------------------------
PS: (Important) Create a resource folder in your lambda and add your document description file
Add Env variables in your Lambda:
    MONGO_DB_PASSWORD=""
    MONGO_DB_USERNAME=""
    MONGO_HOST=""


1. Do import of mongoconnector,
   import mongoconnector</br></br>
2. Create a global variable
   </br> mongo_connector_1 = mongoconnector.Connector()
   </br> res = mongo_connector_1.search_service.find_docs(db_name, collection_name, schema_doc_name, query)
   </br> Here we pass the shemadoc path and query. This method call will verify query for every call made</br></br>
    mongo_connector_2 = mongoconnector.Connector(schema_doc_name, query)
   </br> res = mongo_connector_2.search_service.find_docs("test", "trip")
   </br> Here we pass the shemadoc path and query during mongo_connector object creation and validation is done here. This method call picks the verified query from mongo_connector_2 object</br></br>
2. To search docs by id, Pass the query as param,</br>
     q = mongo_connector.find_doc_by_id(db_name, collection_name, id) </br></br>
3. To Insert doc, Pass the doc and id as param,</br>
        q = mongo_connector.document_service.insert_document(db_name, collection_name, doc, id)</br></br>
4. To insert bulk docs,</br>
   mongo_connector.document_service.insert_document_bulk(db_name, collection_name, docs, id_field_name)</br></br>
5. To find mongo docs based on raw query of mongo,</br>
   mongo_connector.mongo_raw_query_find(db_name, collection_name, query)
6. To upset mongo docs based,</br>
   mongo_connector.document_service.upsert_document_by_id(db_name, collection_name, doc, id)</br>
   </br>mongo_connector.document_service.mongo_raw_query_upsert(db_name, collection_name, filter_criteria,
   update_doc_field_set, array_filter=None, upsert=False)</br></br>
7. To create collection,</br>
   mongo_connector.collection_service.create_collection(db_name, collection_name,)



Sample Data:
-----------------------
1. Mongo connector query samples. Refer file -> query_builder_query_samples.txt
2. Document description structure. Refer file -> doc_schema_flightsearch.json
