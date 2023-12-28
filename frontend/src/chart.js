import React from 'react';
import * as d3 from "d3";

var margin = { top: 30, right: 20, bottom: 40, left: 60 }
    , width = 320
    , height = 60


export default class MyD3Component extends React.Component {
    constructor(props) {
        super(props);

        this.myReference = React.createRef();

    }

    componentDidMount() {

        this.svg = d3.select(this.myReference.current)
            .append("svg")
            .attr("preserveAspectRatio", "xMinYMin meet")
            .attr(`viewBox`, `0 0 ${width + margin.left + margin.right} ${height + margin.top + margin.bottom}`)
            .classed("svg-content", true)
            .append("g")
            .attr("transform", "translate(" + margin.left + "," + margin.top + ")");

        this.update();
    }

    componentDidUpdate() {
        this.update();
    }

    update() {


        let x = this.props.x
        let y = this.props.y

        this.svg.selectAll("*").remove();

        const xScale = d3.scaleLinear().range([0, width]);
        const yScale = d3.scaleLinear().range([height, 0]);

        xScale.domain(d3.extent(this.props.data, d => d[x]));
        yScale.domain(d3.extent(this.props.data, d => d[y]));

        const yaxis = d3.axisLeft()
            .scale(yScale)
            .ticks(3);

        const xaxis = d3.axisBottom()
            .scale(xScale)
            .ticks(5);

        this.svg.append("g")
            .attr("class", "axis")
            .attr("transform", "translate(0," + height + ")")
            .call(xaxis);

        this.svg.append("g")
            .attr("class", "axis")
            .call(yaxis);

        this.svg.append("path")
            .datum(this.props.data)
            .attr("fill", "none")
            .attr("stroke", "#4096ff")
            .attr("stroke-width", 1.5)
            .attr("d", d3.line()
                .x(function (d) { return xScale(d[x]) })
                .y(function (d) { return yScale(d[y]) })
            )


        this.svg.append("text")
            .attr("text-anchor", "middle")  // this makes it easy to centre the text as the transform is applied to the anchor
            .attr("transform", "translate(" + (width / 2) + "," + (height + 37) + ")")  // centre below axis
            .text(this.props.x_label)
            .style("font", "12px sans-serif")

        // Add the text label for Y Axis
        this.svg.append("text")
            .attr("text-anchor", "middle")  // this makes it easy to centre the text as the transform is applied to the anchor
            .attr("transform", "translate(" + (0 - 40) + "," + (height / 2) + ")rotate(-90)")  // text is drawn off the screen top left, move down and out and rotate
            .text(this.props.y_label)
            .style("font", "12px sans-serif")


    }

    render() {
        return (
            <div ref={this.myReference}>
            </div>
        );
    }
}