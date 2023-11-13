import React from "react";
import "./css/sidebar.css";
import MyD3Component from './chart';

export default function Sidebar(props) {

  function handleSubmit(e) {
    e.preventDefault();
    console.log(e.target.value);
    props.setTrip(e.target.value);
  }

  function handleRoute(e) {
    e.preventDefault();
    console.log(e.target.value);
    props.setRoute(e.target.value);
  }

  const updateBattCap = (e) => {setTimeout(() => {props.setBatteryCap(e.target.value)},1000)}
  const updateMass = (e) => {setTimeout(() => {props.setMass(e.target.value)},1000)}
  const updateAux = (e) => {setTimeout(() => {props.setAux(e.target.value)},1000)}
  const updateArea = (e) => {setTimeout(() => {props.setArea(e.target.value)},1000)}
  const updateElv =()=>{
    console.log("toggled")
    props.setElv(e => !e)
  }

  return (
    <div className="sidebar-container prose">
      <h1 className="color-blue">Transit Drivecycle</h1>
      

      <div className="flex flex--column">
        <span>
          <div className="select-container py12">
            <select
              className="select select--stroke color-blue"
              value={props.selectedRoute}
              onChange={handleRoute}
            >
              {props.routes.map((item) => (
                <option key={item.route_id} value={item.route_id}>
                  {String(item.route_short_name)} - {item.route_long_name}
                </option>
              ))}
            </select>
            <div className="select-arrow"></div>
          </div>
        </span>
        <div className="select-container mb18">
          <select
            className="select select--stroke color-blue"
            value={props.selectedTrip}
            onChange={handleSubmit}
          >
            {props.trips.map((item) => (
              <option key={item.trip_id} value={item.trip_id.toString()}>
                {item.shape_id.toString()} {item.trip_headsign.toString()}
              </option>
            ))}
          </select>
          <div className="select-arrow"></div>
        </div>

        <div class='grid'>
            <div class='col w-1/4 txt-s'>Batt. Capacity (kWh)</div>
            <div class='col w-1/4 txt-s'>Vehicle Mass (kg)</div>
            <div class='col w-1/4 txt-s'>Frontal Area (m2)</div>
            <div class='col w-1/4 txt-s'>Aux. Power (kW)</div>
        </div>

        <div class='grid grid--gut3 mb12'>
            <div class='col w-1/4 txt-ms'>
                <input class='input' name="battery_cap" onChange={updateBattCap} placeholder='550' />
            </div>
            <div class='col w-1/4 txt-ms'>
                <input class='input' name="mass" onChange={updateMass} placeholder='15000' />
            </div>
            <div class='col w-1/4 txt-ms'>
                <input class='input' name="area" onChange={updateArea} placeholder='10' />
            </div>
            <div class='col w-1/4 txt-ms'>
                <input class='input' name="aux" onChange={updateAux} placeholder='5' />
            </div>
        </div>

        <div>
            <label>
                <input
                    type="checkbox"
                    checked={props.elv}
                    onChange={updateElv} />
                Include Elevation
            </label>
        </div>

        <div className={!props.toggle ? 'hidden' : null} class='mt12'>

            <div class='grid'>
                <div class='col w-1/2 txt-s'>Energy Efficiency</div>
                <div class='col w-1/2 txt-s'>Total Power Used</div>
            </div>


            <div class='grid'>
                <div class='col w-1/2'><h2>{Math.round(((props.power_final / props.distance) + Number.EPSILON) * 100) / 100} kWh/m</h2></div>
                <div class='col w-1/2 txt-s'><h2>{props.power_final} kWh</h2></div>
            </div>

            <div class='grid mt12'>
                <div class='col w-1/2 txt-s'>Charge Used</div>
                <div class='col w-1/2 txt-s'>Average Speed</div>
            </div>


            <div class='grid'>
                <div class='col w-1/2'><h2>{props.soc_final}%</h2></div>
                <div class='col w-1/2 txt-s'><h2>{props.avg_speed} km/h</h2></div>
            </div>


            <div class='grid mt12'>
                <div class='col w-1/2 txt-s'>Route Distance</div>
                <div class='col w-1/2 txt-s'>Run Time</div>
            </div>


            <div class='grid'>
                <div class='col w-1/2'><h2>{props.distance} km</h2></div>
                <div class='col w-1/2 txt-s'><h2>{props.time} mins</h2></div>
            </div>
        </div>

             
        <MyD3Component
            data={props.drivecycle}
            x={0}
            y={1}
            x_label={"Time (s)"}
            y_label={"Speed (m/s)"}
        />

        <MyD3Component
            data={props.drivecycle}
            x={2}
            y={1}
            x_label={"Distance (m)"}
            y_label={"Speed (m/s)"}
        />

        <MyD3Component
            data={props.elevation}
            x={0}
            y={1}
            x_label={"Distance (m)"}
            y_label={"Elevation (m)"}
        />

        <MyD3Component
            data={props.soc}
            x={2}
            y={4}
            x_label={"Distance (m)"}
            y_label={"State of Charge (%)"}
        />

      </div>

    </div>
  );
}
