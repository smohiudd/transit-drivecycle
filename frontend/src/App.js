import Map from "./map.js";
import Sidebar from "./sidebar.js";
import React, { useEffect, useState } from "react";
import './css/App.css';
import urls from './parquet_files.js';

import { DuckDBClient, makeDB } from "./dbclient.js";

let Db = makeDB();
let db = new DuckDBClient(Db);

urls.map((file) => {
  db.insertParquet(file);
});

function App() {

  const [tripId, setTripId] = useState(null);
  const [routeId, setRouteId] = useState('7-20715');
  const [listRoute, setListRoute] = useState([]);
  const [listTrip, setListTrip] = useState([]);
  const [drivecycle, setDrivecycle] = useState([]);
  const [geom, setGeom] = useState([]);
  const [trace, setTrace] = useState([]);
  const [elevation, setElevation] = useState([]);
  const [soc, setSoc] = useState([]);
  const [soc_final, setSocFinal] = useState(null);
  const [power_final, setPowerFinal] = useState(null);
  const [power_eff, setPowerEff] = useState(null);
  const [drivecycle_error, setDrivecycleError] = useState(false);
  const [line_visbility, setLineVisiblity] = useState("visible");
  const [toggle, setToggle] = useState(null);
  const [distance, setDistance] = useState(null);
  const [time, setTime] = useState(null);
  const [avg_speed, setAvgSpeed] = useState(null);
  const [battery_cap, setBatteryCap] = useState(550.0);
  const [aux, setAux] = useState(5.0);
  const [mass, setMass] = useState(10000.0);
  const [area, setArea] = useState(8.0);
  const [elv, setElv] = useState(true);
  const [isDrawer, setDrawer] = useState("false");

  //Get all routes
  useEffect(() => {
    db.queryStream(
      `SELECT * FROM 'routes.parquet' ORDER BY route_short_name`,
      null,
    ).then((result) => {
      let rows = result.readRows();
      rows.next().then((res) => {
        setListRoute(res.value);
        return rows.next();
      });
    });
  }, []);

  //Get all shape ids
  useEffect(() => {
    db.queryStream(
      `
      SELECT DISTINCT ON (shape_id) shape_id, trip_id, trip_headsign 
      FROM 'trips.parquet' WHERE route_id='${routeId}'
      `,
      null,
    ).then((result) => {
      let rows = result.readRows();
      rows.next().then((res) => {
        setListTrip(res.value);
        setTripId(res.value[0].trip_id);
        return rows.next();
      });
    });
  }, [routeId]);

  //get shape coords and distanced travelled, post to drivecycle api
  useEffect(() => {

    db.queryStream(
      `
      SELECT shape_pt_sequence, shape_pt_lat, shape_pt_lon FROM
      (SELECT * FROM trips.parquet
      WHERE trip_id=${tripId}) as b
      JOIN shapes.parquet ON b.shape_id=shapes.shape_id
      ORDER BY shape_pt_sequence
      `,
      null,
    ).then((result) => {
      let rows = result.readRows();
      rows.next().then((res) => {
        let coords = res.value
        setGeom(coords);

        db.queryStream(
          `
          SELECT b.shape_dist_traveled
          FROM (SELECT stop_times.stop_id, stop_times.stop_sequence, stop_times.shape_dist_traveled FROM stop_times.parquet
          WHERE trip_id=${tripId}
          ORDER BY stop_times.stop_sequence) as b
          JOIN stops.parquet ON b.stop_id=stops.stop_id
          `,
          null,
        ).then((result) => {
          let rows = result.readRows();
          rows.next().then((res) => {
            let distances = res.value
            let distances_ = distances.map(item=>item.shape_dist_traveled*1000)
            let coords_geom = coords.map(item=>[item.shape_pt_lat,item.shape_pt_lon])
    
            fetch(`/drivecycle/`, {
              method: 'POST',
              headers: {
                  'Accept': 'application/json',
                  'Content-Type': 'application/json',
              },
              body: JSON.stringify({
                  geom: coords_geom,
                  distances: distances_,
              })
            }).then(res => {
                  if (res.ok)return res.json() ;
                  throw new Error('Something went wrong.');
              })
              .then(data => {
                setDrivecycle(data.data)
                setTrace(data.trace)
                setElevation(data.elv)
                setAvgSpeed(data.avg_speed)
                setTime(data.time)
                setDistance(data.distance)
                setDrivecycleError(false)
                setLineVisiblity("visible")
                setPowerFinal(null)
                setPowerEff(null)
              })
              .catch(()=>{
                console.log("api error")
                if (tripId != null) setDrivecycleError(true)
                setDrivecycle([])
                setElevation([])
                setSoc([])
                setLineVisiblity("none")
                setSocFinal(null)
                setPowerFinal(null)
                setPowerEff(null)
                setDistance(null)
                setTime(null)
                setAvgSpeed(null)
              })


          });
        });

      });
    });
    console.log(tripId)

  }, [tripId]);
    

  useEffect(() => {

    fetch(`/energy/`, {
      method: 'POST',
      headers: {
          'Accept': 'application/json',
          'Content-Type': 'application/json',
      },
      body: JSON.stringify({
          traj: drivecycle,
          elv: elv ? elevation : [],
          mass: mass,
          area: area,
          capacity: battery_cap,
          aux: aux
        })
      })
      .then(res => res.json())
      .then(data => {
          setSoc(data.soc)
          setSocFinal(data.soc_final)
          setPowerEff(Math.round(((data.power / distance) + Number.EPSILON) * 100) / 100)
          setPowerFinal(data.power)
          
      })
    
    }, [mass, area, aux, battery_cap, elv, elevation, drivecycle])


  return (
    <div>
       <Map 
        geom={geom} 
        trace={trace}
        error={line_visbility}
        />
       <Sidebar
        trips={listTrip}
        setTrip={setTripId}
        selectedTrip={tripId}
        routes={listRoute}
        setRoute={setRouteId}
        selectedRoute={routeId}
        drivecycle={drivecycle}
        elevation={elevation}
        soc={soc}
        soc_final={soc_final}
        power_final={power_final}
        power_eff={power_eff}
        distance={distance}
        time={time}
        avg_speed={avg_speed}
        toggle={toggle}
        setToggle={setToggle}
        battery_cap={battery_cap}
        setBatteryCap={setBatteryCap}
        aux={aux}
        setAux={setAux}
        mass={mass}
        setMass={setMass}
        area={area}
        setArea={setArea}
        elv={elv}
        setElv={setElv}
        error={drivecycle_error}
        drawer={isDrawer}
        setDrawer={setDrawer}
        />
    </div>
  );
}

export default App;
