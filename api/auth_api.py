from typing import List, Optional
from datetime import datetime, timedelta
import databases
import fastapi
from fastapi import Depends, FastAPI, HTTPException, status
from pydantic.main import BaseModel
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
import sqlalchemy
from sqlalchemy.sql.elements import _as_truncated
from starlette import status

from jose import JWTError, jwt
from passlib.context import CryptContext

#from services import openweather_service, report_service

from pathlib import Path
import json

router = fastapi.APIRouter()
metadata = sqlalchemy.MetaData()

from fastapi.security import OAuth2PasswordBearer

# define database connections
file = Path('settings.json').absolute()
with open('settings.json') as fin:
    settings = json.load(fin)
    db_password_secret = settings.get('db_password')
    db_username_secret = settings.get('db_username')
    db_database_name_secret = settings.get('db_database_name')
    db_database_port_secret = settings.get('db_database_port')

    SECRET_KEY = settings.get("SECRET_KEY")

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Set up the database object
host_server = 'localhost'
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

users = sqlalchemy.Table(
    "users",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True),
    sqlalchemy.Column("username", sqlalchemy.String),
    sqlalchemy.Column("full_name", sqlalchemy.String),
    sqlalchemy.Column("email", sqlalchemy.String),
    sqlalchemy.Column("hashed_password", sqlalchemy.String),
    sqlalchemy.Column("enabled", sqlalchemy.Boolean),
)


class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class User(BaseModel):
    id: int
    username: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    enabled: Optional[bool] = None

class UserInDB(User):
    hashed_password: str

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_user(db, username: str):
    if username in db:
        user_dict = db[username]
        return UserInDB(**user_dict)    

def verify_password(plain_password, hashed_password):
    #print(pwd_context.hash(plain_password))
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


@router.get("/items/")
async def read_items(token: str = Depends(oauth2_scheme)):
    return {"token": token}

async def authenticate_user(username: str, password: str):
    query = users.select().where(users.c.username == username)
    if not database.is_connected:
        await database.connect()
    user_record = await database.fetch_all(query)
    user_dict = dict(user_record[0])
    user = UserInDB(**user_dict)

    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user


async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception

    query = users.select().where(users.c.username == token_data.username)
    if not database.is_connected:
        await database.connect()
    user_record = await database.fetch_all(query)

    user_dict = dict(user_record[0])
    user = UserInDB(**user_dict)
    print(user)   


    if user is None:
        raise credentials_exception
    return user

async def get_current_active_user(current_user: User = Depends(get_current_user)):
    print(current_user)
    if not current_user.enabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

@router.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user =  await authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/users/me/", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    return current_user
    
#import pdb; pdb.set_trace()