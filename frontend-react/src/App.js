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
            geom: null
        };
        this.mapContainer = React.createRef();

        this.handleChangeRoute = this.handleChangeRoute.bind(this);
        this.handleChangePattern = this.handleChangePattern.bind(this);
    }

    componentDidMount() {
        this.map = new maplibregl.Map({
            container: this.mapContainer.current,
            style: "https://basemaps.cartocdn.com/gl/positron-gl-style/style.json",
            center: [-114.0708, 51.0486],
            zoom: 11
        });

        let pattern_ = calgary_data.filter(x => x.route === this.state.route)[0].patterns[0]
        let geojson_url = "http://localhost:81/route/?onestop_id=" + pattern_

        this.set_data(pattern_,false)

        this.map.on('load', () => {

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

    set_data(pattern, setdata = true) {
        let url = "http://localhost:81/route/?onestop_id=" + pattern
        fetch(url)
            .then(res => res.json())
            .then(
                (result) => {
                    this.setState({
                        geom: result
                    }, () => {
                        if(setdata){
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
                            })
                        })
                            .then(res => res.json())
                            .then(result => {
                                this.setState({ drivecycle: result }, console.log(this.state.drivecycle))
                            })

                    });
                })
    }

    handleChangeRoute(event) {
        let pattern_ = calgary_data.filter(x => x.route === event.target.value)[0].patterns[0]
        this.setState({ route: event.target.value, pattern: pattern_ },
            () => this.set_data(this.state.pattern, true));
    }

    handleChangePattern(event) {
        this.setState({ pattern: event.target.value },
            () => this.set_data(this.state.pattern, true));
    }

    render() {

        let charts;

        if (this.state.drivecycle) {
            console.log("component updated")
            charts = <MyD3Component
                data={this.state.drivecycle}
            />
        } else {
            charts = <div></div>
        }


        return (
            <div>

                <div ref={this.mapContainer} className="map-container" />

                <div className='sidebar-container bg-red-faint px12 py12 mx24 my24'>
                    <div className="prose">

                        <h2>Transit Drivecycle</h2>

                        <div className='select-container'>
                            Route:
                            <select
                                className='select select--stroke'
                                value={this.state.route}
                                onChange={this.handleChangeRoute}
                            >
                                {calgary_data.map((option) => <option key={option.route} value={option.route} >{option.route_number} {option.route_long_name}</option>)}
                            </select>
                            <div className='select-arrow'></div>
                        </div>


                        <div className='select-container'>
                            Route Pattern:
                            <select
                                className='select select--stroke'
                                value={this.state.pattern}
                                onChange={this.handleChangePattern}
                            >
                                {calgary_data.filter(x => x.route === this.state.route).map((option) => option.patterns.map((list => <option key={list} value={list}>{list}</option>)))}
                            </select>
                            <div className='select-arrow'></div>
                        </div>

                        {charts}

                        {/* <MyD3Component
                            data={data_new}
                        /> */}
                    </div>
                </div>
            </div>
        );
    }
}