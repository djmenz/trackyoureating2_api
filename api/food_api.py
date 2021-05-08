from datetime import date
from typing import List, Optional
import databases
import fastapi
from fastapi import Depends, FastAPI, HTTPException, status
from pydantic.main import BaseModel
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
import sqlalchemy
from sqlalchemy.sql.elements import _as_truncated
from starlette import status
from datetime import date, datetime, time, timedelta

from models.location import Location
from models.reports import Report, ReportSubmittal
from services import openweather_service, report_service
from sqlalchemy.orm import sessionmaker

from api.auth_api import get_current_active_user, User
from pathlib import Path
import json

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

class FoodDataIn(BaseModel):
    name: str
    extended_info: str
    calories: float
    protein: float
    carbs: float
    fats: float

class FoodData(BaseModel):
    id: int
    name: str
    extended_info: str
    creator_id: int
    calories: float
    protein: float
    carbs: float
    fats: float

class TrackingDataIn(BaseModel):
    #user_id: int
    food_id: int
    quantity: float
    date: date
    
class TrackingData(BaseModel):
    id: int
    user_id: int
    food_id: int
    quantity: float
    date: date

class TrackingDataMerged(BaseModel):
    id: int
    user_id: int
    food_id: int
    quantity: float
    date: date
    name: str
    calories: float
    protein: float
    carbs: float
    fats: float    
    
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

class NoteIn(BaseModel):
    text: str
    completed: bool

class Note(BaseModel):
    id: int
    text: str
    completed: bool

notes = sqlalchemy.Table(
    "notes",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True),
    sqlalchemy.Column("text", sqlalchemy.String),
    sqlalchemy.Column("completed", sqlalchemy.Boolean),
)

@router.get("/api/notes", response_model=List[Note], status_code = status.HTTP_200_OK)
async def read_notes(skip: int = 0, take: int = 20):
    query = notes.select().offset(skip).limit(take)
    if not database.is_connected:
        await database.connect()
    return await database.fetch_all(query)
	
@router.post('/api/notes', name='add_report', status_code=201, response_model=Note)
async def reports_post(note_submitted: NoteIn):
    query = notes.insert().values(text=note_submitted.text,completed=note_submitted.completed)
    await database.execute(query)
    return Note(id=1, text="hello", completed=False )

@router.delete('/api/notes', name='delete_report', status_code=201, response_model=bool)
async def reports_delete(id_to_del: int):
    print(f"Delete: {id_to_del}")

    if not database.is_connected:
        await database.connect()
    
    query = notes.delete().where(notes.c.id ==id_to_del)
    await database.execute(query)

    return True

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


@router.get("/api/tracking", response_model=List[TrackingData], status_code = status.HTTP_200_OK)
async def read_tracking(skip: int = 0, take: int = 20, current_user: User = Depends(get_current_active_user)):
    print(current_user)
    if not database.is_connected:
        await database.connect()    

    result = engine.execute('SELECT * FROM tracking inner join food_data_masterlist on tracking.food_id = food_data_masterlist.id WHERE user_id = ' + str(current_user.id))

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
async def delete_tracked_item(id_to_del: int):
    print(f"Delete: {id_to_del}")

    if not database.is_connected:
        await database.connect()
    
    query = tracking.delete().where(tracking.c.id ==id_to_del)
    await database.execute(query)

    return True



@router.delete('/api/notes', name='delete_report', status_code=201, response_model=bool)
async def reports_delete(id_to_del: int):
    print(f"Delete: {id_to_del}")

    if not database.is_connected:
        await database.connect()
    
    query = notes.delete().where(notes.c.id ==id_to_del)
    await database.execute(query)

    return True



#
#
#@router.get('/api/weather/{city}')
#async def weather(loc: Location = Depends(), units: Optional[str] = 'metric'):
#
#	report = await openweather_service.get_report_async(loc.city, loc.state, loc.country, units)
#	return report
#
#
#@router.get('/api/reports', name='all_reports', response_model=List[Report])
#async def reports_get() -> List[Report]:
#    await report_service.add_report("A", Location(city="Portland"))
#    await report_service.add_report("B", Location(city="NYC"))
#    return await report_service.get_reports()
#
#
#@router.post('/api/reports', name='add_report', status_code=201, response_model=Report)
#async def reports_post(report_submittal: ReportSubmittal) -> Report:
#    d = report_submittal.description
#    loc = report_submittal.location
#
#    return await report_service.add_report(d, loc)
#
#
#

