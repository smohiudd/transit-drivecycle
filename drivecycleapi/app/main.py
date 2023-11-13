import json
import os
from typing import List, Optional

import numpy as np
import polyline
import requests
from drivecycle import energy, graph, route
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

valhalla_host = "http://valhalla:8002"

def strictly_increasing(L):
    return all(L[i] < L[i+1] for i in range(len(L)-1))

class Item(BaseModel):
    geom: List
    distances: List
    mass: float
    area: float
    capacity: float
    aux: float

app = FastAPI()

@app.get("/")
def read_root():
    return {"This is Transit Drivecycle V0.1"}


@app.post("/drivecycle_post/")
async def get_drivecycle(item: Item):
    
    stops = [i for i in item.distances if i != 0]

    coords = item.geom
    mass=item.mass
    capacity=item.capacity
    aux=item.aux
    area=item.area

    b = polyline.encode(coords, 6)

    trace_route = json.dumps({
        "encoded_polyline":b,
        "costing":"bus"
    })

    data = json.dumps(
        {
            "encoded_polyline": b,
            "costing": "bus",
            "trace_options":{
                "search_radius":50,
                "gps_accuracy":1.0,
                "breakage_distance":10,
                "interpolation_distance":50
            },
            "shape_match": "map_snap",
            "filters": {
                "attributes": [
                    "edge.way_id",
                    "edge.names",
                    "edge.length",
                    "edge.speed",
                    "node.intersecting_edge.road_class",
                    "node.intersecting_edge.begin_heading",
                    "node.elapsed_time",
                    "node.type",
                ],
                "action": "include",
            },
        }
    )

    height_data = json.dumps({"encoded_polyline": b, "range": True})

    trace = requests.post(f"{valhalla_host}/trace_attributes", data=data)
    height = requests.post(f"{valhalla_host}/height", data=height_data)
    trace_ = requests.post(f"{valhalla_host}/trace_route", data=trace_route)

    coords_trace = []
    try:
        for i in trace_.json()["trip"]["legs"]:
            coords_trace.append(polyline.decode(i["shape"],6))
    except: 
        coords_trace=[[]]

    edges = trace.json()["edges"]

    if len(edges) < 1:
        print("no matched edges")
        raise HTTPException(status_code=500, detail="No matched edges")
        
    data_ = []

    for edge in edges:
        length = edge["length"] * 1000
        speed = edge["speed"]
        way_id = edge["way_id"]
        try:
            intersect = [edge["end_node"]["intersecting_edges"][0]["road_class"]]
        except:
            intersect = [None]

        item = {
            "way_id": way_id,
            "length": length,
            "speed": speed,
            "intersection": intersect,
        }
        data_.append(item)

    a = graph.Graph(data_)
    a.include_stops(stops)
    a.consolidate_intersections()
    a.simplify_graph()

    stop = {"bus_stop":60,"tertiary":120, "secondary":60}
    trajectory = route.sequential(a.get_edges(), stops=stop, stop_at_node=True, step=1)

    drive_cycle = np.around(trajectory, 3)
    elevations = height.json()["range_height"]

    soc = energy.energy_model(
        trajectory,
        elevations,
        m=mass,
        area=area,
        capacity=capacity,
        power_aux=aux,
    )

    return {
        "data": drive_cycle.tolist(),
        "elv": elevations,
        "time": np.round(drive_cycle[-1, 0] / 60, 2),
        "distance":np.round(drive_cycle[-1, 2],2)/1000,
        "avg_speed": np.round(np.average(drive_cycle[:, 1]) * (3600 / 1000), 2),
        "soc": soc.tolist(),
        "soc_final": np.round(np.round(1 - soc[-1, 4], 3) * 100, 4),
        "power": np.round(soc[-1, 3], 2),
        "trace": coords_trace[0]
    }


