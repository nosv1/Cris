import mysql.connector
import os
from dotenv import load_dotenv

load_dotenv()


class Database:
    def __init__(self, database_name: str):
        self.database_name = database_name

    def connect(self):
        self.connection = mysql.connector.connect(
            host=os.getenv("DB_HOST"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            database=self.database_name,
            charset="utf8mb4",
            use_unicode=True,
            buffered=True,
        )
        self.cursor = self.connection.cursor()

    def commit(self):
        self.connection.commit()

    def close(self):
        self.connection.close()
