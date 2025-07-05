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
    Column('user_uuid', String(36), primary_key=True),
    Column('user_name', String(255), nullable=False),
    Column('user_metadata', String, nullable=True)
)

# Chat history table
chat_history_table = Table(
    'chat_history',
    metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('user_uuid', String(36), ForeignKey('user.user_uuid'), nullable=False),
    Column('role', String(50), nullable=False),
    Column('content', String, nullable=False),
    Column('timestamp', DateTime, default=datetime.utcnow, nullable=False)
)

# Create tables
def create_tables(database_url):
    """Create all tables in the database"""
    engine = create_engine(database_url)
    metadata.create_all(engine)
    return engine


class User:
    def __init__(self):
        self.engine = create_engine(os.getenv('POSTGRES_URL'))

    def insert(self, uuid: str, name: str, metadata: str = None):
        """Insert a new user into the database"""
        conn = self.engine.connect()

        conn.execute(
            user_table.insert().values(
                user_uuid=uuid,
                user_name=name,
                user_metadata=metadata if metadata else ""
            )
        )

    def read(self, user_uuid: str):
        """Read user information from the database"""
        conn = self.engine.connect()
        result = conn.execute(
            user_table.select().where(user_table.c.user_uuid == user_uuid)
        ).fetchone()
        return result
    

    def update(self, user_uuid: str, name: str = None, metadata: str = None):
        """Update user information in the database"""
        conn = self.engine.connect()
        update_values = {}
        if name:
            update_values['user_name'] = name
        if metadata:
            update_values['user_metadata'] = metadata

        conn.execute(
            user_table.update().where(user_table.c.user_uuid == user_uuid).values(update_values)
        )

    def has_user(self, user_uuid: str) -> bool:
        """Check if a user exists in the database"""
        conn = self.engine.connect()
        result = conn.execute(
            user_table.select().where(user_table.c.user_uuid == user_uuid)
        ).fetchone()
        return bool(result) if result else False


class ChatHistory:
    def __init__(self):
        self.engine = create_engine(os.getenv('POSTGRES_URL'))

    def insert(self, user_uuid: str, role: str, content: str):
        """Insert a new chat message into the database"""
        conn = self.engine.connect()
        conn.execute(
            chat_history_table.insert().values(
                user_uuid=user_uuid,
                role=role,
                content=content,
            )
        )

    def read(self, user_uuid):
        conn = self.engine.connect()
        """Read chat history for a specific user"""
        result = conn.execute(
            chat_history_table
            .select()
            .where(
                chat_history_table.c.user_uuid == user_uuid
                )
        ).fetchall()
        return result

    def delete(self, id):
        conn = self.engine.connect()
        """Delete a chat message from the database"""
        conn.execute(
            chat_history_table.delete().where(chat_history_table.c.id == id)
        )
    

# Example usage
if __name__ == "__main__":
    import uuid
    from sqlalchemy import insert
    import os
    from dotenv import load_dotenv

    load_dotenv()  # Load environment variables from .env file

    postgres_url = os.getenv('POSTGRES_URL')
    if not postgres_url:
        raise ValueError("Database URL is not set or invalid.")
    else:
        print(f"Using database URL: {os.getenv('POSTGRES_URL')}")
    # Example: Insert data using Core approach
    engine = create_tables(postgres_url)
    with engine.connect() as conn:
        # Insert user
        user_uuid = str(uuid.uuid4())
        conn.execute(
            insert(user_table).values(
                user_uuid=user_uuid,
                user_name="Jane Doe",
                user_metadata='{"preferences": {"language": "en"}}'
            )
        )
        
        # Insert chat message
        conn.execute(
            insert(chat_history_table).values(
                user_uuid=user_uuid,
                role="assistant",
                content="Hello! How can I help you today?"
            )
        )
        
        conn.commit()
    
    print("Tables created and sample data inserted successfully!")