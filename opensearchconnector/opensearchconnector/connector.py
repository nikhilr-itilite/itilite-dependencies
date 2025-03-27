from opensearchpy import OpenSearch, helpers
import logging
import os

index_name = os.getenv("OPENSEARCH_CONNECTOR_INDEXNAME")


class OpensearchConnector:
    client = None

    def __init__(self):
        host = os.getenv("OPENSEARCH_CONNECTOR_HOST")
        auth = (
            os.getenv("OPENSEARCH_CONNECTOR_USERNAME"),
            os.getenv("OPENSEARCH_CONNECTOR_PASSWORD"),
        )

        self.client = OpenSearch(
            hosts=host,
            http_auth=auth,
            use_ssl=True,
            verify_certs=False,
            ssl_assert_hostname=False,
            ssl_show_warn=False,
        )

    def __frame_doc(self, doclist: list, id_field_name: str):
        docs = []
        try:
            for doc in doclist:
                index_data = {
                    "_index": index_name,
                    "_type": "doc",
                    "_id": doc[id_field_name],
                    "_source": doc,
                }
                docs.append(index_data)
        except Exception:
            logging.error("Error framing doc")
        return docs

    def bulk_insert_document(self, docs, id_field_name):
        logging.info("Bulk insert document")
        docs_list = self.__frame_doc(docs, id_field_name)
        helpers.bulk(self.client, docs_list)

    def insert_document(self, doc: dict, doc_id: object):
        response = self.client.index(index=index_name, body=doc, id=doc_id, refresh=True)
        print(response)

    def search_query(self, lat, lon, vendor_unique_id):
        json_query = {
            "query": {
                "bool": {
                    "must": [
                        {"match": {"hotel_details.latitude": lat}},
                        {"match": {"hotel_details.longitude": lon}},
                        {"match": {"hotel_details.vendors.vendor_unique_id": vendor_unique_id}},
                    ],
                    "must_not": [],
                    "should": [],
                }
            },
            "from": 0,
            "size": 10,
            "sort": [],
            "aggs": {},
        }
        res = self.client.search(index=index_name, body=json_query)
        return res

    def search_query_by_id(self, id):
        print("isndide search")
        json_query = {
            "query": {"terms": {"id": [id]}},
            "from": 0,
            "size": 10,
            "sort": [],
            "aggs": {},
        }
        res = self.client.search(index=index_name, body=json_query)
        return res

    def search_query_by_vendor(self, vendor_unique_id_list, vendor_name, vendor_id):
        print(vendor_id)
        json_query = {
            "query": {
                "bool": {
                    "must": [
                        {"match": {"vendors.vendor_id": vendor_id}},
                        {"match": {"vendors.vendor_name": vendor_name}},
                        {"terms": {"vendors.vendor_unique_id": vendor_unique_id_list}},
                    ],
                    "must_not": [],
                    "should": [],
                }
            },
            "from": 0,
            "size": 10000,
            "sort": [],
            "aggs": {},
        }
        res = self.client.search(index=index_name, body=json_query)
        return res
