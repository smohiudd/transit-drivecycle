import React from 'react';
import maplibregl from 'maplibre-gl';
import MyD3Component from './barchart';
import calgary_data from './calgary_routes.json';



export default class App extends React.PureComponent {
    constructor(props) {
        super(props);
        this.state = {
            city: null,
            route: "r-c3nf-1",
            pattern: "",
            drivecycle: null,
            elevation: null,
            soc: null,
            soc_final: null,
            geom: null,
            drivecycle_error: null,
            toggle: true,
            distance: null,
            time: null,
            avg_speed: null,
            battery_cap: 550,
            aux: null,
            mass: 10000,
            gear_ratio: null,
            wheel: null,
            area: 8.0,
        };
        this.mapContainer = React.createRef();

        this.handleChangeRoute = this.handleChangeRoute.bind(this);
        this.handleChangePattern = this.handleChangePattern.bind(this);
        this.toggleState = this.toggleState.bind(this)
        this.handleInputChange = this.handleInputChange.bind(this)

        this.inputimer = null
    }

    componentDidMount() {
        this.map = new maplibregl.Map({
            container: this.mapContainer.current,
            style: "https://basemaps.cartocdn.com/gl/positron-gl-style/style.json",
            center: [-114.0708, 51.0486],
            zoom: 11
        });

        let pattern_ = calgary_data.filter(x => x.route === this.state.route)[0].patterns[0]
        this.setState({ pattern: pattern_ })

        this.set_data(pattern_, false,true)
        // this.set_energy()

        this.map.on('load', () => {

            let geojson_url = "http://localhost:81/route/?onestop_id=" + pattern_


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
                    'line-color': 'red',
                    'line-width': 4
                }
            });

        })
    }

    set_data(pattern, setdata = true, energy = false) {
        let url = "http://localhost:81/route/?onestop_id=" + pattern
        fetch(url)
            .then(res => res.json())
            .then(
                (result) => {
                    this.setState({
                        geom: result
                    }, () => {
                        if (setdata) {
                            this.map.getSource('Route').setData(result)
                        }
                        fetch('http://localhost:81/drivecycle_post/', {
                            method: 'POST',
                            headers: {
                                'Accept': 'application/json',
                                'Content-Type': 'application/json',
                            },
                            body: JSON.stringify({
                                geom: result,
                                mass: this.state.mass,
                                area: this.state.area,
                                capacity: this.state.battery_cap,
                            })
                        })
                            .then(res => {
                                if (!res.ok) this.setState({ drivecycle_error: true });
                                else return res.json();
                            })
                            .then(result => {
                                this.setState({
                                    drivecycle: result,
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
        fetch('http://localhost:81/energy/', {
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
            })
        })
            .then(res => {
                if (!res.ok) this.setState({ drivecycle_error: true });
                else return res.json();
            })
            .then(result => {
                this.setState({
                    soc: result.soc,
                    soc_final: result.soc_final
                })
            })
    }

    handleChangeRoute(event) {
        let pattern_ = calgary_data.filter(x => x.route === event.target.value)[0].patterns[0]
        this.setState({ route: event.target.value, pattern: pattern_, drivecycle_error: false },
            () => this.set_data(this.state.pattern, true, true));
    }

    handleChangePattern(event) {
        this.setState({ pattern: event.target.value, drivecycle_error: false },
            () => this.set_data(this.state.pattern, true, true));
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

                <div className='sidebar-container bg-blue-faint px18 py18 mx24 my24 scroll-styled overflow-auto'>
                    <div className="prose">

                        <h1>Transit Drivecycle</h1>
                        <p class="txt-h5">A tool for simulating drive cycles and trip data for battery electric bus routes using the Drivecycle python package.</p>

                        <div class='grid'>
                            <div class='col w-1/2 txt-s'>Route</div>
                            <div class='col w-1/2 txt-s'>Pattern</div>
                        </div>


                        <div class='grid grid--gut6 mb12'>
                            <div class='col w-1/2'>
                                <div className='select-container bg-blue-lighter w-full px6'>
                                    <select
                                        className='select'
                                        value={this.state.route}
                                        onChange={this.handleChangeRoute}
                                    >
                                        {calgary_data.map((option) => <option key={option.route} value={option.route} >{option.route_number} {option.route_long_name}</option>)}
                                    </select>
                                    <div className='select-arrow'></div>
                                </div>
                            </div>
                            <div class='col w-1/2'>
                                <div className='select-container bg-blue-lighter w-full px6'>
                                    <select
                                        className='select'
                                        value={this.state.pattern}
                                        onChange={this.handleChangePattern}
                                    >
                                        {calgary_data.filter(x => x.route === this.state.route).map((option) => option.patterns.map((list => <option key={list} value={list}>{list}</option>)))}
                                    </select>
                                    <div className='select-arrow'></div>
                                </div>
                            </div>
                        </div>



                        <div class='grid'>
                            <div class='col w-1/3 txt-s'>Battery Capacity (kWh)</div>
                            <div class='col w-1/3 txt-s'>Vehicle Mass (kg)</div>
                            <div class='col w-1/3 txt-s'>Aux. Power (kWH)</div>
                        </div>

                        <div class='grid grid--gut3 mb12'>
                            <div class='col w-1/3 txt-ms'>
                                <input class='input' name="battery_cap" onChange={this.handleInputChange} placeholder='550' />
                            </div>
                            <div class='col w-1/3 txt-ms'>
                                <input class='input' name="mass" onChange={this.handleInputChange} placeholder='15000' />
                            </div>
                            <div class='col w-1/3 txt-ms'>
                                <input class='input' name="aux" onChange={this.handleInputChange} placeholder='10' />
                            </div>
                        </div>

                        <div class='grid'>
                            <div class='col w-1/3 txt-s'>Gear Ratio</div>
                            <div class='col w-1/3 txt-s'>Wheel Radius (m)</div>
                            <div class='col w-1/3 txt-s'>Frontal Area (m2)</div>
                        </div>

                        <div class='grid grid--gut3 mb12'>
                            <div class='col w-1/3 txt-ms'>
                                <input class='input' name="gear_ratio" onChange={this.handleInputChange} placeholder='5.0' />
                            </div>
                            <div class='col w-1/3 txt-ms'>
                                <input class='input' name="wheel" onChange={this.handleInputChange} placeholder='0.5' />
                            </div>
                            <div class='col w-1/3 txt-ms'>
                                <input class='input' name="area" onChange={this.handleInputChange} placeholder='10' />
                            </div>
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
                                <div class='col w-1/2'><h1>1.2 kWh/m</h1></div>
                                <div class='col w-1/2 txt-s'><h1>200 kWh</h1></div>
                            </div>

                            <div class='grid mt24'>
                                <div class='col w-1/2 txt-s'>Charge Used</div>
                                <div class='col w-1/2 txt-s'>Average Speed</div>
                            </div>


                            <div class='grid'>
                                <div class='col w-1/2'><h1>{this.state.soc_final}%</h1></div>
                                <div class='col w-1/2 txt-s'><h1>{this.state.avg_speed} km/h</h1></div>
                            </div>


                            <div class='grid mt24'>
                                <div class='col w-1/2 txt-s'>Route Distance</div>
                                <div class='col w-1/2 txt-s'>Run Time</div>
                            </div>


                            <div class='grid'>
                                <div class='col w-1/2'><h1>{this.state.distance}km</h1></div>
                                <div class='col w-1/2 txt-s'><h1>{this.state.time} mins</h1></div>
                            </div>
                        </div>

                        {charts}

                    </div>
                </div>
            </div>
        );
    }
}