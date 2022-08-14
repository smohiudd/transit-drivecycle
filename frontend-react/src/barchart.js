import React from 'react';
import * as d3 from "d3";

var margin = { top: 20, right: 20, bottom: 100, left: 100 }
    , width = 300
    , height = 200


export default class MyD3Component extends React.Component {
    constructor(props) {
        super(props);

        this.myReference = React.createRef();

    }

    componentDidMount() {

        this.svg = d3.select(this.myReference.current)
            .append("svg")
            .attr("width", width + margin.left + margin.right)
            .attr("height", height + margin.top + margin.bottom)
            .append("g")
            .attr("transform", "translate(" + margin.left + "," + margin.top + ")");

        this.update();
    }

    componentDidUpdate(){
        this.update();
    }

    update() {


        this.svg.selectAll("*").remove();

        const xScale = d3.scaleLinear().range([0, width]);
        const yScale = d3.scaleLinear().range([height, 0]);

        xScale.domain(d3.extent(this.props.data.data, d => d[0]));
        yScale.domain(d3.extent(this.props.data.data, d => d[1]));

        const yaxis = d3.axisLeft()
            .scale(yScale);

        const xaxis = d3.axisBottom()
            .scale(xScale)

        this.svg.append("g")
            .attr("class", "axis")
            .attr("transform", "translate(0," + height + ")")
            .call(xaxis);

        this.svg.append("g")
            .attr("class", "axis")
            .call(yaxis);


        this.svg.append("path")
            .datum(this.props.data.data)
            .attr("fill", "none")
            .attr("stroke", "#4096ff")
            .attr("stroke-width", 1.5)
            .attr("d", d3.line()
                .x(function (d) { return xScale(d[0]) })
                .y(function (d) { return yScale(d[1]) })
            )


        this.svg.append("text")
            .attr("text-anchor", "middle")  // this makes it easy to centre the text as the transform is applied to the anchor
            .attr("transform", "translate(" + (width / 2) + "," + (height + 40) + ")")  // centre below axis
            .text("Time (s)")
            .style("font", "12px sans-serif")

        // Add the text label for Y Axis
        this.svg.append("text")
            .attr("text-anchor", "middle")  // this makes it easy to centre the text as the transform is applied to the anchor
            .attr("transform", "translate(" + (0 - 50) + "," + (height / 2) + ")rotate(-90)")  // text is drawn off the screen top left, move down and out and rotate
            .text("Speed (m/s)")
            .style("font", "12px sans-serif")



        // svg.selectAll("rect")
        //     .data(this.props.data)
        //     .enter()
        //     .append("rect")
        //     .attr("x", (d, i) => i * 70)
        //     .attr("y", (d, i) => h - 10 * d)
        //     .attr("width", 65)
        //     .attr("height", (d, i) => d * 10)
        //     .attr("fill", "green")

    }

    render() {
        return (
            <div ref={this.myReference}>
            </div>
        );
    }
}