import json
from pymongo import MongoClient, ReturnDocument, ASCENDING
import configparser
import os


def init_order(self):
    return self["Init"]


class lt_db(object):
    def __init__(self, config):

        # connection information for DB
        try:
            self.user = os.environ("DBUSER")
            self.password = os.environ("DBPASS")
            self.host = os.environ("DBHOST")
            self.port = os.environ("DBPORT")
            self.dbname = os.environ("DBNAME")
        except:
            self.user = config["user"]
            self.password = config["pass"]
            self.host = config["host"]
            self.port = config["port"]
            self.dbname = config["dbname"]

    def connect(self):
        connection = {
            f"mongodb://{self.user}:{self.password}@{self.host}:{self.port}/{self.dbname}"
        }
        try:
            self.client = MongoClient(connection)
            print("Connected to db!")
            return True
        except Exception as ex:
            print(f"An error occured connecting to the database.{ex}")

    def db_init(self):
        self.db = self.client.brertdtw29riga7
        return True

    def init_add(self, Guild, Category, Name, ID, Init):
        self.db[str(Guild)][str(Category)]
        Entry = {"Name": Name, "ID": ID, "Init": Init}

        self.db[str(Guild)][str(Category)].insert_one(Entry).inserted_id
        turnCheck = self.db[str(Guild)].find_one({"Category": Category})
        initlist = list(self.db[str(Guild)][str(Category)].find({}))
        if turnCheck['turn'] != 1 and initlist[turnCheck['turn']]['Init'] < Init:
            self.db[str(Guild)].update_one(
            {"Category": Category}, {"$inc": {"turn": 1}}
        )



    def init_clear(self, Guild, Category):

        self.db[str(Guild)][str(Category)].drop()
        self.db[str(Guild)].find_one_and_update(
            {"Category": Category}, {"$unset": {"turn": 1}}
        )

    def init_remove(self, Guild, Category, Name):
        query = {"Name": Name}

        self.db[str(Guild)][str(Category)].delete_one(query)

    def init_get(self, Guild, Category):
        initList = self.db[str(Guild)][str(Category)]
        output = list(initList.find({}))
        output.sort(key=init_order, reverse=True)

        return output

    def turn_next(self, Guild, Category):

        current = self.db[str(Guild)].find_one_and_update(
            {"Category": Category}, {"$inc": {"turn": 1}}, upsert=True
        )
        entries = self.db[str(Guild)][str(Category)].count_documents({})

        if current["turn"] >= entries:
            self.db[str(Guild)].find_one_and_update(
                {"Category": Category}, {"$inc": {"turn": -entries}}
            )

    def turn_get(self, Guild, Category):

        turnCheck = self.db[str(Guild)].find_one({"Category": Category})
        try:
            return turnCheck["turn"]
        except:
            self.db[str(Guild)].find_one_and_update(
                {"Category": Category}, {"$set": {"turn": 1}}, upsert=True,
            )
            turnCheck = self.db[str(Guild)].find_one({"Category": Category})
            return turnCheck["turn"]

    def init_delay(self, Guild, Category, Name, newInit):

        current = self.db[str(Guild)].find_one({"Category": Category})
        turn = self.db[str(Guild)].find_one({"Category": Category})["turn"]
        oldInit = self.db[str(Guild)][str(Category)].find_one({"Name": Name})["Init"]
        currentInit = self.db[str(Guild)][str(Category)].find_one_and_update(
            {"Name": Name},
            {"$set": {"Init": int(newInit)}},
            return_document=ReturnDocument.AFTER,
        )["Init"]
        initraw = self.db[str(Guild)][str(Category)].find({})
        nextInit = initraw.sort("Init", -1)[turn - 1]["Init"]

        entries = self.db[str(Guild)][str(Category)].count_documents({})

        if current["turn"] >= entries:
            self.db[str(Guild)].find_one_and_update(
                {"Category": Category}, {"$inc": {"turn": -entries}}
            )

        if currentInit > nextInit or oldInit < currentInit:
            self.db[str(Guild)].update_one(
                {"Category": Category}, {"$inc": {"turn": 1}}
            )

    def add_owner(self, Guild, Category, ID):
        existCheck = self.db[str(Guild)].find_one({"Category": Category})

        try:
            if existCheck["owner"] == ID:
                output = (
                    "It looks like you're already the owner of this channel category."
                )
                return output
            else:
                currentDM = existCheck["owner"]
                output = f"<@{currentDM}> is currently the DM of this category. In order to take ownership, speak with them or a server administrator."
                return output

        except KeyError:
            self.db[str(Guild)].find_one_and_update(
                {"Category": Category}, {"$set": {"owner": ID}}, upsert=True
            )
            output = f"<@{ID}> has been added as the DM for this channel category."
            return output

        except TypeError:
            self.db[str(Guild)].find_one_and_update(
                {"Category": Category}, {"$set": {"owner": ID}}, upsert=True
            )
            output = f"<@{ID}> has been added as the DM for this channel category."
            return output

    def remove_owner(self, Guild, Category, ID, override=False):
        if override == True:
            current = self.db[str(Guild)].find_one_and_update(
                {"Category": Category}, {"$unset": {"owner": 1}}
            )
            owner = current["owner"]
            output = f"<@{owner}> has been removed as this channel's owner."
            return output
        else:
            current = self.db[str(Guild)].find_one({"Category": Category})
            owner = current["owner"]
            if ID == owner:

                self.db[str(Guild)].find_one_and_update(
                    {"Category": Category}, {"$unset": {"owner": 1}}
                )
                output = f"<@{owner}> has been removed as this channel's owner."
                return output
            else:
                output = f"<@{owner}> is the current owner for this category. Please see an administrator or speak with the current owner to take control."
                return output

    def owner_check(self, Guild, Category, ID):
        if self.db[str(Guild)].find_one({"Category": Category})["owner"] == ID:
            check = True
            return check
        else:
            check = False
            return check

    def add_char(self, Guild, Category, ID, Name):

        self.db[str(Guild)].create_index([('name', 'text')])

        try:
            char = self.db[str(Guild)].find_one({"Category": Category, "name": Name})[
                "name"
            ]
            output = f"{char.title()} is already registered."
            return output
        except:
            entry = {
                "name": Name,
                "description": f"Placeholder, replace with whatever you wish, by using the `.char set {Name.title()} description` command!",
                "Category": Category,
                "owner": ID,
                "color": 000000,
            }
            self.db[str(Guild)].insert_one(entry).inserted_id
            output = f"{Name.title()} was added to the database."
            return output

    def remove_char(self, Guild, Category, ID, Name: str):
        query = {"Category": Category, "name": Name}
        try:
            if (
                ID == self.db[str(Guild)].find_one(query)["owner"]
                or self.owner_check(Guild, Category, ID) == True
            ):
                self.db[str(Guild)].delete_one(query)
                output = f"{Name.title()} has been removed."
                return output
            else:
                output = f"{Name.title()} doesn't belong to you."
                return output
        except TypeError as e:
            print(e)
            output = f"{Name.title()} doesn't seem to exist in this category."
            return output

    def get_char(self, Guild, Category, Name):

        query = {'$text': {'$search': Name}}

        output = self.db[str(Guild)].find(query)

        return output

    def char_owner(self, Guild, Category, ID, Name):
        query = {"Category": Category, "name": Name}

        toCheck = self.db[str(Guild)].find_one(query)["owner"]
        if ID == toCheck:
            return True
        else:
            return False

    def set_field(self, Guild, Category, ID, Name, field, value):
        query = {"Category": Category, "name": Name}
        output = self.db[str(Guild)].find_one_and_update(
            query, {"$set": {field: value}}
        )["name"].title()
        return output

    def unset_field(self, Guild, Category, ID, Name, field):
        query = {"Category": Category, "name": Name}
        self.db[str(Guild)].update(query, {"$unset": {field: 1}})
