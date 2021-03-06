import os
import databases
from pathlib import Path
import json
import sqlalchemy
from sqlalchemy.orm import sessionmaker

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base


# define database connections

# If environment vars ready, use them, otherwise load from file
if os.getenv("TYE2_DB_ENDPOINT", "ENV_NOT_SET") != "ENV_NOT_SET":
    host_server = os.getenv("TYE2_DB_ENDPOINT")
    db_password_secret = os.getenv("TYE2_DB_PASSWORD")
    db_username_secret = os.getenv("TYE2_DB_USERNAME")
    db_database_name_secret = os.getenv("TYE2_DB_DATABASE_NAME")
    db_database_port_secret = os.getenv("TYE2_DB_DATABASE_PORT")
	
else:
    file = Path('settings.json').absolute()
    with open('settings.json') as fin:
        settings = json.load(fin)
        db_password_secret = settings.get('db_password')
        db_username_secret = settings.get('db_username')
        db_database_name_secret = settings.get('db_database_name')
        db_database_port_secret = settings.get('db_database_port')
        host_server = settings.get('db_endpoint')

# Set up the database object
db_server_port = db_database_port_secret
database_name = db_database_name_secret
db_username = db_username_secret
db_password = db_password_secret
ssl_mode = 'disable' #prefer
DATABASE_URL = 'postgresql://{}:{}@{}:{}/{}?sslmode={}'.format(db_username, db_password, host_server, db_server_port, database_name, ssl_mode)
database = databases.Database(DATABASE_URL)

metadata = sqlalchemy.MetaData()
engine = sqlalchemy.create_engine(DATABASE_URL, pool_size=3, max_overflow=0)
metadata.create_all(engine)

#os.getenv("TYE2_SECRET_KEY")
#session = sessionmaker()
#session.configure(bind=engine)

#SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False,)

#Base = declarative_base()

# def get_db():
#     db = SessionLocal()
#     try:
#         yield db
#     finally:
#         db.close()


async def get_database():
    if not database.is_connected:
        await database.connect()    
    return database