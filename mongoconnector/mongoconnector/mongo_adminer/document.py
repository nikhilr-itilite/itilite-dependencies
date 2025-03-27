import urllib

from mongoconnector import constants


class Documents:
    __mongo_client = None

    def __init__(self, client):
        self.__mongo_client = client

    def insert_document_bulk(self, db_name: str, collection_name: str, docs: list, id_field_name: str):
        try:
            for doc in docs:
                doc["_id"] = doc.get(id_field_name)

            (self.__mongo_client[urllib.parse.quote(db_name)].get_collection(urllib.parse.quote(collection_name)).insert_many(docs))
            return {"statusCode": 200, "body": "Bulk docs inserted"}
        except Exception as e:
            raise Exception("Error inserting documents in bulk. Error: " + str(e))

    def insert_document(self, db_name, collection_name, doc, id):
        try:
            doc["_id"] = id
            self.__mongo_client[urllib.parse.quote(db_name)].get_collection(urllib.parse.quote(collection_name)).insert_one(doc)
            return {"statusCode": 200, "body": "Document inserted!!!"}
        except Exception as e:
            raise Exception("Error inserting document" + str(doc["_id"]) + ". Error: " + str(e))

    def upsert_document_by_id(self, db_name, collection_name, doc, id):
        try:
            doc["_id"] = id

            self.__mongo_client[urllib.parse.quote(db_name)].get_collection(urllib.parse.quote(collection_name)).update_one(
                {constants.MONGO_ID: id}, {constants.MONGO_SET: doc}, upsert=True
            )
            return {"statusCode": 200, "body": "Document inserted / Updated!!!"}
        except Exception as e:
            raise Exception("Error inserting document" + str(doc["_id"]) + ". Error: " + str(e))

    def mongo_raw_query_upsert(
        self,
        db_name,
        collection_name,
        filter_criteria,
        update_doc_field_set,
        array_filter=None,
        upsert=False,
    ):
        try:
            self.__mongo_client[urllib.parse.quote(db_name)].get_collection(urllib.parse.quote(collection_name)).update_one(
                filter_criteria,
                update_doc_field_set,
                array_filters=array_filter,
                upsert=upsert,
            )
            return {"statusCode": 200, "body": "Document inserted / Updated!!!"}
        except Exception as e:
            raise Exception("Error updating document" + ". Error: " + str(e))

    def insert_document_bulk_autogenerate_id(self, db_name: str, collection_name: str, docs: list):
        try:
            (self.__mongo_client[urllib.parse.quote(db_name)].get_collection(urllib.parse.quote(collection_name)).insert_many(docs))
            return {"statusCode": 200, "body": "Bulk docs inserted"}
        except Exception as e:
            raise Exception("Error inserting documents in bulk. Error: " + str(e))

    def update_many(
        self,
        db_name: str,
        collection_name: str,
        match_criteria_query: dict,
        aggregation_query: dict,
    ):
        try:
            (
                self.__mongo_client[urllib.parse.quote(db_name)]
                .get_collection(urllib.parse.quote(collection_name))
                .update_many(match_criteria_query, aggregation_query)
            )
            return {"statusCode": 200, "body": "Bulk docs updated"}
        except Exception as e:
            raise Exception("Error inserting documents in bulk. Error: " + str(e))

    def mongo_delete_many(self, db_name, collection_name, filter_criteria):
        try:
            self.__mongo_client[urllib.parse.quote(db_name)].get_collection(urllib.parse.quote(collection_name)).delete_many(
                filter_criteria
            )
            return {"statusCode": 200, "body": "Document Deleted!!!"}
        except Exception as e:
            raise Exception("Error deleting document" + ". Error: " + str(e))

    def mongo_bulk_write(self, db_name, collection_name, update_requests):
        try:
            if update_requests:
                self.__mongo_client[urllib.parse.quote(db_name)].get_collection(urllib.parse.quote(collection_name)).bulk_write(
                    update_requests
                )
                return {
                    "statusCode": 200,
                    "body": "{} Documents Updated!!!".format(len(update_requests)),
                }
        except Exception as e:
            raise Exception("Error updating bulk document" + ". Error: " + str(e))
