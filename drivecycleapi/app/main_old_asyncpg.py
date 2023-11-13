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
from app.queries import get_routes
from app.config import Settings
from app.db import close_db_connection, connect_to_db
from buildpg import render

valhalla_host = "http://valhalla:8002"


app = FastAPI()
app.state.settings=Settings()

@app.get("/info")
async def info():
    return {
        "app_name": settings.postgres_user
    }


@app.get("/routes/")
async def read_item(request: Request):
    async with request.app.state.get_connection(request, "r") as conn:
        
        q, p = render(
            """
            SELECT route_id, route_short_name::int,route_long_name FROM routes WHERE route_id LIKE '%20715%' order by route_short_name
            """ 
        )

        result = await conn.fetch(q, *p)
        return result

@app.get("/shapes/{route_id}")
async def read_item(request: Request, route_id: str):
    async with request.app.state.get_connection(request, "r") as conn:
        
        q, p = render(
            """
            SELECT DISTINCT ON (shape_id) shape_id, trip_id, trip_headsign FROM trips WHERE route_id=:route_id
            """,
            route_id=route_id,
        )

        result = await conn.fetch(q, *p)
        return result

@app.get("/route/geom/{trip_id}")
async def read_item(request: Request, trip_id: str):
    async with request.app.state.get_connection(request, "r") as conn:
        
        q, p = render(
            """
            SELECT ST_AsGeoJSON(shapes_aggregated.shape) FROM
            (SELECT * FROM trips WHERE trip_id=:trip_id) as B
            JOIN shapes_aggregated ON B.shape_id=shapes_aggregated.shape_id
            """,
            trip_id=trip_id,
        )

        result = await conn.fetch(q, *p)
        return json.loads(result[0]["st_asgeojson"])


@app.get("/stop/distances/{trip_id}")
async def read_item(request: Request, trip_id: str):
    async with request.app.state.get_connection(request, "r") as conn:
        
        q, p = render(
            """
            SELECT ARRAY_AGG(ST_LineLocatePoint(
                ST_SetSRID(shape_return.shape,4326), 
                stop_return.stop_loc::geometry) * 
                ST_Length(
                    ST_Transform(
                        ST_SetSRID(shape_return.shape,4326),
                        :srid::int
                    )
                )) 
                FROM
            (
            SELECT stop_times.trip_id, trips.shape_id, stops.stop_loc, stop_times.stop_sequence, stop_times.stop_id FROM stop_times
            JOIN stops ON stop_times.stop_id=stops.stop_id
            JOIN trips ON stop_times.trip_id=trips.trip_id
            WHERE stop_times.trip_id=:trip_id
            ORDER BY stop_times.stop_sequence
            ) AS stop_return
            JOIN (
            SELECT shapes_aggregated.shape, shapes_aggregated.shape_id
            FROM shapes_aggregated
            ) AS shape_return 
            ON stop_return.shape_id=shape_return.shape_id
            """,
            srid=int(os.getenv('SRID')), trip_id=trip_id
        )

        result = await conn.fetch(q, *p)
        return result[0]["array_agg"]



@app.on_event("startup")
async def startup_event():
    """Connect to database on startup."""
    await connect_to_db(app)


@app.on_event("shutdown")
async def shutdown_event():
    """Close database connection."""
    await close_db_connection(app)