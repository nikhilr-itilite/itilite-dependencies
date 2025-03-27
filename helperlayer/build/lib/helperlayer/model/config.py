import os

MONGO_DB_USERNAME = os.environ["MONGO_DB_USERNAME"]
MONGO_DB_PASSWORD = os.environ["MONGO_DB_PASSWORD"]
MONGO_HOST = os.environ["MONGO_HOST"]
MONGO_PORT = 27017
TRAVEL_DB = os.environ.get("TRAVEL_DB", "trip_info")

FLIGHT_LEG_EVENT_CNAME = os.environ.get("FLIGHT_LEG_EVENT_CNAME", "flight_leg_event")
FLIGHT_FAREQUOTE_CNAME = os.environ.get("FLIGHT_FAREQUOTE_CNAME", "flight_farequote")

HOTEL_LEG_EVENT_CNAME = os.environ.get("HOTEL_LEG_EVENT_CNAME", "hotel_leg_event")
HOTEL_FAREQUOTE_CNAME = os.environ.get("HOTEL_FAREQUOTE_CNAME", "hotel_farequote")

FLIGHT_RECOMMENDATION_CNAME = os.environ.get("FLIGHT_RECOMMENDATION_CNAME", "flight_recommendation")
HOTEL_RECOMMENDATION_CNAME = os.environ.get("HOTEL_RECOMMENDATION_CNAME", "hotel_recommendation")

FLIGHT_MORE_FARE_CAL_CNAME = os.environ.get("FLIGHT_MORE_FARE_CAL_CNAME", "flight_more_fare_cal")

FLIGHT_TRANSFORMATION_CNAME = os.environ.get("FLIGHT_TRANSFORMATION_CNAME", "flight_transformation")
HOTEL_TRANSFORMATION_CNAME = os.environ.get("HOTEL_TRANSFORMATION_CNAME", "hotel_transformation")

FLIGHT_PREPROCESS_CNAME = os.environ.get("FLIGHT_PREPROCESS_CNAME", "flight_preprocess")
HOTEL_PREPROCESS_CNAME = os.environ.get("HOTEL_PREPROCESS_CNAME", "hotel_preprocess")

config = {
    "databases": {
        "mongodb": {
            "password": MONGO_DB_PASSWORD,
            "username": MONGO_DB_USERNAME,
            "host": MONGO_HOST,
            "port": MONGO_PORT,
            "db_name": TRAVEL_DB,
        },
        # "redis": {
        #   "host": REDIS_HOST,
        #   "port": REDIS_PORT,
        #   "db": REDIS_DB
        # },
        # "mysql": {
        #   "host": MYSQL_HOST,
        #   "port": MYSQL_PORT,
        #   "user": MYSQL_USER,
        #   "password": MYSQL_PASSWORD,
        #   "db_name": MYSQL_DB
        # }
    },
    "active_databases": ["mongodb"],
    "data_mappings": {
        "flight_leg_event": {
            "store": "mongodb",
            "database": TRAVEL_DB,
            "schema": FLIGHT_LEG_EVENT_CNAME,
            "primary_key": "_id",
            "auto_generated": True,
        },
        "hotel_leg_event": {
            "store": "mongodb",
            "database": TRAVEL_DB,
            "schema": HOTEL_LEG_EVENT_CNAME,
            "primary_key": "_id",
            "auto_generated": True,
        },
        "flight_farequote": {
            "store": "mongodb",
            "database": TRAVEL_DB,
            "schema": FLIGHT_FAREQUOTE_CNAME,
            "primary_key": "_id",
            "auto_generated": False,
        },
        "hotel_farequote": {
            "store": "mongodb",
            "database": TRAVEL_DB,
            "schema": HOTEL_FAREQUOTE_CNAME,
            "primary_key": "_id",
            "auto_generated": False,
        },
        "flight_recommendation": {
            "store": "mongodb",
            "database": TRAVEL_DB,
            "schema": FLIGHT_RECOMMENDATION_CNAME,
            "primary_key": "_id",
            "auto_generated": True,
        },
        "hotel_recommendation": {
            "store": "mongodb",
            "database": TRAVEL_DB,
            "schema": HOTEL_RECOMMENDATION_CNAME,
            "primary_key": "_id",
            "auto_generated": True,
        },
        "flight_more_fare_cal": {
            "store": "mongodb",
            "database": TRAVEL_DB,
            "schema": FLIGHT_MORE_FARE_CAL_CNAME,
            "primary_key": "_id",
            "auto_generated": True,
        },
        "flight_transformation": {
            "store": "mongodb",
            "database": TRAVEL_DB,
            "schema": FLIGHT_TRANSFORMATION_CNAME,
            "primary_key": "_id",
            "auto_generated": True,
        },
        "hotel_transformation": {
            "store": "mongodb",
            "database": TRAVEL_DB,
            "schema": HOTEL_TRANSFORMATION_CNAME,
            "primary_key": "_id",
            "auto_generated": True,
        },
        "flight_preprocess": {
            "store": "mongodb",
            "database": TRAVEL_DB,
            "schema": FLIGHT_PREPROCESS_CNAME,
            "primary_key": "_id",
            "auto_generated": True,
        },
        "hotel_preprocess": {
            "store": "mongodb",
            "database": TRAVEL_DB,
            "schema": HOTEL_PREPROCESS_CNAME,
            "primary_key": "_id",
            "auto_generated": True,
        },
    },
}
