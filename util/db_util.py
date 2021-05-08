import sqlite3
from util.config_options import ConfigOption


class DBUtil:
    def __init__(self, db_name, ratings_table_name, reviewed_memes_table_name, config_table_name, responses_table_name,
                 banned_domain_table_name):
        self.db = sqlite3.connect(db_name, isolation_level=None)
        self.cursor = self.db.cursor()
        self.ratings_table_name = ratings_table_name
        self.reviewed_memes_table_name = reviewed_memes_table_name
        self.config_table_name = config_table_name
        self.responses_table_name = responses_table_name
        self.banned_domain_table_name = banned_domain_table_name

    def create_tables(self):
        # create table to store ratings
        self.cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {self.ratings_table_name}(
                    user_id INTEGER,
                    kek INTEGER DEFAULT 1,
                    cringe INTEGER,
                    cursed INTEGER
                );
        """)

        # create table to store already rated meme ids
        self.cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS {self.reviewed_memes_table_name}(
                    message_id INTEGER
                );
        """)

        # create table to store configuration options
        self.cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS config_options(
                    {ConfigOption.prefix.name} INTEGER DEFAULT 62,
                    {ConfigOption.bully_abdur.name} INTEGER DEFAULT 1,
                    {ConfigOption.send_ayy_lmao.name} INTEGER DEFAULT 1,
                    {ConfigOption.send_ping_pong.name} INTEGER DEFAULT 1,
                    {ConfigOption.send_noot_noot.name} INTEGER DEFAULT 1,
                    {ConfigOption.meme_reviewer_role.name} INTEGER DEFAULT -1,
                    {ConfigOption.admin_role.name} INTEGER DEFAULT -1,
                    {ConfigOption.meme_review_channel.name} INTEGER DEFAULT -1,
                    {ConfigOption.enforce_domain_blacklist.name} INTEGER DEFAULT 1
                );
        """)

        # create table to store responses for bully_abdur
        self.cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS {self.responses_table_name}(
                    response TEXT
                );
        """)

        self.cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS {self.banned_domain_table_name}(
                    domain TEXT
                );
        """)
        self.db.commit()

        if self.cursor.execute(f"SELECT * FROM {self.config_table_name};").fetchone() is None:
            print("config table is empty, setting default values now")
            self.cursor.execute(f"INSERT INTO {self.config_table_name} VALUES (62, 1, 1, 1, 1, -1, -1, -1, 1);")
        self.db.commit()

    def __add_first_rating(self, user_id: int, rating: str):
        if rating == 'kek':
            self.cursor.execute(
                f"INSERT INTO {self.ratings_table_name} VALUES ({user_id}, 1, 0, 0);"
            )
        elif rating == 'cringe':
            self.cursor.execute(
                f"INSERT INTO {self.ratings_table_name} VALUES ({user_id}, 0, 1, 0);"
            )
        elif rating == 'cursed':
            self.cursor.execute(
                f"INSERT INTO {self.ratings_table_name} VALUES ({user_id}, 0, 0, 1);"
            )

    def set_stat(self, user_id: int, operation: str, amount: int, rating: str):
        possible_categories = ["kek", "cringe", "cursed"]
        ops = ["add", "subtract"]
        if rating not in possible_categories:
            return
        if operation not in ops:
            return
        row = self.cursor.execute(
            f"SELECT * FROM {self.ratings_table_name} WHERE user_id = {user_id};"
        ).fetchone()
        if row is None or len(row) == 0:
            self.__add_first_rating(user_id, rating)
        else:
            if operation == "subtract":
                amount *= -1  # make the amount negative if you are subtracting
            self.cursor.execute(
                f"UPDATE {self.ratings_table_name} SET {rating} = {rating} + {amount} WHERE user_id = {user_id};"
            )
        self.db.commit()

    def add_meme_to_reviewed(self, message_id: int):
        self.cursor.execute(
            f"INSERT INTO {self.reviewed_memes_table_name} VALUES ({message_id});"
        )
        self.db.commit()

    def remove_meme_from_reviewed(self, message_id):
        self.cursor.execute(
            f"""
                DELETE FROM {self.reviewed_memes_table_name} WHERE rowid = 
                    (SELECT MIN(rowid) FROM {self.reviewed_memes_table_name} WHERE message_id = {message_id})
            """
        )
        self.db.commit()

    def get_last_rated_meme(self):
        row = self.cursor.execute(
            f"SELECT * FROM {self.reviewed_memes_table_name} ORDER BY rowid DESC LIMIT 1;"
        ).fetchone()
        return row[0]

    def get_user_data(self, user_id: int):
        row = self.cursor.execute(
            f"SELECT * FROM {self.ratings_table_name} WHERE user_id = {user_id};"
        ).fetchone()
        return row

    def get_all_user_data(self):
        data = self.cursor.execute(
            f"SELECT * FROM {self.ratings_table_name};"
        ).fetchall()
        return data

    def author_is_in_db(self, user_id: int) -> bool:
        if len(self.get_user_data(user_id)) != 0:
            return True
        return False

    def meme_already_reviewed(self, message_id) -> bool:
        row = self.cursor.execute(
            f"SELECT * FROM {self.reviewed_memes_table_name} WHERE message_id = {message_id};"
        ).fetchall()
        if len(row) != 0:
            return True
        else:
            return False

    # functions for config stuff
    def get_config_option(self, param: ConfigOption):
        index = param.value
        row = self.cursor.execute(
            f"SELECT * FROM {self.config_table_name};"
        ).fetchone()
        try:
            return row[index]
        except IndexError:
            raise ValueError("Invalid config option")

    def set_config_option(self, param: ConfigOption, value: int):
        self.cursor.execute(
            f"UPDATE {self.config_table_name} SET {param.name} = {value};"
        )
        self.db.commit()

    # functions relating to the responder system
    def get_responses(self):
        row = self.cursor.execute(
            f"SELECT rowid, response FROM {self.responses_table_name};"
        ).fetchall()
        return row

    def add_response(self, response: str):
        self.cursor.execute(
            f"INSERT INTO {self.responses_table_name} VALUES(\"{response}\");"
        )
        self.db.commit()

    def remove_response(self, resp_id: int):
        self.cursor.execute(
            f"DELETE FROM {self.responses_table_name} WHERE rowid = {resp_id}"
        )
        self.cursor.execute(
            f"VACUUM;"
        )
        self.db.commit()

    # functions for the domain blacklist
    def get_banned_domains(self):
        row = self.cursor.execute(
            f"SELECT rowid, domain FROM {self.banned_domain_table_name};"
        ).fetchall()
        return row

    def add_domain_to_blacklist(self, domain: str):
        self.cursor.execute(
            f"INSERT INTO {self.banned_domain_table_name} VALUES(\"{domain}\");"
        )
        self.db.commit()

    def remove_domain_from_blacklist(self, domain_id: int):
        self.cursor.execute(
            f"DELETE FROM {self.banned_domain_table_name} WHERE rowid = {domain_id};"
        )
        self.cursor.execute(
            f"VACUUM;"
        )
        self.db.commit()
