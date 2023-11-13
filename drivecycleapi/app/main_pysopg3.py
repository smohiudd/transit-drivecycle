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

valhalla_host = "http://valhalla:8002"

def strictly_increasing(L):
    return all(L[i] < L[i+1] for i in range(len(L)-1))

def fix_distances(distances):
    stop_distances = np.copy(distances)
    stop_distances[0]=0
    end = stop_distances[-1]
    for i in range(1,len(distances)-1):
        if (stop_distances[i-1]>stop_distances[i]):
            if(i<len(distances)/2):
                stop_distances[i-1]=end-stop_distances[i-1]
            else:
                stop_distances[i]=end-stop_distances[i]
    return stop_distances.tolist()

class Item(BaseModel):
    geom: dict

class Energy(BaseModel):
    traj: List[List[float]]
    mass: float
    area: float
    capacity: float
    aux: float
    elv: Optional[List[List[float]]] = None

def get_conn_str():
    return f"""
    dbname={os.getenv('POSTGRES_DB')}
    user={os.getenv('POSTGRES_USER')}
    password={os.getenv('POSTGRES_PASSWORD')}
    host={os.getenv('POSTGRES_HOST')}
    port={os.getenv('POSTGRES_PORT')}
    """

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.async_pool = AsyncConnectionPool(conninfo=get_conn_str())
    yield
    await app.async_pool.close()


app = FastAPI(lifespan=lifespan)

@app.get("/")
def read_root():
    return {"This is Transit Drivecycle V0.1"}

# @app.middleware("http")
# async def add_process_time_header(request: Request, call_next):
#     response = await call_next(request)
#     response.headers["Access-Control-Allow-Private-Network"] = "true"
#     return response

@app.get("/routes/")
async def get_routes(request: Request):
    async with request.app.async_pool.connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute("""
                SELECT jsonb_agg(jsonb_build_object('route_id',B.route_id,'route_short_name', B.route_short_name, 'route_long_name', B.route_long_name)) FROM
                (SELECT route_id, route_short_name::int,route_long_name FROM routes WHERE route_id LIKE '%20715%' order by route_short_name) as B
                """ 
            )
            results = await cur.fetchall()
            return results[0][0]

@app.get("/shapes/{route_id}")
async def get_shapes(request: Request, route_id: str):
    async with request.app.async_pool.connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute("""
                SELECT jsonb_agg(jsonb_build_object('shape_id',B.shape_id,'trip_id', B.trip_id, 'trip_headsign', B.trip_headsign)) FROM
                (SELECT DISTINCT ON (shape_id) shape_id, trip_id, trip_headsign FROM trips WHERE route_id=%s) as B
                """, (route_id,)
            )
            results = await cur.fetchall()
            return results[0][0]

@app.get("/route/geom/{trip_id}")
async def route_geom(request: Request, trip_id: str):
    async with request.app.async_pool.connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute("""
                SELECT ST_AsGeoJSON(shapes_aggregated.shape) FROM
                (SELECT * FROM trips WHERE trip_id=%s) as B
                JOIN shapes_aggregated ON B.shape_id=shapes_aggregated.shape_id
                """, (trip_id,)
            )
            results = await cur.fetchall()
            return json.loads(results[0][0])

@app.get("/stops/{trip_id}")
async def get_stops(request: Request, trip_id: str):
    async with request.app.async_pool.connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                SELECT json_build_object(
                    'type', 'FeatureCollection',
                    'features', json_agg(ST_AsGeoJSON(t.*)::json)) FROM
                (SELECT stops.stop_loc, b.stop_sequence
                FROM (SELECT stop_times.stop_id, stop_times.stop_sequence FROM stop_times
                WHERE stop_times.trip_id=%s
                ORDER BY stop_times.stop_sequence) as b
                JOIN stops ON b.stop_id=stops.stop_id) as t
                """,
                (trip_id,))

            results = await cur.fetchall()
            return results[0][0]

@app.get("/stop/distances/{trip_id}")
async def stop_distances(request: Request, trip_id: str):
    async with request.app.async_pool.connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                SELECT ST_Length(
                        ST_Transform(
                            ST_SetSRID(shape_return.shape,4326),
                            %s::int
                        )
                    ) as length,
                ST_LineLocatePoint(
                    ST_SetSRID(shape_return.shape,4326), 
                    stop_return.stop_loc::geometry) * 
                    ST_Length(
                        ST_Transform(
                            ST_SetSRID(shape_return.shape,4326),
                            %s::int
                        )
                    ) as stops
                    FROM
                (
                SELECT stop_times.trip_id, trips.shape_id, stops.stop_loc, stop_times.stop_sequence, stop_times.stop_id FROM stop_times
                JOIN stops ON stop_times.stop_id=stops.stop_id
                JOIN trips ON stop_times.trip_id=trips.trip_id
                WHERE stop_times.trip_id=%s
                ORDER BY stop_times.stop_sequence
                ) AS stop_return
                JOIN (
                SELECT shapes_aggregated.shape, shapes_aggregated.shape_id
                FROM shapes_aggregated
                ) AS shape_return 
                ON stop_return.shape_id=shape_return.shape_id
                """,
                (os.getenv('SRID'),os.getenv('SRID'),trip_id))

            results = await cur.fetchall()
            # distances = results[0][0]
            # distances.reverse()
           
            # return fix_distances(distances)

            return results


@app.get("/drivecycle/{trip_id}")
async def get_energy(request: Request, trip_id: str):
    async with request.app.async_pool.connection() as conn:
        async with conn.cursor() as cur:
            
            await cur.execute(
                """
                SELECT ARRAY_AGG(ST_LineLocatePoint(
                    ST_SetSRID(shape_return.shape,4326), 
                    stop_return.stop_loc::geometry) * 
                    ST_Length(
                        ST_Transform(
                            ST_SetSRID(shape_return.shape,4326),
                            %s::int
                        )
                    )) 
                    FROM
                (
                SELECT stop_times.trip_id, trips.shape_id, stops.stop_loc, stop_times.stop_sequence, stop_times.stop_id FROM stop_times
                JOIN stops ON stop_times.stop_id=stops.stop_id
                JOIN trips ON stop_times.trip_id=trips.trip_id
                WHERE stop_times.trip_id=%s
                ORDER BY stop_times.stop_sequence
                ) AS stop_return
                JOIN (
                SELECT shapes_aggregated.shape, shapes_aggregated.shape_id
                FROM shapes_aggregated
                ) AS shape_return 
                ON stop_return.shape_id=shape_return.shape_id
                """,
                (os.getenv('SRID'),trip_id)
            )
            
            stop_results = await cur.fetchall()
            stops_ = stop_results[0][0]
            stops_.reverse()
            stops=fix_distances(stops_)

            if not strictly_increasing(stops):
                raise HTTPException(status_code=500, detail="stop distances not strictly increasing")
            
            await cur.execute("""
                SELECT ST_AsGeoJSON(shapes_aggregated.shape) FROM
                (SELECT * FROM trips WHERE trip_id=%s) as B
                JOIN shapes_aggregated ON B.shape_id=shapes_aggregated.shape_id
                """, (trip_id,)
            )
            results = await cur.fetchall()
            geom = json.loads(results[0][0])

            coords = [
                tuple((i[1], i[0])) for i in geom["coordinates"]
            ]

            b = polyline.encode(coords, 6)

            data = json.dumps(
                {
                    "encoded_polyline": b,
                    "costing": "bus",
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

            edges = trace.json()["edges"]

            if len(edges) < 1:
                raise HTTPException(status_code=500, detail="No matched edges returned")


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
            a.include_stops(stops[1:])
            a.consolidate_intersections()
            a.simplify_graph()

            stop = {"bus_stop":60,"tertiary":120, "secondary":60}
            trajectory = route.sequential(a.get_edges(), stops=stop, stop_at_node=True, step=1)

            drive_cycle = np.around(trajectory, 3)

            elevations = height.json()["range_height"]

            return {
                "data": trajectory.tolist(),
                "elv": elevations,
                "dist": np.round(drive_cycle[-1, 2] / 1000, 2),
                "time": np.round(drive_cycle[-1, 0] / 60, 2),
                "avg_speed": np.round(np.average(drive_cycle[:, 1]) * (3600 / 1000), 2),
            }

# @app.post("/energy/")
# async def get_energy(item: Energy):
#     result = {**item.dict()}

#     soc = energy.energy_model(
#         result["traj"],
#         result["elv"],
#         m=result["mass"],
#         area=result["area"],
#         capacity=result["capacity"],
#         power_aux=result["aux"],
#     )

#     return {
#         "soc": soc.tolist(),
#         "soc_final": np.round(np.round(1 - soc[-1, 4], 3) * 100, 4),
#         "power": np.round(soc[-1, 3], 2),
#     }


# @app.post("/drivecycle_post/")
# async def get_drivecycle(item: Item):
#     stops = item.geom["features"][0]["properties"]["stop_distances"]
#     stops = [i for i in stops if i != 0]

#     coords = [
#         tuple((i[1], i[0])) for i in item.geom["features"][0]["geometry"]["coordinates"]
#     ]

#     b = polyline.encode(coords, 6)

#     data = json.dumps(
#         {
#             "encoded_polyline": b,
#             "costing": "auto",
#             "filters": {
#                 "attributes": [
#                     "edge.way_id",
#                     "edge.names",
#                     "edge.length",
#                     "edge.speed",
#                     "node.intersecting_edge.road_class",
#                     "node.intersecting_edge.begin_heading",
#                     "node.elapsed_time",
#                     "node.type",
#                 ],
#                 "action": "include",
#             },
#         }
#     )

#     height_data = json.dumps({"encoded_polyline": b, "range": True})

#     trace = requests.post(f"{valhalla_host}/trace_attributes", data=data)
#     height = requests.post(f"{valhalla_host}/height", data=height_data)

#     edges = trace.json()["edges"]

#     if len(edges) < 10:
#         raise HTTPException(status_code=500, detail="Server encountered an error.")

#     data_ = []

#     for edge in edges:
#         length = edge["length"] * 1000
#         speed = edge["speed"]
#         way_id = edge["way_id"]
#         try:
#             intersect = [edge["end_node"]["intersecting_edges"][0]["road_class"]]
#         except:
#             intersect = [None]

#         item = {
#             "way_id": way_id,
#             "length": length,
#             "speed": speed,
#             "intersection": intersect,
#         }
#         data_.append(item)

#     a = graph.Graph(data_)
#     a.include_stops(stops)
#     a.consolidate_intersections()
#     a.simplify_graph()

#     stop = {"bus_stop": 30, "tertiary": 10}
#     trajectory = route.sequential(a.get_edges(), stops=stop, stop_at_node=True, step=1)

#     drive_cycle = np.around(trajectory, 3)

#     elevations = height.json()["range_height"]

#     return {
#         "data": trajectory.tolist(),
#         "elv": elevations,
#         "dist": np.round(drive_cycle[-1, 2] / 1000, 2),
#         "time": np.round(drive_cycle[-1, 0] / 60, 2),
#         "avg_speed": np.round(np.average(drive_cycle[:, 1]) * (3600 / 1000), 2),
#     }


