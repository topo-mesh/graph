from typing import Union
from fastapi import FastAPI
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

load_dotenv()

# URLs
URL_CURRENT = os.environ["URL_CURRENT"]

# SUPABASE
url: str = os.environ["SUPABASE_URL"]
key: str = os.environ["SUPABASE_KEY"]
supabase: Client = create_client(url, key)
supabase_response = (supabase.table("servers").select("*").execute())
sb_servers = supabase_response.model_dump()



response_ipinfo =  urlopen("https://ipinfo.io/json")

app = FastAPI()


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


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)
    
