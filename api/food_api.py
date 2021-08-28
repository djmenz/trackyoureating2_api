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

import datasource
from models.tracking import FoodDataIn, FoodData, TrackingDataIn, TrackingData,TrackingDataMerged, TemplateInfoIn, TemplateInfo, TemplateDataIn, TemplateData, TemplatesDataMerged
from sqlalchemy.orm import sessionmaker

from api.auth_api import get_current_active_user, User
from pathlib import Path
import json

from fastapi.encoders import jsonable_encoder

router = fastapi.APIRouter()
metadata = sqlalchemy.MetaData()

from fastapi.security import OAuth2PasswordBearer

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
    sqlalchemy.Column("consumed", sqlalchemy.Boolean),
)

template_info = sqlalchemy.Table(
    "template_info",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True),
    sqlalchemy.Column("creator_id", sqlalchemy.Integer),
    sqlalchemy.Column("name", sqlalchemy.Integer),
    sqlalchemy.Column("extended_info", sqlalchemy.Float),
)  

template_data = sqlalchemy.Table(
    "template_data",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True),
    sqlalchemy.Column("creator_id", sqlalchemy.Integer),
    sqlalchemy.Column("template_id", sqlalchemy.Integer),
    sqlalchemy.Column("food_id", sqlalchemy.Integer),
    sqlalchemy.Column("quantity", sqlalchemy.Float),
) 

@router.get("/api/foods", response_model=List[FoodData], status_code = status.HTTP_200_OK)
async def read_foods_for_current_user(skip: int = 0, take: int = 20, current_user: User = Depends(get_current_active_user)):
    # print(current_user)

    database =  await datasource.get_database()
    query = food_data_masterlist.select().offset(skip).limit(take)

    return await database.fetch_all(query)

	
@router.post('/api/foods', name='add_food_db_entry', status_code=201, response_model=bool)
async def create_food_db_entry(food_submitted: FoodDataIn, current_user: User = Depends(get_current_active_user)):
    database =  await datasource.get_database()
    
    query = food_data_masterlist.insert().values(
        name=food_submitted.name,
        extended_info=food_submitted.extended_info,
        creator_id=current_user.id,
        calories=food_submitted.calories,
        protein=food_submitted.protein,
        carbs=food_submitted.carbs,
        fats=food_submitted.fats,
        )
  
    await database.execute(query)
    return True
    
@router.get("/api/foods/{food_id}", response_model=FoodData, status_code = status.HTTP_200_OK)
async def read_foods(food_id:int, current_user: User = Depends(get_current_active_user)):
    database =  await datasource.get_database()

    query = "SELECT * FROM food_data_masterlist  WHERE id = :food_id"
    row = await database.fetch_one(query=query, values = {'food_id':food_id})
    
    return row

@router.patch("/api/foods/{food_id}", response_model=FoodData, status_code = status.HTTP_200_OK)
async def patch_foods(food_id:int, new_attributes: dict, current_user: User = Depends(get_current_active_user)):

    database =  await datasource.get_database()

    # Get old item
    query = 'SELECT * FROM food_data_masterlist WHERE id =:food_id '
    row = await database.fetch_one(query=query, values = {'food_id': food_id})

    if 'id' in new_attributes:
        new_attributes.pop('id')

    stored_item_data = row
    stored_item_model = FoodData(**stored_item_data)
    update_data = stored_item_model.copy(update = new_attributes)

    # update back into database
    query = food_data_masterlist.update().where(food_data_masterlist.c.id == food_id).values(update_data.__dict__)
    await database.execute(query)

    query = "SELECT * FROM food_data_masterlist  WHERE id = :food_id"
    row = await database.fetch_one(query=query, values = {'food_id':food_id})

    return row

# Need to get this and the patch one below working in swagger (seems to work with curl??)
@router.get("/api/tracking/{food_id}", response_model=TrackingData, status_code = status.HTTP_200_OK)
async def read_tracking_by_id(food_id:int, current_user: User = Depends(get_current_active_user)):
    database =  await datasource.get_database()

    query = "SELECT * FROM tracking  WHERE id = :food_id"
    row = await database.fetch_one(query=query, values = {'food_id':food_id})
    
    return row

@router.patch("/api/tracking/{food_id}", response_model=TrackingData, status_code = status.HTTP_200_OK)
async def patch_tracking(food_id:int, new_attributes: dict, current_user: User = Depends(get_current_active_user)):

    database =  await datasource.get_database()
    # print(food_id)
    # Get old item
    query = 'SELECT * FROM tracking WHERE id =:food_id '
    row = await database.fetch_one(query=query, values = {'food_id': food_id})

    if 'id' in new_attributes:
        new_attributes.pop('id')

    stored_item_data = row
    stored_item_model = TrackingData(**stored_item_data)
    update_data = stored_item_model.copy(update = new_attributes)

    # update back into database
    query = tracking.update().where(tracking.c.id == food_id).values(update_data.__dict__)
    await database.execute(query)

    query = "SELECT * FROM tracking  WHERE id = :food_id"
    row = await database.fetch_one(query=query, values = {'food_id':food_id})

    return row


@router.get("/api/tracking", response_model=List[TrackingData], status_code = status.HTTP_200_OK)
async def read_tracking(skip: int = 0, take: int = 20, current_user: User = Depends(get_current_active_user)):
    database =  await datasource.get_database()   

    query = "SELECT * FROM tracking  WHERE user_id = :user_id"
    rows = await database.fetch_all(query=query, values={"user_id": current_user.id})

    return(rows)

@router.get("/api/trackingmerged", response_model=List[TrackingDataMerged], status_code = status.HTTP_200_OK)
async def read_tracking(skip: int = 0, take: int = 20, current_user: User = Depends(get_current_active_user)):
    database =  await datasource.get_database()

    query = '''SELECT tracking.id, tracking.user_id, tracking.food_id, tracking.quantity, 
    tracking.date, tracking.consumed, food_data_masterlist.name, food_data_masterlist.calories, food_data_masterlist.protein, 
    food_data_masterlist.carbs, food_data_masterlist.fats                         
    FROM tracking inner join food_data_masterlist on tracking.food_id = food_data_masterlist.id WHERE user_id = :user_id'''

    rows = await database.fetch_all(query = query, values = {'user_id' : current_user.id})   

    return(rows)

# This needs to be completed and tested to work, currently is just a stub
@router.get("/api/templatesmerged", response_model=List[TemplatesDataMerged], status_code = status.HTTP_200_OK)
async def read_tracking(skip: int = 0, take: int = 20, current_user: User = Depends(get_current_active_user)):
    database =  await datasource.get_database()

    query = '''SELECT template_data.id, template_data.food_id, template_data.quantity, template_data.creator_id, template_data.template_id,
    food_data_masterlist.name, food_data_masterlist.calories, food_data_masterlist.protein, 
    food_data_masterlist.carbs, food_data_masterlist.fats                         
    FROM template_data inner join food_data_masterlist on template_data.food_id = food_data_masterlist.id WHERE template_data.creator_id = :user_id'''

    rows = await database.fetch_all(query = query, values = {'user_id' : current_user.id})   

    return(rows)

@router.post('/api/tracking', name='add_food_tracking_entry', status_code=201, response_model=bool)
async def create_food_db_entry(tracking_submitted: TrackingDataIn, current_user: User = Depends(get_current_active_user)):
    database =  await datasource.get_database() 
    query = tracking.insert().values(
        user_id=current_user.id,
        food_id=tracking_submitted.food_id,
        quantity=tracking_submitted.quantity,
        date=tracking_submitted.date,
        consumed=tracking_submitted.consumed,
        )

    await database.execute(query)
    return True

@router.delete('/api/tracking', name='delete_tracked_item', status_code=201, response_model=bool)
async def delete_tracked_item(id_to_del: int, current_user: User = Depends(get_current_active_user)):

    database =  await datasource.get_database() 
    query = tracking.delete().where(tracking.c.id == id_to_del)
    await database.execute(query)

    return True

@router.post('/api/templateinfo', name='add_template_info_entry', status_code=201, response_model=int)
async def create_template(tracking_submitted: TemplateInfoIn, current_user: User = Depends(get_current_active_user)):
    database =  await datasource.get_database() 

    query = template_info.insert().values(
        creator_id=current_user.id,
        name=tracking_submitted.name,
        extended_info=tracking_submitted.extended_info,
        )

    res = await database.execute(query)
    return res

@router.get("/api/templateinfo", response_model=List[TemplateInfo], status_code = status.HTTP_200_OK)
async def read_templates(skip: int = 0, take: int = 20, current_user: User = Depends(get_current_active_user)):
    
    database =  await datasource.get_database()   
    query = "SELECT * FROM template_info WHERE creator_id = :creator_id"
    rows = await database.fetch_all(query=query, values={"creator_id": current_user.id})
    
    return rows 

@router.delete('/api/templateinfo', name='delete', status_code=201, response_model=bool)
async def delete_template(id_to_del: int, current_user: User = Depends(get_current_active_user)):

    database =  await datasource.get_database() 
    query = template_info.delete().where(template_info.c.id == id_to_del)
    await database.execute(query)

    return True

@router.post('/api/templatedata', name='add_template_data_entry', status_code=201, response_model=bool)
async def create_template_data_entry(submitted: TemplateDataIn, current_user: User = Depends(get_current_active_user)):
    database =  await datasource.get_database() 

    query = template_data.insert().values(
        creator_id=current_user.id,
        food_id=submitted.food_id,
        quantity=submitted.quantity,
        template_id=submitted.template_id,
        )

    await database.execute(query)
    return True

@router.get("/api/templatedata", response_model=List[TemplateData], status_code = status.HTTP_200_OK)
async def read_template_data(skip: int = 0, take: int = 20, current_user: User = Depends(get_current_active_user)):
    
    database =  await datasource.get_database()   
    query = "SELECT * FROM template_data  WHERE creator_id = :creator_id"
    rows = await database.fetch_all(query=query, values={"creator_id": current_user.id})

    return rows 

@router.delete('/api/templatedata', name='delete', status_code=201, response_model=bool)
async def delete_tracked_template_item(id_to_del: int, current_user: User = Depends(get_current_active_user)):

    database =  await datasource.get_database() 
    query = template_data.delete().where(template_data.c.id == id_to_del)
    await database.execute(query)

    return True
