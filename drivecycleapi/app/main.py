from typing import Optional
from drivecycle import route, graph
import numpy as np 
import polyline
import json
import requests
from . import config

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from pydantic import BaseModel


class Item(BaseModel):
    geom: dict
    
valhalla_host = "http://valhalla:8002"

origins = [
    "http://localhost:3000",
]

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"This is Transit Drivecycle V0.1"}

@app.post("/drivecycle_post/")
async def get_drivecycle(item: Item):

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
        return {
            "statusCode": 500,
            "headers": headers,
            "body": json.dumps({
                    "Message" : "Server encountered an error."
                })
        }

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

    return {"data": drive_cycle.tolist(),"elv": elevations}

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
        return {
            "statusCode": 500,
            "headers": headers,
            "body": json.dumps({
                    "Message" : "Server encountered an error."
                })
        }

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
