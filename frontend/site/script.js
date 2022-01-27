function responsivefy(svg) {
    const container = d3.select(svg.node().parentNode),
        width = parseInt(svg.style('width'), 10),
        height = parseInt(svg.style('height'), 10),
        aspect = width / height;
   
    svg.attr('viewBox', `0 0 ${width} ${height}`)
        .attr('preserveAspectRatio', 'xMinYMid')
        .call(resize);
   
    d3.select(window).on(
        'resize.' + container.attr('id'), 
        resize
    );
   
    function resize() {
        const w = parseInt(container.style('width'));
        svg.attr('width', w);
        svg.attr('height', Math.round(w / aspect));
    }
}


mapboxgl.accessToken = 'pk.eyJ1Ijoic2FhZGlxbSIsImEiOiJjamJpMXcxa3AyMG9zMzNyNmdxNDlneGRvIn0.wjlI8r1S_-xxtq2d-W5qPA';
const transitland_endpoint = 'https://b9d8625q6c.execute-api.us-east-1.amazonaws.com'
// const transitland_endpoint = 'http://localhost:3000/'

var map = new mapboxgl.Map({
    container: 'map', // container id
    style: 'mapbox://styles/saadiqm/cjx964vch2dtg1cm9vmsl9bsa', // style URL
    center: [-114, 51], // starting position [lng, lat]
    zoom: 9 // starting zoom
});

var isLoading = d3.select("div#is_loading")
var showTitle = d3.selectAll("div#titles")
var showError = d3.selectAll("div#error")

var margin = { top: 40, right: 100, bottom: 60, left: 70 }
    , width = 750
    , height = 400

const svg = d3.select("div#container1").append("svg")
    .attr("width", width + margin.left + margin.right)
    .attr("height", height + margin.top + margin.bottom)
    .call(responsivefy)
    .append("g")
    .attr("transform", "translate(" + margin.left + "," + margin.top + ")");

const svg2 = d3.select("div#container2").append("svg")
    .attr("width", width + margin.left + margin.right)
    .attr("height", height + margin.top + margin.bottom)
    .call(responsivefy)
    .append("g")
    .attr("transform", "translate(" + margin.left + "," + margin.top + ")");

const svg3 = d3.select("div#container3").append("svg")
    .attr("width", width + margin.left + margin.right)
    .attr("height", height + margin.top + margin.bottom)
    .call(responsivefy)
    .append("g")
    .attr("transform", "translate(" + margin.left + "," + margin.top + ")");

const svg4 = d3.select("div#container4").append("svg")
    .attr("width", width + margin.left + margin.right)
    .attr("height", height + margin.top + margin.bottom)
    .call(responsivefy)
    .append("g")
    .attr("transform", "translate(" + margin.left + "," + margin.top + ")");


let selected_operator = document.getElementById("operator").value
get_operator(selected_operator).then(url => get_data(url)).catch(error => {
    console.log("Could not list routes")
    isLoading.classed("loading loading--s", !isLoading.classed("loading loading--s"));
    showError.classed("none",false)
  });


d3.select("select#operator").on("change", function () {
    isLoading.classed("loading loading--s", !isLoading.classed("loading loading--s"));
    var selectedoperator = d3.select(this).property('value')
    console.log(selectedoperator)

    get_operator(selectedoperator).then(url => get_data(url)).catch(error => {
       console.log("Could not list routes")
       isLoading.classed("loading loading--s", !isLoading.classed("loading loading--s"));
       showError.classed("none",false)
      });
})


function get_data(url){
    d3.json(url).then(data => {

        isLoading.classed("loading loading--s", !isLoading.classed("loading loading--s"));
        showError.classed("none",true)
        
        let routes = data.routes.map(x => {
            let a = {
                onestop_id:x.onestop_id,
                route:x.name,
                route_long_name:x.tags.route_long_name,
                route_stop_patterns:x.route_stop_patterns_by_onestop_id
            }
            return a
        });
    
        let routes2 = routes.filter(x=>x.route_stop_patterns.length>0)

        d3.select("select#routes").html("")
        d3.select("select#patterns").html("")
        
        d3.select("select#routes").selectAll("option")
        .data(routes2)
        .enter()
        .append("option")
        .attr("value", (d) => d.onestop_id)
        .text((d) => d.route+" "+d.route_long_name)
    
        let selected_route = document.getElementById("routes").value
        let patterns2 = routes2.filter(x => x.onestop_id === selected_route)[0].route_stop_patterns
    
        d3.select("select#patterns").selectAll("option")
        .data(patterns2)
        .enter()
        .append("option")
        .attr("value", (d) => d)
        .text((d) => d)
        
        get_drive_cycle(patterns2[0])
        isLoading.classed("loading loading--s", !isLoading.classed("loading loading--s"));
        showError.classed("none",true)
        
        d3.select("select#routes").on("change", function () {
            showError.classed("none",true)
            var selectedroute = d3.select(this).property('value')
    
            let patterns = routes2.filter(x => x.onestop_id === selectedroute)[0].route_stop_patterns
    
            d3.select("select#patterns").html("")
    
            d3.select("select#patterns").selectAll("option")
            .data(patterns)
            .enter()
            .append("option")
            .attr("value", (d) => d)
            .text((d) => d)


            get_drive_cycle(patterns[0])
            isLoading.classed("loading loading--s", !isLoading.classed("loading loading--s"));
    
        })
    
        d3.select("select#patterns").on("change", function () {
            isLoading.classed("loading loading--s", !isLoading.classed("loading loading--s"));
            showError.classed("none",true)
            var selectedpattern = d3.select(this).property('value')
            get_drive_cycle(selectedpattern)
    
        });
    })
}

function get_drive_cycle(pattern) {

    const params = {
        onestop_id:pattern
    }

    const transitland = new URL('/dev/stops',transitland_endpoint)
    const url = new URL('/dev/drivecycle',transitland_endpoint)

    Object.keys(params).forEach(key => url.searchParams.append(key, params[key]))
    Object.keys(params).forEach(key => transitland.searchParams.append(key, params[key]))

    const drivecycle_url = decodeURIComponent(url.href)
    const transitland_route_url = decodeURIComponent(transitland.href)

    Promise.all([
        d3.json(drivecycle_url),
        d3.json(transitland_route_url)
    ]).then(([drivecycle,route]) =>{

        isLoading.classed("loading loading--s", !isLoading.classed("loading loading--s"));
        showTitle.classed("none", false);

        // if (drivecycle.data==0){
        //     showError.classed("none",false)
        //     return
        // }

        if (map.getSource("route")) {
            map.getSource('route').setData(route);
            var bbox = turf.bbox(route);
            console.log("zoom")
            map.fitBounds(bbox, {padding: 30});
            
        }else{
            map.addSource('route', {
                'type': 'geojson',
                'data': route
            });
            map.addLayer({
                'id': 'route',
                'type': 'line',
                'source': 'route',
                'layout': {
                    'line-join': 'round',
                    'line-cap': 'round'
                },
                'paint': {
                    'line-color': '#ff8987',
                    'line-width': 3
                }
            });
            var bbox = turf.bbox(route);
            console.log("zoom")
            map.fitBounds(bbox, {padding: 30});
        }

    
        map.on('data', function (e) {

            if (map.isSourceLoaded('route')) {
               
            }

            // if (e.sourceId !== 'route' || !e.isSourceLoaded) return
            // var f = map.querySourceFeatures('route')
            // if (f.length === 0) return
            // var bbox = turf.bbox(route);
            // map.fitBounds(bbox, {padding: 30});    
        })
        
        svg.selectAll("*").remove();
        svg2.selectAll("*").remove();
        svg3.selectAll("*").remove();
        svg4.selectAll("*").remove();

        const xScale = d3.scaleLinear().range([0, width]);
        const yScale = d3.scaleLinear().range([height, 0]);

        xScale.domain(d3.extent(drivecycle.data, d => d[0]));
        yScale.domain(d3.extent(drivecycle.data, d => d[1]));

        const yaxis = d3.axisLeft()
            .scale(yScale);

        const xaxis = d3.axisBottom()
            .scale(xScale)

        svg.append("g")
            .attr("class", "axis")
            .attr("transform", "translate(0," + height + ")")
            .call(xaxis);

        svg.append("g")
            .attr("class", "axis")
            .call(yaxis);

        svg.append("path")
        .datum(drivecycle.data)
        .attr("fill", "none")
        .attr("stroke", "#4096ff")
        .attr("stroke-width", 1.5)
        .attr("d", d3.line()
            .x(function(d) { return xScale(d[0]) })
            .y(function(d) { return yScale(d[1]) })
            )

            // Add the text label for X Axis
        svg.append("text")
            .attr("text-anchor", "middle")  // this makes it easy to centre the text as the transform is applied to the anchor
            .attr("transform", "translate(" + (width / 2) + "," + (height + 40) + ")")  // centre below axis
            .text("Time (s)")
            .style("font", "12px sans-serif")

        // Add the text label for Y Axis
        svg.append("text")
            .attr("text-anchor", "middle")  // this makes it easy to centre the text as the transform is applied to the anchor
            .attr("transform", "translate(" + (0 - 50) + "," + (height / 2) + ")rotate(-90)")  // text is drawn off the screen top left, move down and out and rotate
            .text("Speed (m/s)")
            .style("font", "12px sans-serif")


        // SVG 2
        const yScale2 = d3.scaleLinear().range([height, 0]);
        yScale2.domain(d3.extent(drivecycle.data, d => d[2]));

        const yaxis2 = d3.axisLeft()
            .scale(yScale2);

        const xaxis2 = d3.axisBottom()
            .scale(xScale)

        svg2.append("g")
            .attr("class", "axis")
            .attr("transform", "translate(0," + height + ")")
            .call(xaxis2);

        svg2.append("g")
            .attr("class", "axis")
            .call(yaxis2);

        svg2.append("path")
            .datum(drivecycle.data)
            .attr("fill", "none")
            .attr("stroke", "#4096ff")
            .attr("stroke-width", 1.5)
            .attr("d", d3.line()
            .x(function(d) { return xScale(d[0]) })
            .y(function(d) { return yScale2(d[2]) })
            )

            // Add the text label for X Axis
        svg2.append("text")
            .attr("text-anchor", "middle")  // this makes it easy to centre the text as the transform is applied to the anchor
            .attr("transform", "translate(" + (width / 2) + "," + (height + 40) + ")")  // centre below axis
            .text("Time (s)")
            .style("font", "12px sans-serif")

        // Add the text label for Y Axis
        svg2.append("text")
            .attr("text-anchor", "middle")  // this makes it easy to centre the text as the transform is applied to the anchor
            .attr("transform", "translate(" + (0 - 50) + "," + (height / 2) + ")rotate(-90)")  // text is drawn off the screen top left, move down and out and rotate
            .text("Distance (m)")
            .style("font", "12px sans-serif")

        //SVG 3
        const xScale3 = d3.scaleLinear().range([0, width]);
        const yScale3 = d3.scaleLinear().range([height, 0]);

        xScale3.domain(d3.extent(drivecycle.data, d => d[2]));
        yScale3.domain(d3.extent(drivecycle.data, d => d[1]));

        const yaxis3 = d3.axisLeft()
            .scale(yScale3);

        const xaxis3 = d3.axisBottom()
            .scale(xScale3)

        svg3.append("g")
            .attr("class", "axis")
            .attr("transform", "translate(0," + height + ")")
            .call(xaxis3);

        svg3.append("g")
            .attr("class", "axis")
            .call(yaxis3);

        svg3.append("path")
        .datum(drivecycle.data)
        .attr("fill", "none")
        .attr("stroke", "#4096ff")
        .attr("stroke-width", 1.5)
        .attr("d", d3.line()
            .x(function(d) { return xScale3(d[2]) })
            .y(function(d) { return yScale3(d[1]) })
            )

            // Add the text label for X Axis
        svg3.append("text")
            .attr("text-anchor", "middle")  // this makes it easy to centre the text as the transform is applied to the anchor
            .attr("transform", "translate(" + (width / 2) + "," + (height + 40) + ")")  // centre below axis
            .text("Distance (m)")
            .style("font", "14px sans-serif")

        // Add the text label for Y Axis
        svg3.append("text")
            .attr("text-anchor", "middle")  // this makes it easy to centre the text as the transform is applied to the anchor
            .attr("transform", "translate(" + (0 - 50) + "," + (height / 2) + ")rotate(-90)")  // text is drawn off the screen top left, move down and out and rotate
            .text("Speed (m/s)")
            .style("font", "14px sans-serif")

        
        //SVG 4
        const xScale4 = d3.scaleLinear().range([0, width]);
        const yScale4 = d3.scaleLinear().range([height, 0]);

        xScale4.domain(d3.extent(drivecycle.elv, d => d[0]));
        yScale4.domain(d3.extent(drivecycle.elv, d => d[1]));

        const yaxis4 = d3.axisLeft()
            .scale(yScale4);

        const xaxis4 = d3.axisBottom()
            .scale(xScale4)

        svg4.append("g")
            .attr("class", "axis")
            .attr("transform", "translate(0," + height + ")")
            .call(xaxis4);

        svg4.append("g")
            .attr("class", "axis")
            .call(yaxis4);

        svg4.append("path")
        .datum(drivecycle.elv)
        .attr("fill", "none")
        .attr("stroke", "#4096ff")
        .attr("stroke-width", 1.5)
        .attr("d", d3.line()
            .x(function(d) { return xScale4(d[0]) })
            .y(function(d) { return yScale4(d[1]) })
            )

            // Add the text label for X Axis
        svg4.append("text")
            .attr("text-anchor", "middle")  // this makes it easy to centre the text as the transform is applied to the anchor
            .attr("transform", "translate(" + (width / 2) + "," + (height + 40) + ")")  // centre below axis
            .text("Distance (m)")
            .style("font", "14px sans-serif")

        // Add the text label for Y Axis
        svg4.append("text")
            .attr("text-anchor", "middle")  // this makes it easy to centre the text as the transform is applied to the anchor
            .attr("transform", "translate(" + (0 - 50) + "," + (height / 2) + ")rotate(-90)")  // text is drawn off the screen top left, move down and out and rotate
            .text("Elevation (m)")
            .style("font", "14px sans-serif")
    }).catch(error => {
        console.error("There was an error")
        isLoading.classed("loading loading--s", !isLoading.classed("loading loading--s"));
        showError.classed("none",false)
      });

}

function get_operator(operator){

    return new Promise(function(resolve, reject) {
        const params = {
            operated_by:operator
        }
        const url = new URL('/dev/routes',transitland_endpoint)
        Object.keys(params).forEach(key => url.searchParams.append(key, params[key]))

        resolve(decodeURIComponent(url.href))

    })

}
