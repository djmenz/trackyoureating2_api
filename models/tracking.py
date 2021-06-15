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
    consumed: bool
    
class TrackingData(BaseModel):
    id: int
    user_id: int
    food_id: int
    quantity: float
    date: date
    consumed: bool

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
    consumed: bool

class TemplatesDataMerged(BaseModel):
    id: int
    template_id: int
    creator_id: int
    food_id: int
    quantity: float
    name: str
    calories: float
    protein: float
    carbs: float
    fats: float

class TemplateInfoIn(BaseModel):
    name: str
    extended_info: str  

class TemplateInfo(BaseModel):
    id: int
    creator_id: int
    name: str
    extended_info: str

class TemplateDataIn(BaseModel):
    food_id: int
    quantity: float
    template_id: int

class TemplateData(BaseModel):
    id: int
    creator_id: int
    template_id: int
    food_id: int
    quantity: float