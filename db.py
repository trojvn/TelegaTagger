from mongowrapper import MongoOptions, MongoUser

from envs import DB_NAME, DB_PSWD, DB_USER

MONGO_OPTIONS = MongoOptions(DB_USER, DB_PSWD, DB_NAME)
settings = MongoUser(MONGO_OPTIONS, "settings.project").collection
