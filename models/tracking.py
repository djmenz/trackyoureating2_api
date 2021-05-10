import datetime
from datetime import date
from typing import Optional
from pydantic import BaseModel
import uuid

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