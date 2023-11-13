from fastapi import Request

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

async def get_route_geom(request: Request, trip_id: str):
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

async def get_stop_geom(request: Request, trip_id: str):
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

async def stop_distances(request: Request, trip_id: str):
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
                (os.getenv('SRID'),trip_id))

            results = await cur.fetchall()
            return results[0][0]