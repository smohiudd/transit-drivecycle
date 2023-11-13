import React, { useRef, useEffect, useState } from "react";
import maplibregl from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";
import "./css/map.css";
import { lineString, bbox, point, featureCollection } from "@turf/turf";

export default function Map(props) {
    const mapContainer = useRef(null);
    const map = useRef(null);
    const [lng] = useState(-114.07769);
    const [lat] = useState(51.0536);
    const [zoom] = useState(10);

    useEffect(() => {
      if (map.current) return; // stops map from intializing more than once
  
      map.current = new maplibregl.Map({
        container: mapContainer.current,
        style: "https://basemaps.cartocdn.com/gl/positron-gl-style/style.json",
        center: [lng, lat],
        zoom: zoom,
      });

      map.current.on("load", function () {
        map.current.addSource("route", {
          type: "geojson",
          data: null,
        });
        map.current.addLayer({
          id: "route",
          type: "line",
          source: "route",
          layout: {
            "line-join": "round",
            "line-cap": "round",
          },
          paint: {
            "line-color": "blue",
            "line-width": 3,
          },
        });

        map.current.addSource("route_trace", {
          type: "geojson",
          data: null,
        });
        map.current.addLayer({
          id: "route_trace",
          type: "line",
          source: "route_trace",
          layout: {
            "line-join": "round",
            "line-cap": "round",
          },
          paint: {
            "line-color": "red",
            "line-width": 7,
            "line-opacity":0.5
          },
        });

      })
  
    }, [lng, lat, zoom]);

    useEffect(() => {
      if (!props.geom || props.geom.length == 0) return;
      let coords = props.geom.map((item) => [
        item.shape_pt_lon,
        item.shape_pt_lat,
      ]);
      let line = lineString(coords);
      map.current.getSource("route").setData(line);
      let box = bbox(line);
      map.current.fitBounds(box, { padding: 30 });

    }, [props.geom]);


    useEffect(() => {
      if (props.trace.length == 0) return;

      let coords = props.trace.map((item) => [
        item[1],
        item[0],
      ]);
      let line = lineString(coords);
      map.current.getSource("route_trace").setData(line);
      let box = bbox(line);
      map.current.fitBounds(box, { padding: 30 });

    }, [props.trace]);
    
    return (
      <div>
        <div ref={mapContainer} className="map" />
      </div>
    );
  }