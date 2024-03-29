from pymongo import MongoClient, ReturnDocument, ASCENDING
from cogs.lt_logger import lt_logger
import traceback
import re


def init_order(self):
    return self["Init"]


class lt_db(object):
    def __init__(self, config):
        self.logger = lt_logger
        # connection information for DB

        self.URI = config["db_uri"]
        self.dbname = config["dbname"]

    def connect(self):

        try:
            self.client = MongoClient(self.URI)
            print("Connected to db!")
            return True
        except Exception as ex:
            print(f"An error occured connecting to the database.{ex}")
            return False

    def db_init(self):
        self.db = self.client.brertdtw29riga7
        return True

    def create_collections(self, Guild):
        self.db.dice[str(Guild)].insert_one({"user": "N/A"})
        self.db.dice[str(Guild)].delete_one({"user": "N/A"})
        self.db.rand[str(Guild)].insert_one({"user": "N/A"})
        self.db.rand[str(Guild)].delete_one({"user": "N/A"})
        self.db[str(Guild)].create_index([("name", "text")])

    def drop_collection(self, Guild):
        collections = self.db.list_collection_names()
        dropped = 0
        for c in collections:
            if re.search(str(Guild), c) == None:
                pass
            else:
                check = self.db[c].drop()
                if check != True:
                    dropped += 1
        return dropped

    # region Dice

    def dice_add(self, User, Guild, Alias, updoot):
        query = {"user": User, "Alias": Alias.lower()}
        # updoot = {"$set": {"user": User, "Alias": Alias.lower(), "Value": [Value]}}
        self.db.dice[str(Guild)].update_one(query, updoot, upsert=True)
        return f"Your {Alias} variable has been updated."

    def dice_get(self, User, Guild, Alias):

        query = {"user": User, "Alias": Alias.lower()}
        dice = self.db.dice[str(Guild)].find_one(query)
        return dice["Value"]

    def dice_delete(self, User, Guild, Alias):

        query = {"user": User, "Alias": Alias.lower()}
        check = self.db.dice[str(Guild)].find_one_and_delete(query)
        if check != None:
            return f"{Alias} has been removed!"
        else:
            return f"It doesn't looks like {Alias} was a saved dice expression."

    def dice_list(self, User, Guild):
        query = {"user": User}
        dice = self.db.dice[str(Guild)].find(query)

        outDict = {}
        for d in dice:
            outDict.update({d["Alias"]: d["Value"]})

        return outDict

    # endregion

    # region Initiative

    def init_add(self, Guild, Category, Name, ID, Init):
        self.db[str(Guild)][str(Category)]
        Entry = {"Name": Name, "ID": ID, "Init": Init}

        self.db[str(Guild)][str(Category)].insert_one(Entry).inserted_id
        turnCheck = self.db[str(Guild)].find_one({"Category": Category})
        initlist = list(self.db[str(Guild)][str(Category)].find({}))
        try:
            if turnCheck["turn"] != 1 and initlist[turnCheck["turn"]]["Init"] < Init:
                self.db[str(Guild)].update_one(
                    {"Category": Category}, {"$inc": {"turn": 1}}
                )
        except:
            pass

    def init_clear(self, Guild, Category):

        self.db[str(Guild)][str(Category)].drop()
        self.db[str(Guild)].update_one({"Category": Category}, {"$unset": {"turn": 1}})

    def init_remove(self, Guild, Category, Name):
        query = {"Name": Name}
        
        deleted = self.db[str(Guild)][str(Category)].delete_one(query)
        
        return deleted.deleted_count

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
        return current["owner"]

    def turn_get(self, Guild, Category):

        turnCheck = self.db[str(Guild)].find_one({"Category": Category})
        try:
            return turnCheck["turn"]
        except:
            self.db[str(Guild)].find_one_and_update(
                {"Category": Category},
                {"$set": {"turn": 1}},
                upsert=True,
            )
            turnCheck = self.db[str(Guild)].find_one({"Category": Category})
            return turnCheck["turn"]

    def turn_set(self, Guild, Category, newPos):

        self.db[str(Guild)].find_one_and_update(
            {"Category": Category}, {"$set": {"turn": newPos}}
        )

    def init_delay(self, Guild, Category, Name, newInit):
        try:
            turn = self.db[str(Guild)].find_one({"Category": Category})["turn"]
            oldInit = self.db[str(Guild)][str(Category)].find_one({"Name": Name})["Init"]
            currentInit = self.db[str(Guild)][str(Category)].find_one_and_update(
                {"Name": Name},
                {"$set": {"Init": float(newInit)}},
                return_document=ReturnDocument.AFTER,
            )["Init"]
            initraw = self.db[str(Guild)][str(Category)].find({})
            nextInit = initraw.sort("Init", -1)[turn - 1]["Init"]


            entries = self.db[str(Guild)][str(Category)].count_documents({})

            if turn >= entries:
                self.db[str(Guild)].find_one_and_update(
                    {"Category": Category}, {"$inc": {"turn": -entries}}
                )

            if currentInit > nextInit or oldInit < currentInit:
                self.db[str(Guild)].update_one(
                    {"Category": Category}, {"$inc": {"turn": 1}}
                )
        except Exception as e:
            print(e)
            
        
    # endregion

    # region Category Ownership

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
                {"Category": Category}, {"$set": {"owner": ID, "turn": 1}}, upsert=True
            )
            output = f"<@{ID}> has been added as the DM for this channel category."
            return output

        except TypeError:
            self.db[str(Guild)].find_one_and_update(
                {"Category": Category}, {"$set": {"owner": ID, "turn": 1}}, upsert=True
            )
            output = f"<@{ID}> has been added as the DM for this channel category."
            return output

    def remove_owner(self, Guild, Category, ID, override=False):
        if override == True:
            current = self.db[str(Guild)].find_one_and_update(
                {"Category": Category}, {"$unset": {"owner": 1}}
            )
            owner = current["owner"]
            output = f"<@{owner}> has been removed as this category's owner."
            return output
        else:
            current = self.db[str(Guild)].find_one({"Category": Category})
            owner = current["owner"]
            if ID == owner:

                self.db[str(Guild)].find_one_and_update(
                    {"Category": Category}, {"$unset": {"owner": 1}}
                )
                output = f"<@{owner}> has been removed as this category's owner."
                return output
            else:
                output = f"<@{owner}> is the current owner for this category. Please see an administrator or speak with the current owner to take control."
                return output

    def owner_check(self, Guild, Category, ID):
        if self.db[str(Guild)].find_one({"Category": Category})["owner"] == ID:
            return True
        else:
            return False

    def set_ic(self, Guild, Category, ID, Channel: int, URL):
        if self.db[str(Guild)].find_one({"Category": Category})["owner"] == ID:
            self.db[str(Guild)].find_one_and_update(
                {"Category": Category}, {"$set": {"IC": Channel, "webhook_url": URL}}
            )
            return True

    def get_ic(self, Guild, Category):
        try:
            category = self.db[str(Guild)].find_one({"Category": Category})
            return category["IC"], category["webhook_url"]
        except:
            return None, None

    def get_all_ic(self, Guild, ID):
        try:

            categories = self.db[str(Guild)].find(
                {"owner": ID, "IC": {"$exists": True}}
            )

            channels = []
            for category in categories.sort("owner", ASCENDING):

                channels.append(category["IC"])
            return channels
        except:
            message = str(traceback.format_exc())
            print(
                f"An error has occured while trying to get all ICs for {ID} in {Guild}.\n{message}"
            )

    def set_proxy(self, Guild, Category, ID, Character):

        proxy = self.get_one_char(Guild, Character, ID)["_id"]

        output = self.db[str(Guild)].find_one_and_update(
            {"Category": Category}, {"$set": {f"{ID}": proxy}}
        )

        return output

    def remove_proxy(self, Guild, Category, ID):
        output = self.db[str(Guild)].find_one_and_update(
            {"Category": Category}, {"$unset": {f"{ID}": 1}}
        )

        return output

    def get_proxy(self, Guild, Category, ID):
        try:
            proxy = self.db[str(Guild)].find_one({"Category": Category})[f"{ID}"]
            return self.db[str(Guild)].find_one({"owner": ID, "_id": proxy})

        except:
            return None

    #    def get_all_webhooks(self, Guild, ID):
    #        try:
    #            categories = self.db[str(Guild)].find({"owner":ID}, "webhook_url": {"$exists": True})
    #            channels = []
    #            for category in categories:
    #                channels.append(category["webhook_url"])
    #            return channels
    #        except:
    #            return None

    # endregion

    # region Category Settings

    def set_currency(self, Guild, Category, ID, Currency: str):
        if self.db[str(Guild)].find_one({"Category": Category})["owner"] == ID:
            self.db[str(Guild)].find_one_and_update(
                {"Category": Category}, {"$set": {"currency": Currency}}
            )
        return True

    # endregion

    # region Character Profiles

    def add_char(self, Guild, ID, Name):

        self.db[str(Guild)].create_index([("name", "text")])

        try:
            char = self.db[str(Guild)].find_one({"name": Name})["name"]
            output = f"{char.title()} is already registered."
            return output
        except:
            entry = {
                "name": Name,
                "description": f"Placeholder, replace with whatever you wish, by using the `.char set {Name.title()} description` command!",
                "owner": ID,
                "color": int("000000", 16),
                "public": "False",
            }
            self.db[str(Guild)].insert_one(entry).inserted_id
            output = f"{Name.title()} was added to the database. You can edit them using commands via Discord, or using the Web Editor, found at https://webthunder.herokuapp.com/"
            return output

    def remove_char(self, Guild, ID, Name: str):
        query = {"name": Name}
        try:
            if ID == self.db[str(Guild)].find_one(query)["owner"]:
                self.db[str(Guild)].delete_one(query)
                output = f"{Name.title()} has been removed."
                return output
            else:
                output = f"{Name.title()} doesn't belong to you."
                return output
        except:
            output = f"{Name.title()} doesn't seem to exist in this category."
            return output

    def get_char(self, Guild, Name):

        query = {"$text": {"$search": Name}}

        output = self.db[str(Guild)].find(query)

        return output

    def get_char_by_owner(self, Guild, User):
        query = {"owner": User}
        output = self.db[str(Guild)].find(query)

        return output

    def get_one_char(self, Guild, Name, ID):
        query = {"name": Name, "owner": ID}

        return self.db[str(Guild)].find_one(query)

    def get_all_char(self, Guild):
        query = {"name": {"$exists": True}}
        return self.db[str(Guild)].find(query)

    def char_owner(self, Guild, ID, Name):
        query = {"name": Name}

        toCheck = self.db[str(Guild)].find_one(query)["owner"]
        if ID == toCheck:
            return True
        else:
            return False

    def set_field(self, Guild, ID, Name, field, value):
        query = {"name": Name}
        output = (
            self.db[str(Guild)]
            .find_one_and_update(query, {"$set": {field: value}})["name"]
            .title()
        )
        return output

    def unset_field(self, Guild, ID, Name, field):
        query = {"name": Name}
        self.db[str(Guild)].update(query, {"$unset": {field: 1}})

    def change_owner(self, Guild, Name, newOwner):
        query = {"name": Name}
        self.db[str(Guild)].find_one_and_update(query, {"$set": {"owner": newOwner}})
        output = f"{Name.title()}'s ownership has been transferred to <@{newOwner}>."

        return output

    # endregion

    # region Random Tables

    def rand_new(self, Guild, ID, Table):

        try:
            table = self.db.rand[str(Guild)].find_one({"table": Table.lower()})["table"]
            output = f"{table.title()} is already registered."
            return output
        except:
            try:
                entry = {
                    "table": Table.lower(),
                    "user": ID,
                    "pairs": [],
                    "deckMode": "off",
                }
                self.db.rand[str(Guild)].insert_one(entry).inserted_id
                output = f"{Table.title()} was added to the database. You can edit this table using commands via Discord, or in the future, using the Web Editor, found at https://webthunder.herokuapp.com/"
                return output
            except:
                output = f"{Table.title()} could not be added to the database."

    def rand_add(self, Guild, ID, Table, Weight, Value):
        query = {"table": Table.lower()}
        table = self.db.rand[str(Guild)].find_one(query)

        try:
            pubCheck = table["public"]
        except:
            pubCheck = "off"

        if ID == table["user"] or pubCheck == "on":
            pairs = table["pairs"]
            pairs.append([Value, Weight])
            updoot = {"$set": {"pairs": pairs}}
            self.db.rand[str(Guild)].update_one(query, updoot)
            return f"{Table.title()} has been updated!"
        else:
            return f"{Table.title()} doesn't seem to belong to you!"

    def rand_remove(self, Guild, ID, Table, Value):
        query = {"table": Table.lower()}
        table = self.db.rand[str(Guild)].find_one(query)
        if ID == table["user"]:
            pairs = list(table["pairs"])

            try:
                for item in pairs:
                    if item[0] == Value:
                        pairs.remove(item)
                        updoot = {"$set": {"pairs": pairs}}
                        self.db.rand[str(Guild)].update_one(query, updoot)
                        return f"{Value} has been removed from the table."
                    else:
                        pass
            except:
                pass
        return f"{Value} was not found!"

    def rand_delete(self, Guild, ID, Table):
        query = {"table": Table.lower()}
        table = self.db.rand[str(Guild)].find_one(query)
        if ID == table["user"]:
            self.db.rand[str(Guild)].delete_one(query)
            return f"{Table.title()} has been deleted."
        else:
            return f"{Table.title()} doesn't seem to belong to you."

    def rand_get(self, Guild, Table):
        output = self.db.rand[str(Guild)].find_one({"table": Table.lower()})
        return output

    def rand_get_owned(self, User, Guild):
        query = {"user": User}
        output = self.db.rand[str(Guild)].find(query)
        return output

    def rand_get_all(self, Guild):
        output = self.db.rand[str(Guild)].find()
        return output

    def toggle(self, Guild, ID, Table, Setting):
        query = {"table": Table.lower()}
        table = self.db.rand[str(Guild)].find_one(query)

        if ID == table["user"]:
            if Setting == "deck":
                if table["deckMode"] == "off":
                    updoot = {"$set": {"deckMode": "on"}}
                    output = f"Deckmode has been enabled for {Table.title()}."
                else:
                    updoot = {"$set": {"deckMode": "off"}}
                    output = f"Deckmode has been disabled for {Table.title()}."
            elif Setting == "public":
                try:
                    if table["public"] == "off":
                        updoot = {"$set": {"public": "on"}}
                        output = f"{Table.title()} is now public."
                    else:
                        updoot = {"$set": {"public": "off"}}
                        output = f"{Table.title()} is now private."
                except:
                    updoot = {"$set": {"public": "on"}}
                    output = f"{Table.title()} is now public."
            else:
                output = f"{Setting} is not a valid setting to toggle."

        self.db.rand[str(Guild)].update_one(query, updoot)
        return output

    def deck_shuffle(self, Guild, ID, Table):
        query = {"table": Table.lower()}
        table = self.db.rand[str(Guild)].find_one(query)
        if ID == table["user"]:

            while len(table["spentPairs"]) > 0:
                val = table["spentPairs"][0]
                table["pairs"].append(val)
                del table["spentPairs"][0]

            updoot = {
                "$set": {"pairs": table["pairs"], "spentPairs": table["spentPairs"]}
            }
            self.db.rand[str(Guild)].update_one(query, updoot)
        return f"{Table} has been shuffled."

    def deck_draw(self, Guild, ID, mid, Value):
        query = {"_id": mid}
        table = self.db.rand[str(Guild)].find_one(query)
        if ID == table["user"]:
            for v, w in table["pairs"]:

                if v == Value:
                    table["pairs"].remove([v, w])
                    try:
                        table["spentPairs"].append([v, w])
                    except:
                        table["spentPairs"] = []
                        table["spentPairs"].append([v, w])

                else:
                    pass

            try:
                updoot = {
                    "$set": {"pairs": table["pairs"], "spentPairs": table["spentPairs"]}
                }
            except:
                pass

            self.db.rand[str(Guild)].update_one(query, updoot)
            output = f"{Value} has been taken out of the deck."
            return output
        else:
            return f"{Value} does not appear to belong to you."

    # endregion

    # region DM Enablement

    def add_server_proxy(self, Guild, ID):
        query = {"user": ID}
        self.db.proxies.update_one(
            query, {"$set": {"guild": Guild, "user": ID}}, upsert=True
        )

    def get_server_proxy(self, ID):
        query = {"user": ID}
        guild = self.db.proxies.find_one(query)["guild"]
        return int(guild)

    # endregion