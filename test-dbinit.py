import pytest
from pytest_mongodb.plugin import mongomock
from pytest_mongodb.plugin import pymongo
from dbinit import lt_db


bad_config = {}

good_config = {
    "user": "test",
    "pass": "test",
    "host": "127.0.0.1",
    "port": 27017,
    "dbname": "users",
}


class Testdb:
    @pytest.fixture()
    def db(self):
        db = lt_db(good_config)
        return db

    def test_config(self, db):
        """
        test_config Tests that a valid config is not altered

        :param db: lt_db database object
        :type db: lt_db
        """
        assert db.user == good_config["user"]
        assert db.password == good_config["pass"]
        assert db.host == good_config["host"]
        assert db.port == good_config["port"]
        assert db.dbname == good_config["dbname"]

    def test_invalid_config(self):
        """
        test_invalid_config Tests that an invalid config raises exception
        """
        with pytest.raises(Exception):
            assert lt_db(bad_config)

    def test_connection(self, db):
        """
        test_connection [summary]

        :param db: lt_db database object
        :type db: lt_db
        """
        db.connect()
        assert isinstance(db.client, pymongo.mongo_client.MongoClient)

    def test_db_init(self, db):
        """
        test_db_init test database init

        :param db: lt_db database object
        :type db: lt_db
        """

        db.connect()
        db.db_init()
        assert isinstance(db.db, pymongo.database.Database)

    def test_collections(self, mongodb):
        assert "character" in mongodb.list_collection_names()
        assert "initentry" in mongodb.list_collection_names()
        assert "init" in mongodb.list_collection_names()

    def test_init_add(self, db, mongodb):
        """
        test_init_add Tests adding init for character

        :param db: lt_db database object
        :type db: lt_db
        """
        db.db = mongodb
        guild = "init"
        category = "entry"
        name = "sneg"
        char_id = 1273461827364134
        init = 5
        pass
