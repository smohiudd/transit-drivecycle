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
  const toggleDrawer = () => {
    props.setDrawer(e => !e); 
   };

  return (
    
    <div className={props.drawer ? "sidebar-container prose" : "sidebar-container-full prose"}>
      <div id="button-visibility" className="show-button">
        
        <button onClick={toggleDrawer} className='btn btn--green btn--s'>{props.drawer ? "Click to Expand" : "Click to Collapse"}</button>
      </div>
      
      <div className="txt-h1 color-blue mt12 mb6">Transit Drivecycle</div>
      <p className="color-blue txt-ms">This app uses <a href="https://github.com/smohiudd/drivecycle">Drivecycle</a> to dynamically generate speed profiles and energy consumption of bus routes.
      See the <a href="https://github.com/smohiudd/transit-drivecycle">github repo</a> for more info on how this app is deployed. </p>
      

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
        <div className="select-container mb6">
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

        <div style={{visibility: props.error ? 'visible' : 'hidden' }}>
          <div className="txt-h5 color-orange mb6 align-center animation-fade-in-out animation--infinite">Not able to generate speed (No Trace).</div>
        </div>

        <div class='grid'>
            <div class='col w-1/4 txt-s'>Batt. Capacity</div>
            <div class='col w-1/4 txt-s'>Vehicle Mass</div>
            <div class='col w-1/4 txt-s'>Frontal Area</div>
            <div class='col w-1/4 txt-s'>Aux. Power</div>
        </div>

        <div class='grid grid--gut3 mb12'>
            <div class='col w-1/4 txt-ms'>
                <input class='input' name="battery_cap" onChange={updateBattCap} placeholder='550 kWh' />
            </div>
            <div class='col w-1/4 txt-ms'>
                <input class='input' name="mass" onChange={updateMass} placeholder='15000 kg' />
            </div>
            <div class='col w-1/4 txt-ms'>
                <input class='input' name="area" onChange={updateArea} placeholder='10 m2' />
            </div>
            <div class='col w-1/4 txt-ms'>
                <input class='input' name="aux" onChange={updateAux} placeholder='5 kWh' />
            </div>
        </div>

        <div>
            <label className="txt-ms">
                <input
                    type="checkbox"
                    checked={props.elv}
                    onChange={updateElv} />
                 Include Elevation
            </label>
        </div>

        <div class='mt12'>

            <div class='grid'>
                <div class='col w-1/2 txt-s'>Energy Efficiency</div>
                <div class='col w-1/2 txt-s'>Total Power Used</div>
            </div>


            <div class='grid'>
                <div class='col w-1/2'><h3>{props.power_eff} kWh/m</h3></div>
                <div class='col w-1/2 txt-s'><h3>{props.power_final} kWh</h3></div>
            </div>

            <div class='grid mt6'>
                <div class='col w-1/2 txt-s'>Charge Used</div>
                <div class='col w-1/2 txt-s'>Average Speed</div>
            </div>


            <div class='grid'>
                <div class='col w-1/2'><h3>{props.soc_final}%</h3></div>
                <div class='col w-1/2 txt-s'><h3>{props.avg_speed} km/h</h3></div>
            </div>


            <div class='grid mt6'>
                <div class='col w-1/2 txt-s'>Route Distance</div>
                <div class='col w-1/2 txt-s'>Run Time</div>
            </div>


            <div class='grid'>
                <div class='col w-1/2'><h3>{props.distance} km</h3></div>
                <div class='col w-1/2 txt-s'><h3>{props.time} mins</h3></div>
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
