import React from 'react';
import maplibregl from 'maplibre-gl';
import bbox from '@turf/bbox';
import MyD3Component from './barchart';
import calgary_data from './calgary_routes.json';
import all_routes from './all_routes.json';

export default class App extends React.PureComponent {
    constructor(props) {
        super(props);
        this.state = {
            city: "o-c3nf-calgarytransit",
            route: "r-c3nf-1",
            pattern: "",
            drivecycle: null,
            elevation: null,
            soc: null,
            soc_final: null,
            power_final: null,
            geom: null,
            drivecycle_error: null,
            toggle: true,
            distance: null,
            time: null,
            avg_speed: null,
            battery_cap: 550,
            aux: 5,
            mass: 10000,
            area: 8.0,
            elv_check: true
        };
        this.mapContainer = React.createRef();

        this.handleChangeRoute = this.handleChangeRoute.bind(this);
        this.handleChangePattern = this.handleChangePattern.bind(this);
        this.handleChangeCity = this.handleChangeCity.bind(this);
        this.handleChangeElv = this.handleChangeElv.bind(this);
        this.toggleState = this.toggleState.bind(this);
        this.handleInputChange = this.handleInputChange.bind(this);

        this.inputimer = null
    }

    componentDidMount() {
        this.map = new maplibregl.Map({
            container: this.mapContainer.current,
            style: "https://basemaps.cartocdn.com/gl/positron-gl-style/style.json",
            center: [-113.98968, 51.03338],
            zoom: 12
        });

        let pattern_ = calgary_data.filter(x => x.route === this.state.route)[0].patterns[0]
        this.setState({ pattern: pattern_ })

        this.set_data(pattern_, false, true)
        // this.set_energy()

        this.map.on('load', () => {

            let geojson_url = `/route/?onestop_id=${pattern_}`

            this.map.addSource('Route', {
                type: 'geojson',
                data: geojson_url
            });

            this.map.addLayer({
                'id': 'route',
                'type': 'line',
                'source': 'Route',
                'layout': {
                    'line-join': 'round',
                    'line-cap': 'round'
                },
                'paint': {
                    'line-color': 'blue',
                    'line-width': 3
                }
            });

        })
    }

    set_data(pattern, setdata = true, energy = false) {
        let url = `/route/?onestop_id=` + pattern
        fetch(url)
            .then(res => res.json())
            .then(
                (result) => {
                    this.setState({
                        geom: result
                    }, () => {
                        if (setdata) {
                            this.map.getSource('Route').setData(result)
                            var box = bbox(result);
                            this.map.fitBounds(box, { padding: 30 });
                        }
                        fetch(`/drivecycle_post/`, {
                            method: 'POST',
                            headers: {
                                'Accept': 'application/json',
                                'Content-Type': 'application/json',
                            },
                            body: JSON.stringify({
                                geom: result
                            })
                        })
                            .then(res => {
                                if (!res.ok) this.setState({ drivecycle_error: true });
                                else return res.json();
                            })
                            .then(result => {
                                this.setState({
                                    drivecycle: result,
                                    elevation:result.elv,
                                    distance: result.dist,
                                    time: result.time,
                                    avg_speed: result.avg_speed,
                                }, () => {
                                    if (energy) this.set_energy()
                                })
                            })

                    });
                })
    }

    set_energy() {
        fetch(`/energy/`, {
            method: 'POST',
            headers: {
                'Accept': 'application/json',
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                traj: this.state.drivecycle.data,
                mass: this.state.mass,
                area: this.state.area,
                capacity: this.state.battery_cap,
                aux: this.state.aux,
                elv: this.state.elevation
            })
        })
            .then(res => {
                if (!res.ok) this.setState({ drivecycle_error: true });
                else return res.json();
            })
            .then(result => {
                this.setState({
                    soc: result.soc,
                    soc_final: result.soc_final,
                    power_final: result.power
                })
            })
    }

    handleChangeCity(event) {
        let route_ = all_routes[event.target.value].routes[0].route
        let pattern_ = all_routes[event.target.value].routes.filter(x => x.route === route_)[0].patterns[0]
        this.setState({ city: event.target.value, route: route_, pattern: pattern_, drivecycle_error: false },
            () => this.set_data(this.state.pattern, true, true));
    }


    handleChangeRoute(event) {
        let pattern_ = all_routes[this.state.city].routes.filter(x => x.route === event.target.value)[0].patterns[0]
        this.setState({ route: event.target.value, pattern: pattern_, drivecycle_error: false },
            () => this.set_data(this.state.pattern, true, true));
    }

    handleChangePattern(event) {
        this.setState({ pattern: event.target.value, drivecycle_error: false },
            () => this.set_data(this.state.pattern, true, true));
    }

    handleChangeElv(){
        let elv_state = this.state.elv_check ? null : this.state.drivecycle.elv
        this.setState(prevState => ({
            elv_check: !prevState.elv_check,
            elevation:elv_state
          }),
          ()=> {
            this.set_energy()
        });
        
    }

    toggleState() {
        this.setState({
            toggle: !this.state.toggle
        });
    }

    handleInputChange(e) {
        var duration = 800;
        clearTimeout(this.inputimer);
        this.inputimer = setTimeout(() => {
            this.updateInputValue(e);
        }, duration);
    }

    updateInputValue = (e) => {
        this.setState({ [e.target.name]: e.target.value }, () => this.set_energy());
    }

    render() {

        let charts;
        let error;

        if (this.state.drivecycle && this.state.soc && !this.state.drivecycle_error) {
            charts = <div>
                <MyD3Component
                    data={this.state.drivecycle.data}
                    x={0}
                    y={1}
                    x_label={"Time (s)"}
                    y_label={"Speed (m/s)"}
                />
                <MyD3Component
                    data={this.state.drivecycle.elv}
                    x={0}
                    y={1}
                    x_label={"Distance (m)"}
                    y_label={"Elevation (m)"}
                />
                <MyD3Component
                    data={this.state.soc}
                    x={2}
                    y={4}
                    x_label={"Distance (m)"}
                    y_label={"State of Charge (%)"}
                />
            </div>


        }

        if (this.state.drivecycle_error) {
            error = <div>Error: Could not generate drivecycle.</div>
        }

        return (
            <div>

                <div ref={this.mapContainer} className="map-container" />

                <div className='sidebar-container bg-blue-faint scroll-styled overflow-auto'>
                    <div className="prose">

                        <h1 class="txt-shadow-darken50">Transit Drivecycle</h1>
                        <p class="txt-h5">A tool for simulating drive cycles and trip data for battery electric bus routes using the <a href="https://github.com/smohiudd/drivecycle">Drivecycle</a> python package. <a href="http://www.saadiqm.com">www.saadiqm.com</a></p>
                        

                        <div class='grid'>
                            <div class='col w-1/3 txt-s'>Agency</div>
                            <div class='col w-1/3 txt-s'>Route</div>
                            <div class='col w-1/3 txt-s'>Pattern</div>
                        </div>


                        <div class='grid grid--gut6 mb12'>

                            <div class='col w-1/3'>
                                <div className='select-container bg-blue-lighter w-full px6'>
                                    <select
                                        className='select'
                                        value={this.state.city}
                                        onChange={this.handleChangeCity}
                                    >
                                        {Object.keys(all_routes).map((key) => <option key={key} value={key}>{all_routes[key].agency}</option>)}
                                    </select>
                                    <div className='select-arrow'></div>
                                </div>
                            </div>
                            <div class='col w-1/3'>
                                <div className='select-container bg-blue-lighter w-full px6'>
                                    <select
                                        className='select'
                                        value={this.state.route}
                                        onChange={this.handleChangeRoute}
                                    >
                                        {/* {calgary_data.map((option) => <option key={option.route} value={option.route} >{option.route_number} {option.route_long_name}</option>)} */}
                                        {all_routes[this.state.city].routes.map((option) => <option key={option.route} value={option.route} >{option.route_number} {option.route_long_name}</option>)}
                                    </select>
                                    <div className='select-arrow'></div>
                                </div>
                            </div>
                            <div class='col w-1/3'>
                                <div className='select-container bg-blue-lighter w-full px6'>
                                    <select
                                        className='select'
                                        value={this.state.pattern}
                                        onChange={this.handleChangePattern}
                                    >
                                        {/* {calgary_data.filter(x => x.route === this.state.route).map((option) => option.patterns.map((list => <option key={list} value={list}>{list}</option>)))} */}
                                        {all_routes[this.state.city].routes.filter(x => x.route === this.state.route).map((option) => option.patterns.map((list => <option key={list} value={list}>{list}</option>)))}
                                    </select>
                                    <div className='select-arrow'></div>
                                </div>
                            </div>
                        </div>





                        <div class='grid'>
                            <div class='col w-1/4 txt-s'>Batt. Capacity (kWh)</div>
                            <div class='col w-1/4 txt-s'>Vehicle Mass (kg)</div>
                            <div class='col w-1/4 txt-s'>Frontal Area (m2)</div>
                            <div class='col w-1/4 txt-s'>Aux. Power (kW)</div>
                        </div>

                        <div class='grid grid--gut3 mb12'>
                            <div class='col w-1/4 txt-ms'>
                                <input class='input' name="battery_cap" onChange={this.handleInputChange} placeholder='550' />
                            </div>
                            <div class='col w-1/4 txt-ms'>
                                <input class='input' name="mass" onChange={this.handleInputChange} placeholder='15000' />
                            </div>
                            <div class='col w-1/4 txt-ms'>
                                <input class='input' name="area" onChange={this.handleInputChange} placeholder='10' />
                            </div>
                            <div class='col w-1/4 txt-ms'>
                                <input class='input' name="aux" onChange={this.handleInputChange} placeholder='5' />
                            </div>
                        </div>

                        <div>
                            <label>
                                <input
                                    type="checkbox"
                                    checked={this.state.elv_check}
                                    onChange={this.handleChangeElv} />
                                Include Elevation
                            </label>
                        </div>

                        {/* 
                        <div class='toggle-group mt6 mb18'>
                            <label class='toggle-container w120'>
                                <input name='toggle-1' type='radio' onChange={this.toggleState} checked={!this.state.toggle} />
                                <div class='toggle'>Charts</div>
                            </label>
                            <label class='toggle-container w120'>
                                <input name='toggle-1' type='radio' onChange={this.toggleState} checked={this.state.toggle} />
                                <div class='toggle'>Indicators</div>
                            </label>
                        </div>
                 */}

                        {error}

                        <div className={!this.state.toggle ? 'hidden' : null} class='mt12'>

                            <div class='grid'>
                                <div class='col w-1/2 txt-s'>Energy Efficiency</div>
                                <div class='col w-1/2 txt-s'>Total Power Used</div>
                            </div>


                            <div class='grid'>
                                <div class='col w-1/2'><h2>{Math.round(((this.state.power_final / this.state.distance) + Number.EPSILON) * 100) / 100} kWh/m</h2></div>
                                <div class='col w-1/2 txt-s'><h2>{this.state.power_final} kWh</h2></div>
                            </div>

                            <div class='grid mt12'>
                                <div class='col w-1/2 txt-s'>Charge Used</div>
                                <div class='col w-1/2 txt-s'>Average Speed</div>
                            </div>


                            <div class='grid'>
                                <div class='col w-1/2'><h2>{this.state.soc_final}%</h2></div>
                                <div class='col w-1/2 txt-s'><h2>{this.state.avg_speed} km/h</h2></div>
                            </div>


                            <div class='grid mt12'>
                                <div class='col w-1/2 txt-s'>Route Distance</div>
                                <div class='col w-1/2 txt-s'>Run Time</div>
                            </div>


                            <div class='grid'>
                                <div class='col w-1/2'><h2>{this.state.distance} km</h2></div>
                                <div class='col w-1/2 txt-s'><h2>{this.state.time} mins</h2></div>
                            </div>
                        </div>

                        <div className="svg-container">
                            {charts}

                        </div>



                    </div>
                </div>
            </div>
        );
    }
}