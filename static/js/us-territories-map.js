(function () {
  "use strict";

  function regionFill() {
    return document.documentElement.getAttribute("data-theme") === "nike"
      ? "#3a3a3a"
      : "#8ec1e6";
  }

  function clearNode(node) {
    while (node.firstChild) {
      node.removeChild(node.firstChild);
    }
  }

  function resetMapUi(container) {
    if (!container) {
      return;
    }
    var tooltip = container.querySelector(".intl-map-tooltip");
    if (tooltip) {
      tooltip.style.opacity = "0";
    }
    var active = document.activeElement;
    if (active && container.contains(active)) {
      active.blur();
    }
  }

  function initMap() {
    var container = document.getElementById("us-territories-map");
    if (!container || typeof d3 === "undefined") {
      return;
    }
    if (container.getAttribute("data-map-init") === "1") {
      resetMapUi(container);
      return;
    }
    container.setAttribute("data-map-init", "1");

    var dataEl = document.getElementById("us-territories-map-data");
    if (!dataEl) {
      return;
    }

    try {
      var territories = JSON.parse(dataEl.textContent);
      var geoUrl = container.getAttribute("data-geo-url");
      var byCode = new Map(
        territories.map(function (territory) {
          return [String(territory.code || "").toUpperCase(), territory];
        })
      );

      function featureCode(feature) {
        var props = feature.properties || {};
        var code = props.code;
        if (!code) {
          return null;
        }
        return String(code).toUpperCase();
      }

      function territoryForFeature(feature) {
        var code = featureCode(feature);
        return code ? byCode.get(code) : null;
      }

      var width = container.clientWidth || 960;
      var height = Math.round(width * 0.58);

      clearNode(container);

      var svg = d3
        .select(container)
        .append("svg")
        .attr("viewBox", "0 0 " + width + " " + height)
        .attr("preserveAspectRatio", "xMidYMid meet")
        .attr("role", "img")
        .attr("aria-label", "US territories map with clickable regions");

      var mapLayer = svg.append("g").attr("class", "intl-map-layer");
      var projection = d3.geoIdentity();
      var path = d3.geoPath(projection);

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
        tooltip.style.opacity = 0;
      }

      function labelFontSize(area) {
        return Math.min(11, Math.max(5.5, Math.sqrt(area) / 5));
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

          projection.fitSize([width - 4, height - 4], {
            type: "FeatureCollection",
            features: features,
          });

          var territoriesLayer = mapLayer.append("g").attr("class", "us-map-territories");
          var labelsLayer = mapLayer.append("g").attr("class", "us-map-labels");

          territoriesLayer
            .selectAll("path")
            .data(features)
            .join("path")
            .attr("class", "intl-map-country intl-map-country--data us-map-territory")
            .attr("d", path)
            .attr("fill", regionFill())
            .attr("tabindex", function (feature) {
              return territoryForFeature(feature) ? 0 : -1;
            })
            .on("mousemove", function (event, feature) {
              var territory = territoryForFeature(feature);
              if (territory) {
                showTooltip(
                  event,
                  "<strong>" + territory.code + "</strong> " + territory.name + "<br>Area code maps"
                );
              } else {
                showTooltip(event, "No data for this region");
              }
            })
            .on("mouseleave", hideTooltip)
            .on("click", function (event, feature) {
              var territory = territoryForFeature(feature);
              event.currentTarget.blur();
              hideTooltip();
              if (territory && territory.url) {
                window.location.href = territory.url;
              }
            })
            .on("keydown", function (event, feature) {
              if (event.key !== "Enter" && event.key !== " ") {
                return;
              }
              event.preventDefault();
              var territory = territoryForFeature(feature);
              if (territory && territory.url) {
                window.location.href = territory.url;
              }
            });

          labelsLayer
            .selectAll("text")
            .data(
              features.filter(function (feature) {
                return territoryForFeature(feature);
              })
            )
            .join("text")
            .attr("class", "us-map-label")
            .attr("text-anchor", "middle")
            .attr("dy", "0.35em")
            .each(function (feature) {
              feature._mapArea = path.area(feature);
            })
            .attr("transform", function (feature) {
              var centroid = path.centroid(feature);
              return "translate(" + centroid[0] + "," + centroid[1] + ")";
            })
            .style("font-size", function (feature) {
              return labelFontSize(feature._mapArea || 0) + "px";
            })
            .text(featureCode);

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

  function onPageShow() {
    resetMapUi(document.getElementById("us-territories-map"));
  }

  window.addEventListener("pageshow", onPageShow);

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initMap);
  } else {
    initMap();
  }
})();
