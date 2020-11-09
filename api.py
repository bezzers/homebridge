import os
import requests
import uuid 
import asyncio
import datetime
from functools import partial
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
from sfmc import SFMC
from azure_storage import AZ_BLOB

# Get secrets and store as variables
response = requests.get("https://mgti-dal-so-vlt.mrshmc.com/v1/kv/data/oss2/owg-sfmc-connector", headers={"X-Vault-Token": os.environ['VAULT_TOKEN'], "X-Vault-Namespace": "OCIO-POC-Vault"})
if response.status_code != 200:
    raise Exception("Unable to fetch secrets - ", response.content)
secrets = response.json()['data']['data']

# set up the app and a list to store active runs
app = FastAPI()
active_runs = list()

# Define the model for requests
class Request(BaseModel):
    secret: str
    offset: Optional[int] = 0

@app.post("/run", status_code=202)
async def run(req: Request):
    if req.secret != secrets['api_secret']:
        raise HTTPException(status_code=401, detail='Invalid api secret')
    if req.offset < 0 or req.offset > 52:
        raise HTTPException(status_code=400, detail='The offset must be between 0 and 52')
    
    try:
        id = uuid.uuid4()
        sfmc = SFMC(secrets['sfmc_org_id'], secrets['sfmc_client_id'], secrets['sfmc_client_secret'])
        azb = AZ_BLOB(secrets['azure_connection_string'])
        future = asyncio.ensure_future(sfmc.run_week(id, azb, req.offset))
        active_runs.append({"id": id, "res": future, "time": datetime.datetime.now()})
        return {"id": id}

    except BaseException as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/check/{id}", status_code=200)
async def check(id):
    global active_runs
    active_runs = [r for r in active_runs if datetime.datetime.now() - r['time'] < datetime.timedelta(days=1) and not r['res'].done()]
    run = next((r for r in active_runs if str(r['id']) == id), {"res": "no data"})
    if not asyncio.isfuture(run['res']):
        raise HTTPException(status_code=404, detail='No data for that id')
    if not run['res'].done():
        return {"status": "processing"}
    if run['res'].exception():
        return {"status": "failed"}
    return {"status": "succeeded"}
