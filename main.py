from typing import Union
from fastapi import FastAPI
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from pydantic import BaseModel
import os
import json
from datetime import datetime
from urllib.request import urlopen
import requests
import psutil
from supabase import create_client, Client
import uvicorn
import asyncio


load_dotenv()


# CONSTANTS - DO NOT CHANGE
SERVICE_NAME: str = os.environ["SERVICE_NAME"]
SUPABASE_URL: str = os.environ["SUPABASE_URL"]
SUPABASE_KEY: str = os.environ["SUPABASE_KEY"]

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
response_ipinfo =  urlopen("https://ipinfo.io/json")


@asynccontextmanager
async def lifespan(app: FastAPI):
    enviroment = {}
    try:
        enviroment = supabase.table("servers").select("*").eq("name", SERVICE_NAME).execute().model_dump()
        app.state.config = enviroment["data"]
    except Exception as e:
        raise SystemError(f"ERROR: Failed to load configuration for {SERVICE_NAME}. Details: {e}")

    async def scheduled_ping_loop():
        while True:
            await execute_ping() 
            await asyncio.sleep(60) 
    asyncio.create_task(scheduled_ping_loop())
    yield
    del app.state.config


app = FastAPI(lifespan=lifespan)


@app.get("/")
def read_root():
    return {"hello":"world!"}


@app.get("/health")
def read_health():
    return {
        "now": datetime.now(),
        "data": json.load(response_ipinfo)
    }


@app.get("/ping")
def read_ping():
    data = {}
    # This is UNSAFE + DANGEROUS + VULNERABLE
    sb_servers = (supabase.table("servers").select("*").execute()).model_dump()
    for server in sb_servers["data"]:
        try:
            response = requests.get(server["url"], timeout=5)
            data[server["name"]] = {
                "is_active": True,
                "status_code": response.status_code,
                "response_time": response.elapsed.total_seconds(),
            }
        except requests.exceptions.RequestException as e:
            data[server["name"]] = {
                "is_active": False,
                "error": str(e)
            }
    return data
        

@app.get("/me")
def read_me():
    me = {
        "cpu": {
            "cpu_times": psutil.cpu_times(),
            "cpu_times_percent": psutil.cpu_times_percent(),
            "cpu_percent": psutil.cpu_percent(),
            "cpu_stats": psutil.cpu_stats(),
            "cpu_freq": psutil.cpu_freq(),
            "cpu_count": psutil.cpu_count(),
            "getloadavg": psutil.getloadavg()
        },
        "memory": {
            "virtual_memory": psutil.virtual_memory(),
            "swap_memory": psutil.swap_memory()
        },
        "disk": {
            "disk_partitions": psutil.disk_partitions(),
            "disk_usage": psutil.disk_usage("/"),
            "disk_io_counters": psutil.disk_io_counters()
        },
        "network": {
            "net_io_counters": psutil.net_io_counters(),
            "net_connections": psutil.net_connections(),
            "net_if_addrs": psutil.net_if_addrs(),
            "net_if_stats": psutil.net_if_stats()
        },
        "sensors": {
            "sensors_temperatures": psutil.sensors_temperatures(),
            "sensors_fans": psutil.sensors_fans(),
            "sensors_battery": psutil.sensors_battery()
        },
        "other": {
            "boot_time": psutil.boot_time(),
            "users": psutil.users(),
        }
    }
    return me


@app.get("/is_active")
async def execute_ping():
    data = (supabase.table("servers").update({
        "is_active": True,
        "last_ping_at": "now()" 
        }).eq("name", SERVICE_NAME).execute()).model_dump()
    return data["data"]


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)
