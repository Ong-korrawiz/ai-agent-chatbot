import os
from pathlib import Path
import sys

from google.cloud.sql.connector import Connector, IPTypes

import sqlalchemy
import pg8000
from logging import getLogger
from sqlalchemy.dialects.postgresql import insert


sys.path.append(str(Path(__file__).parents[2]))

from src.settings import (
    INSTANCE_CONNECTION_NAME,
    DB_USER,
    DB_PASSWORD,
    DB_NAME,
)
from src.db import metadata, chat_history_table, user_table, all_tables_names
from src._types import Message


logger = getLogger(__name__)


class CloudSql():
    def __init__(self):
        """Initialize the Cloud SQL connector with environment variables"""
        self._connector = Connector()
        self._instance_connection_name = INSTANCE_CONNECTION_NAME
        self._db_user = DB_USER
        self._db_password = DB_PASSWORD
        self._db_name = DB_NAME
        self._driver = "pg8000"
        self._tables = all_tables_names

    def get_conn(self):
        conn = self._connector.connect(
            self._instance_connection_name,
            self._driver,
            user=self._db_user,
            password=self._db_password,
            db=self._db_name,
        )
        return conn

    def get_engine(self):
        """Create a SQLAlchemy engine for the Cloud SQL instance"""
        return sqlalchemy.create_engine(
            "postgresql+pg8000://",
            creator=self.get_conn,
        )

class CloudSqlManager(CloudSql):
    def __init__(self):
        super().__init__()
        self.engine = self.get_engine()

    def has_table(self, table_name: str) -> bool:
        print("self.engine", self.engine, "table name", table_name)
        return sqlalchemy.inspect(self.engine).has_table(table_name)
    
    def validate_tables(self):
        """Check if all required tables exist in the database"""
        for table_name in self._tables:
            if not self.has_table(table_name):
                logger.error(f"Table {table_name} does not exist.")
                return False
        return True

    def create_table(self):
        """Create the chat history table if it does not exist"""
        if self.validate_tables():
            logger.info("All required tables already exist.")
            return
        
        try:
            metadata.create_all(self.engine, checkfirst=True)
            logger.info("Tables created successfully.")
        except Exception as e:
            print(f"Error creating tables: {e}")
            raise e
        
    def re_create_tables(self):
        """Recreate all tables in the database"""
        try:
            metadata.drop_all(self.engine)
            metadata.create_all(self.engine)
            logger.info("All tables recreated successfully.")
        except Exception as e:
            print(f"Error recreating tables: {e}")
            raise e
        
    def get_engine(self):
        return super().get_engine()


class ChatHistoryTable(CloudSql):
    def __init__(self, engine=None):
        super().__init__()
        self.engine = engine if engine else self.get_engine()
        self._conn = self.engine.connect()


    def insert(self, user_uuid: str, role: str, content: str, messenger_timestamp: str = None):
        """Insert a new chat message into the database"""
        self._conn.execute(
            chat_history_table.insert().values(
                user_uuid=user_uuid,
                role=role,
                content=content,
                messenger_timestamp=messenger_timestamp if messenger_timestamp else ""
            )
        )
        self._conn.commit()
    
    def read(self, user_uuid: str) -> list:
        """Read chat history for a specific user"""
        result = self._conn.execute(
            chat_history_table.select().where(chat_history_table.c.user_uuid == user_uuid)
        ).fetchall()
        return result
    
    def get_chat_history(self, user_uuid: str) -> list[Message]:
        """Get chat history for a specific user"""
        messages = self.read(user_uuid)
        return [
            Message(role=msg.role, content=msg.content, messenger_timestamp=msg.messenger_timestamp) for msg in messages 
            if msg.role in ["user", "assistant"]
        ]


class UserTable(CloudSql):
    def __init__(self, engine=None):
        super().__init__()
        self.engine = self.get_engine() if engine is None else engine
        self._conn = self.engine.connect()


    def insert(self, user_uuid: str, name: str = None, metadata: str = None):
        """Insert a new user into the database"""
        try:
            self._conn.execute(
                insert(user_table).values(
                    user_uuid=user_uuid,
                    user_name=name if name else "",
                    user_metadata=metadata if metadata else ""
                ).on_conflict_do_update(
                    index_elements=['user_uuid'],
                    set_=dict(
                        user_name=name if name else "",
                        user_metadata=metadata if metadata else ""
                    )
                )
            )

            self._conn.commit()
        except sqlalchemy.exc.DatabaseError as e:
            if "duplicate key value violates unique constraint" in str(e):
                logger.warning(f"User with UUID {user_uuid} already exists. Skipping insert.")
            else:
                logger.error(f"Error inserting user: {e}")


    def read(self, user_uuid: str):
        """Read user information from the database"""
        result = self._conn.execute(
            user_table.select().where(user_table.c.user_uuid == user_uuid)
        ).fetchone()
        return result
    

    def get_all_users(self) -> list:
        """Get all users from the database"""
        query = """SELECT * FROM user;"""
        result = self._conn.execute(
            sqlalchemy.text(query)
            ).fetchall()
        return result




