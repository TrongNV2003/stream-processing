from pymongo import MongoClient

from stream_processing.setting.config import mongo_config

class DatabaseHandler:
    def __init__(self):
        self.client = MongoClient(mongo_config.mongo_uri)
        self.db = self.client[mongo_config.db_name]
        self.collection = self.db[mongo_config.results_attack_collection]
        self.client.admin.command('ping')
    
    def save_result(self, result: dict):
        self.collection.insert_one(result)

    def get_latest_results(self, limit: int = 10):
        results = self.collection.find().sort("timestamp", -1).limit(limit)
        return list(results)
