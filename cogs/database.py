import re
import os

from pymongo import MongoClient
from dotenv import load_dotenv



class DatabaseHandler:
    def __init__(self, env_path='req/.env'):
        load_dotenv(env_path)
        self.client = MongoClient(os.getenv('MONGO'))
        self.db = self.client.price.tags

    def get_estimated_count(self):
        return self.db.estimated_document_count()

    def find_one_card(self, **kwargs):
        return self.db.find_one(kwargs)

    def find_cards_by_name(self, name_pattern):
        regex = re.compile(f".*{re.escape(name_pattern)}.*", re.IGNORECASE)
        return self.db.find({"name": regex})

    def insert_many_cards(self, cards):
        if cards:
            self.db.insert_many(cards)

    def update_card(self, card_id, update_fields):
        self.db.update_one({"_id": card_id}, {"$set": update_fields})

    def get_last_document_id(self):
        last_doc = self.db.find_one(sort=[("_id", -1)])
        return last_doc["_id"] if last_doc else 0