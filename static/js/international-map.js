(function () {
  "use strict";

  function noDataFill() {
    return document.documentElement.getAttribute("data-theme") === "nike"
      ? "#3a3a3a"
      : "#d4d4d4";
  }

  function clearNode(node) {
    while (node.firstChild) {
      node.removeChild(node.firstChild);
    }
  }

  function initMap() {
    var container = document.getElementById("intl-map");
    if (!container || typeof d3 === "undefined") {
      return;
    }
    if (container.getAttribute("data-map-init") === "1") {
      return;
    }
    container.setAttribute("data-map-init", "1");

    var dataEl = document.getElementById("intl-map-data");
    var legendEl = document.getElementById("intl-map-legend");
    if (!dataEl) {
      return;
    }

    try {
      var countries = JSON.parse(dataEl.textContent);
      var geoUrl = container.getAttribute("data-geo-url");
      var byIso2 = new Map(
        countries.map(function (country) {
          return [String(country.iso2 || "").toUpperCase(), country];
        })
      );

      function featureIso2(feature) {
        var props = feature.properties || {};
        var iso2 = props.ISO_A2_EH || props.ISO_A2;
        if (!iso2 || iso2 === "-99") {
          return null;
        }
        return String(iso2).toUpperCase();
      }

      function countryForFeature(feature) {
        var iso2 = featureIso2(feature);
        return iso2 ? byIso2.get(iso2) : null;
      }

      function lengthValue(country) {
        if (!country || (country.min == null && country.max == null)) {
          return null;
        }
        return country.max != null ? country.max : country.min;
      }

      function lengthLabel(country) {
        if (!country || (country.min == null && country.max == null)) {
          return "No length data";
        }
        if (country.min === country.max) {
          return country.min + " digits";
        }
        return country.min + "\u2013" + country.max + " digits";
      }

      function fillForFeature(feature, colorScale) {
        var country = countryForFeature(feature);
        var value = lengthValue(country);
        if (value == null) {
          return noDataFill();
        }
        return colorScale(value);
      }

      var lengths = countries
        .map(lengthValue)
        .filter(function (value) {
          return value != null;
        });

      if (!lengths.length) {
        container.textContent = "Length data is not available yet.";
        return;
      }

      var minLen = Math.min.apply(null, lengths);
      var maxLen = Math.max.apply(null, lengths);
      var width = container.clientWidth || 960;
      var height = Math.round(width * 0.52);

      clearNode(container);

      var svg = d3
        .select(container)
        .append("svg")
        .attr("viewBox", "0 0 " + width + " " + height)
        .attr("preserveAspectRatio", "xMidYMid meet")
        .attr("role", "img")
        .attr("aria-label", "World map colored by national phone number length");

      var mapLayer = svg.append("g").attr("class", "intl-map-layer");
      var projection = d3.geoNaturalEarth1();
      var path = d3.geoPath(projection);
      var color = d3
        .scaleLinear()
        .domain([minLen, maxLen])
        .range(["#8ec1e6", "#055a8e"])
        .clamp(true);

      var tooltip = d3
        .select(container)
        .append("div")
        .attr("class", "intl-map-tooltip")
        .style("opacity", 0);

      function showTooltip(event, label) {
        tooltip
          .style("opacity", 1)
          .html(label)
          .style("left", event.offsetX + 12 + "px")
          .style("top", event.offsetY + 12 + "px");
      }

      function hideTooltip() {
        tooltip.style("opacity", 0);
      }

      function drawLegend() {
        if (!legendEl) {
          return;
        }

        clearNode(legendEl);
        var legendWidth = Math.min(280, width - 24);
        var steps = 24;
        var legendSvg = d3
          .select(legendEl)
          .append("svg")
          .attr("viewBox", "0 0 " + legendWidth + " 42")
          .attr("aria-hidden", "true");

        var defs = legendSvg.append("defs");
        var gradient = defs
          .append("linearGradient")
          .attr("id", "intl-map-gradient")
          .attr("x1", "0%")
          .attr("x2", "100%");

        for (var i = 0; i <= steps; i += 1) {
          var value = minLen + ((maxLen - minLen) * i) / steps;
          gradient
            .append("stop")
            .attr("offset", (100 * i) / steps + "%")
            .attr("stop-color", color(value));
        }

        legendSvg
          .append("rect")
          .attr("x", 0)
          .attr("y", 0)
          .attr("width", legendWidth)
          .attr("height", 12)
          .attr("rx", 2)
          .style("fill", "url(#intl-map-gradient)");

        legendSvg
          .append("text")
          .attr("x", 0)
          .attr("y", 30)
          .attr("class", "intl-map-legend-label")
          .text(minLen + " digits");

        legendSvg
          .append("text")
          .attr("x", legendWidth)
          .attr("y", 30)
          .attr("text-anchor", "end")
          .attr("class", "intl-map-legend-label")
          .text(maxLen + " digits");
      }

      fetch(geoUrl)
        .then(function (response) {
          if (!response.ok) {
            throw new Error("geojson");
          }
          return response.json();
        })
        .then(function (geo) {
          var features = (geo.features || []).filter(function (feature) {
            return feature.geometry;
          });

          projection.fitExtent([[2, 2], [width - 2, height - 2]], {
            type: "FeatureCollection",
            features: features,
          });

          mapLayer
            .selectAll("path")
            .data(features)
            .join("path")
            .attr("class", function (feature) {
              var country = countryForFeature(feature);
              if (!country || lengthValue(country) == null) {
                return "intl-map-country intl-map-country--nodata";
              }
              return "intl-map-country intl-map-country--data";
            })
            .attr("d", path)
            .attr("fill", function (feature) {
              return fillForFeature(feature, color);
            })
            .attr("tabindex", function (feature) {
              return countryForFeature(feature) ? 0 : -1;
            })
            .on("mousemove", function (event, feature) {
              var country = countryForFeature(feature);
              var props = feature.properties || {};
              var name = props.NAME || props.ADMIN || featureIso2(feature);
              if (country) {
                showTooltip(
                  event,
                  "<strong>" + country.name + "</strong><br>" + lengthLabel(country)
                );
              } else {
                showTooltip(event, name + "<br>No data in this app");
              }
            })
            .on("mouseleave", hideTooltip)
            .on("click", function (event, feature) {
              var country = countryForFeature(feature);
              if (country && country.url) {
                window.location.href = country.url;
              }
            })
            .on("keydown", function (event, feature) {
              if (event.key !== "Enter" && event.key !== " ") {
                return;
              }
              event.preventDefault();
              var country = countryForFeature(feature);
              if (country && country.url) {
                window.location.href = country.url;
              }
            });

          var zoom = d3
            .zoom()
            .scaleExtent([1, 8])
            .clickDistance(5)
            .on("zoom", function (event) {
              mapLayer.attr("transform", event.transform);
            });

          svg.call(zoom);

          function zoomBy(factor) {
            svg
              .transition()
              .duration(200)
              .call(zoom.scaleBy, factor, [width / 2, height / 2]);
          }

          var controls = d3
            .select(container)
            .append("div")
            .attr("class", "intl-map-controls");

          controls
            .append("button")
            .attr("type", "button")
            .attr("class", "intl-map-control intl-map-reset")
            .attr("aria-label", "Reset map zoom")
            .text("Reset view")
            .on("click", function () {
              svg.transition().duration(250).call(zoom.transform, d3.zoomIdentity);
            });

          controls
            .append("button")
            .attr("type", "button")
            .attr("class", "intl-map-control intl-map-zoom")
            .attr("aria-label", "Zoom in")
            .text("+")
            .on("click", function () {
              zoomBy(1.35);
            });

          controls
            .append("button")
            .attr("type", "button")
            .attr("class", "intl-map-control intl-map-zoom")
            .attr("aria-label", "Zoom out")
            .text("\u2212")
            .on("click", function () {
              zoomBy(1 / 1.35);
            });

          drawLegend();
        })
        .catch(function () {
          container.removeAttribute("data-map-init");
          container.textContent = "Unable to load the map data.";
        });
    } catch (error) {
      container.removeAttribute("data-map-init");
      container.textContent = "Unable to draw the map.";
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initMap);
  } else {
    initMap();
  }
})();
