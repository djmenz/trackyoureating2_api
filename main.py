import json
from typing import List
import databases
import fastapi
from fastapi.middleware.cors import CORSMiddleware

from fastapi import FastAPI, status, Response, Request
from pydantic.main import BaseModel
import uvicorn
from pathlib import Path

import sqlalchemy
import urllib
import os

# from starlette.requests import Request
from starlette.staticfiles import StaticFiles
from starlette.templating import Jinja2Templates

from api import food_api
from api import auth_api
#from views import home

origins = '*'

api = fastapi.FastAPI()

api.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=['*'],
)

def configure():
	configure_routing()

def configure_routing():
	api.mount('/static', StaticFiles(directory='static'),name='static')
	#api.include_router(home.router)
	api.include_router(auth_api.router)
	api.include_router(food_api.router)

if __name__== '__main__':
	configure()
	if os.getenv("TYE2_DEPLOYMENT_HOST_IP", "ENV_NOT_SET") != "ENV_NOT_SET":
		deployment_host = os.getenv("TYE2_DEPLOYMENT_HOST_IP")
	else:
		file = Path('settings.json').absolute()
		with open('settings.json') as fin:
			settings = json.load(fin)
			deployment_host = settings.get('deployment_host_ip')
	uvicorn.run(api,port=8000, host=deployment_host) #localhost use 127.0.0.1, 0.0.0.0 for container deployment
else:
	configure()
