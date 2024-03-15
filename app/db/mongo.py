from pymongo import MongoClient

class MongoDB:
    def __init__(self, uri, db_name):
        self.client = MongoClient(uri)
        self.db = self.client[db_name]

    def create(self, collection_name, data):
        collection = self.db[collection_name]
        result = collection.insert_one(data)
        return result.inserted_id

    def read(self, collection_name, query):
        collection = self.db[collection_name]
        result = collection.find(query)
        return list(result)

    def update(self, collection_name, query, data):
        collection = self.db[collection_name]
        result = collection.update_many(query, {"$set": data})
        return result.modified_count

    def delete(self, collection_name, query):
        collection = self.db[collection_name]
        result = collection.delete_many(query)
        return result.deleted_count
