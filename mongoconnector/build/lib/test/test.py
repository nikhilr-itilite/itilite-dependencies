import json
import pprint

import mongoconnector

if __name__ == "__main__":
    pp = pprint.PrettyPrinter(indent=4)

    # data = json.load(open("../mongoconnector/test_search_builder_query.json", 'r'))
    data = json.load(
        open(
            "/home/mamtakumari/Mamta/Projects/package-and-streaming/fast-api/lambda_layer/mongoconnector/test/ \
            hotel_recommendation_query.json",
            "r",
        )
    )
    # pp.pprint(data['search'])

    # init_serializer= Query(**data['search']['query'])
    # query = Query(**data)
    mongo_connector = mongoconnector.Connector()
    # res = mongo_connector.find_docs("test", "trip", "flight_trip.json", data)

    # mongo_connector = mongoconnector.Connector("flight_trip.json", data)
    # res = mongo_connector.find_docs("test", "trip")

    doc = {"hi": "test"}
    # q = mongo_connector.insert_document("test", "test2", doc, "124444")
    # res = mongo_connector.upsert_document("test", "test2", doc, "124444")
    # res = mongo_connector.search_service.find_docs("test", "trip", "flight_trip.json", data)
    # res = mongo_connector.document_service.insert_document("test", "test2", doc, "1244445")
    # doc = {
    #     "hi": "test-update"
    # }
    # res = mongo_connector.document_service.upsert_document("test", "test2", doc, "1244445")

    # res = mongo_connector.collection_service.create_collection("test","test3")

    # res = mongo_connector.document_service.mongo_raw_query_upsert("test", "0012-0149",
    # {"leg_info.leg_unique_id": "4fdfd0f7-b9fc-41d2-8f85-be2339ccda4d"},{
    # "$set": {'leg_info.$.request.$[reqarr].status': 0}},
    # [{"reqarr.status": 1}], False)

    res = mongo_connector.search_service.find_docs("hotel", "hotel_recommendation", "hotel_recommended.json", data)
    print(res)
