from typing import Optional
from drivecycle.trajectory import Trajectory
from drivecycle.drivecycle import Drivecycle
from drivecycle import utils
import numpy as np 
import polyline
import json
import requests

from fastapi import FastAPI

valhalla_host = "http://valhalla:8002"

app = FastAPI()

@app.get("/")
def read_root():
    return {"This is Transit Drivecycle V0.1"}

@app.get("/drivecycle/")
def read_item(onestop_id: str=None):

    url = f"http://transit.land/api/v1/route_stop_patterns.geojson?onestop_id={onestop_id}"

    r = requests.get(url,headers={'apikey':'SN0N9PZyDIDrOf9tcm3DS1t8sbqZi1Ul'},timeout=(3.05, 10)).json()

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

        
    a = utils.Graph(data_)
    c = a.get_source_target()
    b = utils.include_stops(a.simplify_graph(),stops) 

    simple_edges = utils.get_edges(b,c)

    stop={"bus_stop":30,"tertiary":10}
    trajectory = Drivecycle().drivecycle(simple_edges,stops=stop, stop_at_node=True, step=0.1).get_trajectory()
    drive_cycle  = np.around(trajectory,3)

    elevations =  height.json()["range_height"]

    return {
        "statusCode": 200,
        "body": json.dumps({"data":drive_cycle.tolist(),"elv":elevations})
    }
