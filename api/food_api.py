from typing import List, Optional
import databases
import fastapi
from fastapi import Depends, FastAPI, HTTPException, status
from pydantic.main import BaseModel
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
import sqlalchemy
from sqlalchemy.sql.elements import _as_truncated
from sqlalchemy.sql.expression import update
from starlette import status
from datetime import date, datetime, time, timedelta

from models.tracking import FoodDataIn, FoodData, TrackingDataIn, TrackingData,TrackingDataMerged
from sqlalchemy.orm import sessionmaker

from api.auth_api import get_current_active_user, User
from pathlib import Path
import json

from fastapi.encoders import jsonable_encoder

router = fastapi.APIRouter()
metadata = sqlalchemy.MetaData()

from fastapi.security import OAuth2PasswordBearer

db_password_secret: Optional[str] = None

# define database connections
file = Path('settings.json').absolute()
with open('settings.json') as fin:
    settings = json.load(fin)
    db_password_secret = settings.get('db_password')
    db_username_secret = settings.get('db_username')
    db_database_name_secret = settings.get('db_database_name')
    db_database_port_secret = settings.get('db_database_port')

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

session = sessionmaker()
session.configure(bind=engine)
    
food_data_masterlist = sqlalchemy.Table(
    "food_data_masterlist",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True),
    sqlalchemy.Column("name", sqlalchemy.String),
    sqlalchemy.Column("extended_info", sqlalchemy.String),
    sqlalchemy.Column("creator_id", sqlalchemy.String),
    sqlalchemy.Column("calories", sqlalchemy.Float),
    sqlalchemy.Column("protein", sqlalchemy.Float),
    sqlalchemy.Column("carbs", sqlalchemy.Float),
    sqlalchemy.Column("fats", sqlalchemy.Float),
    )


tracking = sqlalchemy.Table(
    "tracking",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True),
    sqlalchemy.Column("user_id", sqlalchemy.Integer),
    sqlalchemy.Column("food_id", sqlalchemy.Integer),
    sqlalchemy.Column("quantity", sqlalchemy.Float),
    sqlalchemy.Column("date", sqlalchemy.Date),
)    

@router.get("/api/foods", response_model=List[FoodData], status_code = status.HTTP_200_OK)
async def read_foods(skip: int = 0, take: int = 20, current_user: User = Depends(get_current_active_user)):
    print(current_user)
    
    # need to get this working
    query = food_data_masterlist.select().offset(skip).limit(take)
    if not database.is_connected:
        await database.connect()
    return await database.fetch_all(query)

	
@router.post('/api/foods', name='add_food_db_entry', status_code=201, response_model=bool)
async def create_food_db_entry(food_submitted: FoodDataIn, current_user: User = Depends(get_current_active_user)):
    query = food_data_masterlist.insert().values(
        name=food_submitted.name,
        extended_info=food_submitted.extended_info,
        creator_id=current_user.id,
        calories=food_submitted.calories,
        protein=food_submitted.protein,
        carbs=food_submitted.carbs,
        fats=food_submitted.fats,
        )

    if not database.is_connected:
        await database.connect()    
    await database.execute(query)
    return True



@router.get("/api/foods/{food_id}", response_model=FoodData, status_code = status.HTTP_200_OK)
async def read_foods(food_id:int, current_user: User = Depends(get_current_active_user)):
    result = engine.execute('SELECT * FROM food_data_masterlist  WHERE id = ' + str(food_id))
    if not database.is_connected:
        await database.connect()
    rows = result.fetchall()
    return rows[0]

# need to get this working
@router.patch("/api/foods/{food_id}", response_model=FoodData, status_code = status.HTTP_200_OK)
async def patch_foods(food_id:int, new_attributes: dict, current_user: User = Depends(get_current_active_user)):

    # Get old item
    result = engine.execute('SELECT * FROM food_data_masterlist WHERE id = ' + str(food_id))
    if not database.is_connected:
        await database.connect()
    rows = result.fetchall()
    stored_item_data = rows[0]
    stored_item_model = FoodData(**stored_item_data)
    update_data = stored_item_model.copy(update = new_attributes)


    # Save new one
    print(update_data)

    # Need to save the new object to the database properly
    result = engine.execute('SELECT * FROM food_data_masterlist WHERE id = ' + str(food_id))
    rows = result.fetchall()

    # non working lines
    #database.query(food_data_masterlist).filter(id=food_id).update(update_data)
    #database.commit()
    
    return rows[0]


@router.get("/api/tracking", response_model=List[TrackingData], status_code = status.HTTP_200_OK)
async def read_tracking(skip: int = 0, take: int = 20, current_user: User = Depends(get_current_active_user)):
    print(current_user)
    if not database.is_connected:
        await database.connect()    

    result = engine.execute('SELECT * FROM tracking  WHERE user_id = ' + str(current_user.id))

    rows = result.fetchall()
    print(rows)     
    
    # query = tracking.select().where(tracking.c.user_id == current_user.id).offset(skip).limit(take)
    # result = engine.execute('SELECT * FROM person WHERE id >= :id', id=3)
    #return await database.fetch_all(query)
    return(rows)

@router.get("/api/trackingmerged", response_model=List[TrackingDataMerged], status_code = status.HTTP_200_OK)
async def read_tracking(skip: int = 0, take: int = 20, current_user: User = Depends(get_current_active_user)):
    print(current_user)
    if not database.is_connected:
        await database.connect()    

    result = engine.execute('''SELECT tracking.id, tracking.user_id, tracking.food_id, tracking.quantity, 
    tracking.date, food_data_masterlist.name, food_data_masterlist.calories, food_data_masterlist.protein, 
    food_data_masterlist.carbs, food_data_masterlist.fats                         
    FROM tracking inner join food_data_masterlist on tracking.food_id = food_data_masterlist.id WHERE user_id = ''' + str(current_user.id))

    rows = result.fetchall()
    print(rows)     

    return(rows)


@router.post('/api/tracking', name='add_food_tracking_entry', status_code=201, response_model=bool)
async def create_food_db_entry(tracking_submitted: TrackingDataIn, current_user: User = Depends(get_current_active_user)):
    query = tracking.insert().values(
        user_id=current_user.id,
        food_id=tracking_submitted.food_id,
        quantity=tracking_submitted.quantity,
        date=tracking_submitted.date,
        )

    if not database.is_connected:
        await database.connect()    
    await database.execute(query)
    return True


@router.delete('/api/tracking', name='delete_tracked_item', status_code=201, response_model=bool)
async def delete_tracked_item(id_to_del: int, current_user: User = Depends(get_current_active_user)):

    if not database.is_connected:
        await database.connect()
    
    query = tracking.delete().where(tracking.c.id ==id_to_del)
    await database.execute(query)

    return True