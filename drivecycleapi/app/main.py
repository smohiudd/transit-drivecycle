from typing import Optional,List 
from drivecycle import route, graph, energy
import numpy as np 
import polyline
import json
import requests
from . import config

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

from pydantic import BaseModel


class Item(BaseModel):
    geom: dict
    mass: float
    area: float
    capacity: float

class Energy(BaseModel):
    traj: List[List[float]]
    mass: float
    area: float
    capacity: float
    
valhalla_host = "http://valhalla:8002"
# valhalla_host = "http://localhost:8002"

# class MyHeadersMiddleware(BaseHTTPMiddleware):
#     async def dispatch(self, request, call_next):
#         response = await call_next(request)
#         response.headers["Access-Control-Allow-Private-Network"] = "true"
#         return response


origins = [
    "http://localhost:3000",
    "http://localhost",
    "https://localhost",
    "http://drivecycle.eastus.azurecontainer.io/"
]

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# app.add_middleware(MyHeadersMiddleware)



@app.get("/")
def read_root():
    return {"This is Transit Drivecycle V0.1"}


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    response = await call_next(request)
    response.headers["Access-Control-Allow-Private-Network"] = "true"
    return response

@app.post("/energy/")
async def get_energy(item: Energy):
    result = {**item.dict()}

    # print(result["traj"])

    soc = energy.energy_model(result["traj"], m=result["mass"], area=result["area"], capacity=result["capacity"])

    return {
        "soc": soc.tolist(),
        "soc_final": np.round(np.round(1-soc[-1,4],3)*100,4)
    }

@app.post("/drivecycle_post/")
async def get_drivecycle(item: Item):

    result = {**item.dict()}

    stops = item.geom["features"][0]["properties"]["stop_distances"]
    stops = [i for i in stops if i!=0]

    coords = [tuple((i[1],i[0])) for i in item.geom["features"][0]["geometry"]["coordinates"]]

    b = polyline.encode(coords, 6)

    data =json.dumps({
        "encoded_polyline":b,
        "costing":"auto",
        "filters":
            {
                "attributes":[
                    "edge.way_id",
                    "edge.names",
                    "edge.length",
                    "edge.speed",
                    "node.intersecting_edge.road_class",
                    "node.intersecting_edge.begin_heading",
                    "node.elapsed_time","node.type"
                    ],
                "action":"include"
            }
        })

    height_data = json.dumps({"encoded_polyline":b,"range":True})

    trace = requests.post(f"{valhalla_host}/trace_attributes", data=data)
    height = requests.post(f"{valhalla_host}/height", data=height_data)

    edges = trace.json()["edges"]

    if len(edges)<10:
        raise HTTPException(status_code=500, detail="Server encountered an error.")

    data_ = []

    for edge in edges:
        length = edge["length"]*1000
        speed = edge["speed"]
        way_id = edge["way_id"]
        try:
            intersect = [edge["end_node"]["intersecting_edges"][0]["road_class"]]
        except:
            intersect = [None]

        item = {
            "way_id":way_id,
            "length":length,
            "speed":speed,
            "intersection":intersect,
        }
        data_.append(item)

        
    a = graph.Graph(data_)
    a.include_stops(stops)
    a.consolidate_intersections()
    a.simplify_graph()

    stop={"bus_stop":30,"tertiary":10}
    trajectory = route.sequential(a.get_edges(),stops=stop, stop_at_node=True, step=1)

    drive_cycle  = np.around(trajectory,3)

    elevations =  height.json()["range_height"]

    soc = energy.energy_model(trajectory, m=result["mass"], area=result["area"], capacity=result["capacity"])

    final = np.c_[drive_cycle, soc[:,4]]

    return {
        "data": trajectory.tolist(),
        "elv": elevations,
        "dist": np.round(final[-1,2]/1000,2),
        "time": np.round(final[-1,0]/60,2),
        "avg_speed": np.round(np.average(final[:,1])*(3600/1000),2),
        "soc": np.round(np.round(1-soc[-1,4],3)*100,4)
        }

@app.get("/drivecycle/")
def read_item(onestop_id: str=None):

    url = f"http://transit.land/api/v1/route_stop_patterns.geojson?onestop_id={onestop_id}"

    r = requests.get(url,headers={'apikey':config.api_key},timeout=(3.05, 10)).json()

    stops = r["features"][0]["properties"]["stop_distances"]
    stops = [i for i in stops if i!=0]

    coords = [tuple((i[1],i[0])) for i in r["features"][0]["geometry"]["coordinates"]]

    b = polyline.encode(coords, 6)

    data =json.dumps({
        "encoded_polyline":b,
        "costing":"auto",
        "filters":
            {
                "attributes":[
                    "edge.way_id",
                    "edge.names",
                    "edge.length",
                    "edge.speed",
                    "node.intersecting_edge.road_class",
                    "node.intersecting_edge.begin_heading",
                    "node.elapsed_time","node.type"
                    ],
                "action":"include"
            }
        })

    height_data = json.dumps({"encoded_polyline":b,"range":True})

    trace = requests.post(f"{valhalla_host}/trace_attributes", data=data)
    height = requests.post(f"{valhalla_host}/height", data=height_data)

    edges = trace.json()["edges"]

    if len(edges)<10:
        raise HTTPException(status_code=500, detail="Server encountered an error.")

    data_ = []

    for edge in edges:
        length = edge["length"]*1000
        speed = edge["speed"]
        way_id = edge["way_id"]
        try:
            intersect = [edge["end_node"]["intersecting_edges"][0]["road_class"]]
        except:
            intersect = [None]

        item = {
            "way_id":way_id,
            "length":length,
            "speed":speed,
            "intersection":intersect,
        }
        data_.append(item)

        
    a = graph.Graph(data_)
    a.include_stops(stops)
    a.consolidate_intersections()
    a.simplify_graph()

    stop={"bus_stop":30,"tertiary":10}
    trajectory = route.sequential(a.get_edges(),stops=stop, stop_at_node=True, step=1)
    #trajectory = Drivecycle().drivecycle(simple_edges,stops=stop, stop_at_node=True, step=0.1).get_trajectory()
    drive_cycle  = np.around(trajectory,3)

    elevations =  height.json()["range_height"]

    return {"data": drive_cycle.tolist(),"elv": elevations}


@app.get("/routes/")
def read_item(operated_by: str=None):

    url = f"http://transit.land/api/v1/routes?per_page=1000&operated_by={operated_by}&include_geometry=false&vehicle_type=bus"

    response = requests.get(url,headers={'apikey':config.api_key},timeout=(10, 15))

    if response.ok:
        return response.json()
    else:
        raise HTTPException(status_code=500, detail="No response. Server encountered an error.")


@app.get("/route/")
def read_item(onestop_id: str=None):

    url = f"http://transit.land/api/v1/route_stop_patterns.geojson?onestop_id={onestop_id}"

    response = requests.get(url,headers={'apikey':config.api_key},timeout=(10, 15))

    if response.ok:
        return response.json()
    else:
        raise HTTPException(status_code=500, detail="No response. Server encountered an error.")
