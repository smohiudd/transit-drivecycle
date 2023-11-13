"""Database connection handling."""

import json
from contextlib import asynccontextmanager, contextmanager
from typing import AsyncIterator, Callable, Dict, Generator, Literal, Union

import attr
import orjson
from asyncpg import Connection, exceptions
from buildpg import V, asyncpg, render
from fastapi import FastAPI, Request

async def con_init(conn):
    """Use orjson for json returns."""
    await conn.set_type_codec(
        "json",
        encoder=orjson.dumps,
        decoder=orjson.loads,
        schema="pg_catalog",
    )
    await conn.set_type_codec(
        "jsonb",
        encoder=orjson.dumps,
        decoder=orjson.loads,
        schema="pg_catalog",
    )

ConnectionGetter = Callable[[Request, Literal["r", "w"]], AsyncIterator[Connection]]


async def connect_to_db(app: FastAPI, get_conn: ConnectionGetter = None) -> None:
    """Create connection pools & connection retriever on application."""
    settings = app.state.settings

    readpool = settings.reader_connection_string
    writepool = settings.writer_connection_string
    db = DB()
    app.state.readpool = await db.create_pool(readpool, settings)
    app.state.writepool = await db.create_pool(writepool, settings)
    app.state.get_connection = get_conn if get_conn else get_connection


async def close_db_connection(app: FastAPI) -> None:
    """Close connection."""
    await app.state.readpool.close()
    await app.state.writepool.close()


@asynccontextmanager
async def get_connection(
    request: Request,
    readwrite: Literal["r", "w"] = "r",
) -> AsyncIterator[Connection]:
    """Retrieve connection from database conection pool."""
    pool = (
        request.app.state.writepool if readwrite == "w" else request.app.state.readpool
    )
    async with pool.acquire() as conn:
        yield conn


async def dbfunc(conn: Connection, func: str, arg: Union[str, Dict]):
    """Wrap PLPGSQL Functions.

    Keyword arguments:
    pool -- the asyncpg pool to use to connect to the database
    func -- the name of the PostgreSQL function to call
    arg -- the argument to the PostgreSQL function as either a string
    or a dict that will be converted into jsonb
    """
    with translate_pgstac_errors():
        if isinstance(arg, str):
            q, p = render(
                """
                SELECT * FROM :func(:item::text);
                """,
                func=V(func),
                item=arg,
            )
            return await conn.fetchval(q, *p)
        else:
            q, p = render(
                """
                SELECT * FROM :func(:item::text::jsonb);
                """,
                func=V(func),
                item=json.dumps(arg),
            )
            return await conn.fetchval(q, *p)


@attr.s
class DB:
    """DB class that can be used with context manager."""

    connection_string = attr.ib(default=None)
    _pool = attr.ib(default=None)
    _connection = attr.ib(default=None)

    async def create_pool(self, connection_string: str, settings):
        """Create a connection pool."""
        pool = await asyncpg.create_pool(
            connection_string,
            min_size=settings.db_min_conn_size,
            max_size=settings.db_max_conn_size,
            max_queries=settings.db_max_queries,
            max_inactive_connection_lifetime=settings.db_max_inactive_conn_lifetime,
            init=con_init
        )
        return pool