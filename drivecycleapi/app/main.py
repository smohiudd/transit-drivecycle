import json
import os
from contextlib import asynccontextmanager
from typing import List, Optional

import geopandas as gpd
import numpy as np
import pandas as pd
import polyline
import requests
from drivecycle import energy, route, simplification
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from psycopg_pool import AsyncConnectionPool
from pydantic import BaseModel

valhalla_host = "http://valhalla:8002"


def strictly_increasing(L):
    return all(L[i] < L[i + 1] for i in range(len(L) - 1))


class Energy(BaseModel):
    traj: List
    elv: List
    mass: float
    area: float
    capacity: float
    aux: float


class Item(BaseModel):
    geom: List
    distances: List


app = FastAPI()


@app.get("/")
def read_root():
    return {"This is Transit Drivecycle V0.1"}


@app.post("/drivecycle/")
async def get_drivecycle(item: Item):
    stops = [i for i in item.distances if i != 0]

    coords = item.geom

    b = polyline.encode(coords, 6)

    data = json.dumps(
        {
            "encoded_polyline": b,
            "costing": "bus",
            "filters": {
                "attributes": [
                    "shape",
                    "edge.length",
                    "edge.speed",
                    "node.intersecting_edge.road_class",
                ],
                "action": "include",
            },
        }
    )

    height_data = json.dumps({"encoded_polyline": b, "range": True})

    trace = requests.post(f"{valhalla_host}/trace_attributes", data=data)
    height = requests.post(f"{valhalla_host}/height", data=height_data)

    coords_trace = polyline.decode(trace.json()["shape"], 6)

    if len(trace.json()["edges"]) < 1:
        print("no matched edges")
        raise HTTPException(status_code=500, detail="No matched edges")

    df = gpd.GeoDataFrame(trace.json()["edges"])
    df["end"] = df["end_node"].map(
        lambda x: x["intersecting_edges"][0]["road_class"]
        if "intersecting_edges" in x
        else None
    )
    df["lr"] = df["length"].cumsum() * 1000
    df["speed"] = df.apply(lambda x: x["speed"] * (1000 / 3600), axis=1)
    df = df[["speed", "end", "lr"]]

    df1 = pd.DataFrame({"speed": np.NaN, "end": "bus_stop", "lr": stops})

    df2 = (
        pd.concat([df, df1], axis=0)
        .reset_index()[["speed", "end", "lr"]]
        .sort_values("lr")
        .ffill()
        .fillna(0)
    )

    df_clustered = simplification.cluster_nodes(df2, 30)
    df_clustered = df_clustered[df_clustered["lr"] > 0]

    stop_params = {"bus_stop": 60, "tertiary": 120, "secondary": 60}
    trajectory = route.sequential(df_clustered, stop_params, step=2, a_max=2)

    drive_cycle = np.around(trajectory, 3)
    elevations = height.json()["range_height"]

    return {
        "data": drive_cycle.tolist(),
        "elv": elevations,
        "time": np.round(drive_cycle[-1, 0] / 60, 2),
        "distance": np.round(drive_cycle[-1, 2] / 1000, 2),
        "avg_speed": np.round(np.average(drive_cycle[:, 1]) * (3600 / 1000), 2),
        "trace": coords_trace,
    }


@app.post("/energy/")
async def get_energy(item: Energy):
    mass = item.mass
    capacity = item.capacity
    aux = item.aux
    area = item.area
    traj = item.traj
    elv = item.elv

    soc = energy.energy_model(
        traj,
        elv if len(elv) > 0 else None,
        m=mass,
        area=area,
        capacity=capacity,
        power_aux=aux,
    )

    return {
        "soc": soc.tolist(),
        "soc_final": np.round(soc[-1, 4] * -1, 2),
        "power": np.round(soc[-1, 3], 2),
    }
