from helperlayer import PyMongoConnection

mongo_obj = PyMongoConnection()
mongo_secondary_obj = PyMongoConnection(prefered_connection="secondaryPreferred")
