from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from bson.objectid import ObjectId
from dotenv import load_dotenv
import os

class MongoWrapper:
    def __init__(self):
        load_dotenv()
        db_uri = os.environ.get("DB_URI")
        self.mongo_cli = MongoClient(db_uri, server_api = ServerApi('1'))
        self.collections = ["File", "Peer", "Part"]
        self.set_databases()
        self.set_collection()

    def set_databases(self):
        self.primary_db = self.mongo_cli["FileSharingDB"]

    def set_collection(self):
        collection_list = self.primary_db.list_collection_names()
        for col in self.collections:
            if col not in collection_list:
                print(f"Created {col}")
                self.primary_db[col]

    def get_collection_data(self, collection):
        return self.primary_db[collection].find({})

    def add_data_to_collection(self, collection_name, data):
        try:
            data = self.primary_db[collection_name].insert_one(data)
            return str(data.inserted_id)
        except Exception:
            return None
        
    def update_data(self, collection_name, data, updated_data) -> bool:
        dt = {"$set": updated_data}
        try:
            self.primary_db[collection_name].update_one(data, dt)
            return True
        except Exception:
            return False
        
    def get_file_data(self, file_uid):
        try:
            file_uid = ObjectId(file_uid)
            file = self.primary_db["File"].find_one({"_id": file_uid})
            file['_id'] = str(file['_id'])
            return file
        except Exception as e:
            return e
        
    def update_seeders_post_download(self, file_info, offset, user):
        try:
            meta = {"part_file_name": f'{offset}.part',
                        "original_name": file_info['name'],
                        "file_id": file_info['_id'],
                        "extension": file_info['type'],
                        "offset": offset, "length": file_info['total_parts'],
                        "user_mac": user,
                        "timestamp": file_info['timestamp'],
                        "original_size": file_info['size']}
            self.add_data_to_collection('Part', meta)
        except Exception as e:
            return e
        
    def get_parts_for_file(self, file_uid):
        try:
            cursor = self.primary_db["Part"].find({"file_id": file_uid})
            return cursor
        except Exception as e:
            return e
        
    def get_user_if_active(self, user_id):
        try:
            peer = self.primary_db['Peer'].find_one({'user_id': user_id, 'active': "True"})
            return peer
        except Exception as e:
            return e
        
    def get_user(self, user_id):
        try:
            peer = self.primary_db['Peer'].find_one({'user_id': user_id})
            return peer
        except Exception as e:
            return e
        
        
    def delete_part(self, file_uid, offset):
        try:
            result = self.primary_db["Part"].delete_one({'file_uid': file_uid, 'offset': offset})
            return result
        except Exception as e:
            return e
        
    def count_documents(self, collection):
        try:
            return self.primary_db[collection].count_documents({})
        except Exception as e:
            return e
        
    def delete_database(self):
        try:
            self.primary_db['Peer'].delete_many({})
            self.primary_db['Part'].delete_many({})
            self.primary_db['File'].delete_many({})
        except Exception as e:
            return e
        


