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
    var container = document.getElementById("canada-provinces-map");
    if (!container || typeof d3 === "undefined") {
      return;
    }
    if (container.getAttribute("data-map-init") === "1") {
      resetMapUi(container);
      return;
    }
    container.setAttribute("data-map-init", "1");

    var dataEl = document.getElementById("canada-provinces-map-data");
    if (!dataEl) {
      return;
    }

    try {
      var regions = JSON.parse(dataEl.textContent);
      var geoUrl = container.getAttribute("data-geo-url");
      var byRegion = new Map(
        regions.map(function (region) {
          return [String(region.region || region.name || ""), region];
        })
      );

      function featureRegionKey(feature) {
        var props = feature.properties || {};
        return props.region || props.name || null;
      }

      function regionForFeature(feature) {
        var key = featureRegionKey(feature);
        return key ? byRegion.get(key) : null;
      }

      function groupKeyForFeature(feature) {
        var region = regionForFeature(feature);
        return region ? String(region.region || region.name || "") : null;
      }

      var regionsLayer;

      function setGroupHover(groupKey) {
        if (!regionsLayer) {
          return;
        }
        regionsLayer
          .selectAll("path.canada-map-region")
          .classed("intl-map-country--group-hover", function (feature) {
            return groupKey && groupKeyForFeature(feature) === groupKey;
          });
      }

      function featureLabel(feature) {
        var props = feature.properties || {};
        return props.code || "";
      }

      var width = container.clientWidth || 960;
      var height = Math.round(width * 0.72);

      clearNode(container);

      var svg = d3
        .select(container)
        .append("svg")
        .attr("viewBox", "0 0 " + width + " " + height)
        .attr("preserveAspectRatio", "xMidYMid meet")
        .attr("role", "img")
        .attr("aria-label", "Canada map with clickable provinces and territories");

      var mapLayer = svg.append("g").attr("class", "intl-map-layer");
      var projection = d3
        .geoConicConformal()
        .parallels([49, 77])
        .rotate([96, 0])
        .center([0, 62]);
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
        tooltip.style("opacity", 0);
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

          regionsLayer = mapLayer.append("g").attr("class", "canada-map-regions");
          var labelsLayer = mapLayer.append("g").attr("class", "canada-map-labels");

          regionsLayer
            .selectAll("path")
            .data(features)
            .join("path")
            .attr("class", "intl-map-country intl-map-country--data canada-map-region")
            .attr("d", path)
            .attr("fill", regionFill())
            .attr("tabindex", function (feature) {
              return regionForFeature(feature) ? 0 : -1;
            })
            .on("mouseover", function (event, feature) {
              var region = regionForFeature(feature);
              if (region) {
                setGroupHover(groupKeyForFeature(feature));
                showTooltip(
                  event,
                  "<strong>" + region.code + "</strong> " + region.name + "<br>Area code maps"
                );
              } else {
                setGroupHover(null);
                showTooltip(event, "No data for this region");
              }
            })
            .on("mousemove", function (event, feature) {
              var region = regionForFeature(feature);
              if (region) {
                showTooltip(
                  event,
                  "<strong>" + region.code + "</strong> " + region.name + "<br>Area code maps"
                );
              }
            })
            .on("mouseout", function (event) {
              var related = event.relatedTarget;
              if (
                related &&
                related.closest &&
                related.closest("#canada-provinces-map path.canada-map-region")
              ) {
                return;
              }
              setGroupHover(null);
              hideTooltip();
            })
            .on("focus", function (event, feature) {
              if (regionForFeature(feature)) {
                setGroupHover(groupKeyForFeature(feature));
              }
            })
            .on("blur", function () {
              window.requestAnimationFrame(function () {
                var active = document.activeElement;
                var activeKey = null;
                if (active && active.classList.contains("canada-map-region")) {
                  var datum = d3.select(active).datum();
                  if (datum) {
                    activeKey = groupKeyForFeature(datum);
                  }
                }
                setGroupHover(activeKey);
              });
            })
            .on("click", function (event, feature) {
              var region = regionForFeature(feature);
              event.currentTarget.blur();
              setGroupHover(null);
              hideTooltip();
              if (region && region.url) {
                window.location.href = region.url;
              }
            })
            .on("keydown", function (event, feature) {
              if (event.key !== "Enter" && event.key !== " ") {
                return;
              }
              event.preventDefault();
              var region = regionForFeature(feature);
              if (region && region.url) {
                window.location.href = region.url;
              }
            });

          var labelFeatures = [];
          var labelGroupsSeen = new Set();
          features
            .filter(function (feature) {
              return regionForFeature(feature);
            })
            .forEach(function (feature) {
              feature._mapArea = path.area(feature);
            });
          features
            .filter(function (feature) {
              return regionForFeature(feature);
            })
            .sort(function (a, b) {
              return (b._mapArea || 0) - (a._mapArea || 0);
            })
            .forEach(function (feature) {
              var groupKey = groupKeyForFeature(feature);
              if (labelGroupsSeen.has(groupKey)) {
                return;
              }
              labelGroupsSeen.add(groupKey);
              labelFeatures.push(feature);
            });

          labelsLayer
            .selectAll("text")
            .data(labelFeatures)
            .join("text")
            .attr("class", "us-map-label")
            .attr("text-anchor", "middle")
            .attr("dy", "0.35em")
            .attr("transform", function (feature) {
              var centroid = path.centroid(feature);
              return "translate(" + centroid[0] + "," + centroid[1] + ")";
            })
            .style("font-size", function (feature) {
              return labelFontSize(feature._mapArea || 0) + "px";
            })
            .text(featureLabel);

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
    resetMapUi(document.getElementById("canada-provinces-map"));
  }

  window.addEventListener("pageshow", onPageShow);

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initMap);
  } else {
    initMap();
  }
})();
