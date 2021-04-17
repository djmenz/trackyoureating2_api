import json
from typing import List
import databases
import fastapi
from fastapi import FastAPI, status
from pydantic.main import BaseModel
import uvicorn
from pathlib import Path


import sqlalchemy
import urllib
import os

from starlette.requests import Request
from starlette.staticfiles import StaticFiles
from starlette.templating import Jinja2Templates

from services import openweather_service
from api import food_api
from api import auth_api
from views import home

api = fastapi.FastAPI()


def configure():
	configure_routing()
	configure_api_keys()

def configure_api_keys():
	file = Path('settings.json').absolute()
	with open('settings.json') as fin:
		settings = json.load(fin)
		openweather_service.api_key = settings.get('api_key')


def configure_routing():
	api.mount('/static', StaticFiles(directory='static'),name='static')
	api.include_router(home.router)
	api.include_router(auth_api.router)
	api.include_router(food_api.router)


if __name__== '__main__':
	configure()
	uvicorn.run(api,port=8000, host='127.0.0.1')
else:
	configure()

