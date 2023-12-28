## Transit Drivecyle

Transit Drivecycle creates a visualization of bus velocity profiles, energy consumption and state of charge using the [Drivecycle](https://github.com/smohiudd/drivecycle) python library.

![alt text](./assets/transit-drivecycle.gif)

### Project Setup

**The GTFS data used in this project must have the `shape_dist_traveled` field to get linearly reference stop distances.**

#### Download OSM Data

Download OSM data from [geofabrik](https://download.geofabrik.de/) and save in `/valhalla/data`. This will be used to generate the routing graph in Valhalla.

#### Convert GTFS CSV to Parquet

Since we are using DuckDb-Wasm for the joining GTFS tables in the browser, we'll need to convert the GTFS csv files to Parquet. See [this notebook](./notebooks/geoparquet.ipynb) for more information on using Pandas to convert csv to Parquet. Parquet files must be stored in and S3 bucket an referenced in `frontend/src/parquet_files.js`

#### Optional GTFS Database using `gtfs-postgres`

If would like to setup a traditional PostGIS/PostGres database to instead of using DuckDb then you can use [gtfs-via-postgres](https://github.com/public-transport/gtfs-via-postgres) to ingest GTFS. This will require changes to the API in `drivecycleapi` to connect to the db (not currently implemented).

### Run Locally

#### Run Dev

```bash
docker compose -f docker-compose-dev.yml up frontend-dev
```

#### Run Production

```
docker compose up
```

### Deploy Using AWS Fargate

CDK is used to deploy to AWS Fargate. To install deploy python requirements, run:

```
pip install -r requirements.txt
```

And then the following to deploy to AWS:

```
cdk deploy
```