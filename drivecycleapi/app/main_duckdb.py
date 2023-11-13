import json
import os
from contextlib import asynccontextmanager
from typing import List, Optional

import numpy as np
import polyline
import requests
from drivecycle import energy, graph, route
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from psycopg_pool import AsyncConnectionPool
from pydantic import BaseModel

import duckdb

valhalla_host = "http://valhalla:8002"

parquet_files= [
  {
    "file": "trips",
    "url": "https://gtfs-parquet.s3.us-west-2.amazonaws.com/trips-calgary.parquet",
  },
  {
    "file": "shapes",
    "url": "https://gtfs-parquet.s3.us-west-2.amazonaws.com/shapes-calgary.parquet",
  },
  {
    "file": "routes",
    "url": "https://gtfs-parquet.s3.us-west-2.amazonaws.com/routes-calgary.parquet",
  },
  {
    "file": "stop_times",
    "url": "https://gtfs-parquet.s3.us-west-2.amazonaws.com/stop_times-calgary.parquet",
  },
  {
    "file": "stops",
    "url": "https://gtfs-parquet.s3.us-west-2.amazonaws.com/stops-calgary.parquet",
  },
]

conn = duckdb.connect()

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("connecting")

    for parquet in parquet_files:
        rel=conn.read_parquet(parquet ["url"])
        rel.create_view(parquet ["file"])

    yield
    conn.close()


app = FastAPI(lifespan=lifespan)

@app.get("/")
def read_root():
    return {"This is Transit Drivecycle V0.1"}


@app.get("/routes/")
async def get_routes():
    cur = conn.cursor()
    routes = cur.execute("""
        SELECT json_group_array(json_object('route_id',route_id,'route_short_name', route_short_name, 'route_long_name', route_long_name)) 
        FROM routes
    """
    ).fetchall()

    return json.loads(routes[0][0])

@app.get("/shapes/{route_id}")
async def get_shapes(route_id: str):
    shapes = conn.execute("""
        SELECT json_group_array(json_object('shape_id',B.shape_id,'trip_id', B.trip_id, 'trip_headsign', B.trip_headsign)) FROM
        (SELECT DISTINCT ON (shape_id) shape_id, trip_id, trip_headsign FROM trips WHERE route_id=$1) as B
        """, [route_id]
    ).fetchall()

    return json.loads(shapes[0][0])


@app.get("/route/geom/{trip_id}")
async def route_geom(trip_id: str):
    geom = conn.execute("""
        SELECT shape_pt_sequence, shape_pt_lat, shape_pt_lon FROM
        (SELECT * FROM trips WHERE trip_id=$1) as b
        JOIN shapes ON b.shape_id=shapes.shape_id
        ORDER BY shape_pt_sequence
        """, [trip_id]
    ).fetchall()

    return geom

