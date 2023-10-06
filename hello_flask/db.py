from pymongo import MongoClient
import requests

mongo_client = MongoClient("mongo")
db = mongo_client["database"]

users = db["collection"]

def isUser(username):
    # check if user exists
    pass

def register():
    pass
    # check if username already exists
    
    # elif store username, password

def login():
    pass
    # check if username exists
        # else register
    # check correct username and password

    # note: session module in flask saves data so
        # only need to log in once per session

def logout():
    pass
    # idk if we want to do something like this?