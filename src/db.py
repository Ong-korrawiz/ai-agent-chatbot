from sqlalchemy import Table, Column, String, DateTime, ForeignKey, MetaData, create_engine, Integer
from datetime import datetime
import os
from dotenv import load_dotenv


load_dotenv()  # Load environment variables from .env file
metadata = MetaData()

# User table
user_table = Table(
    'user',
    metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('user_uuid', String(36), unique=True, nullable=False),
    Column('user_name', String(255), nullable=False),
    Column('user_metadata', String, nullable=True)
)

# Chat history table
chat_history_table = Table(
    'chathistory',
    metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('user_uuid', String(36), ForeignKey('user.user_uuid'), nullable=False),
    Column('role', String(50), nullable=False),
    Column('content', String, nullable=False),
    Column('timestamp', DateTime, default=datetime.utcnow, nullable=False),
    Column('messenger_timestamp', String, nullable=True)
)

all_tables_names = metadata.tables.keys()