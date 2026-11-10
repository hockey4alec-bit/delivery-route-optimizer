# Delivery Route Optimizer

A Python project that plans a single-vehicle delivery route using
road-network distances from OSRM.

The program compares the original CSV order, a nearest-neighbor route,
and a route improved using 2-opt segment reversals. It displays the
resulting route on an interactive road-following map.

## Features

- Load delivery coordinates from CSV
- Request road-distance and estimated-duration matrices from OSRM
- Build a nearest-neighbor route
- Improve the route with 2-opt
- Support asymmetric driving distances
- Compare route distances
- Display numbered stops and road geometry with Folium

## Tools

Python, Requests, OSRM, Folium, OpenStreetMap, and unittest.

## Input format

Create a file named `stops.csv` in the project folder:

```csv
name,lat,lon
Boise Depot,43.6150,-116.2023
Stop A,43.6000,-116.2150
Stop B,43.6200,-116.2100
```

The first location is the depot. Routes start and finish there.
The included coordinates are sample data, not verified customer addresses.

## Windows setup

Open a terminal in the project folder:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## Run the program

Start the local map server:

```powershell
.\.venv\Scripts\python.exe -m http.server 8000 --bind 127.0.0.1
```

Leave that terminal running. In a second terminal:

```powershell
.\.venv\Scripts\python.exe delivery_route_optimizer.py
```

View the map at:

http://127.0.0.1:8000/route_map.html

An internet connection is required for OSRM requests and map resources.

## Run automated tests

```powershell
.\.venv\Scripts\python.exe -m unittest -v test_optimizer
```
The seven automated tests check:

- Direction-aware route-distance calculations
- Expected nearest-neighbor ordering
- Visiting each location exactly once before returning to the depot
- Route validity after 2-opt
- 2-opt does not increase the starting route’s distance
- Improvement on a known test example
- A depot with one delivery stop

All seven tests passed locally on Windows.
Tests use fixed matrices and do not call the live OSRM service.
The optimizer tests use fixed distance matrices and do not call OSRM.

## Example result

For one run using the included five-location sample:

| Method | Distance | Estimated driving time |
|---|---:|---:|
| Nearest neighbor | 7.37 miles | 22.2 minutes |
| Nearest neighbor + 2-opt | 7.27 miles | 21.7 minutes |

The program reported a 1.3% distance reduction relative to nearest
neighbor. Results are specific to this sample and routing data.

## Limitations

- Single vehicle, with a required return to the depot
- No vehicle capacities, delivery time windows, or service times
- Optimizes distance, not estimated driving time
- OSRM distances follow its fastest routes, not necessarily
  shortest-distance road paths
- Heuristics do not guarantee a globally shortest route
- The result is not guaranteed to improve on the original CSV order
- Uses the public OSRM demo service for development
- Requires latitude and longitude; address geocoding is not included

## Future improvements

- Cache OSRM matrices
- Validate CSV headers and coordinate ranges
- Allow selecting an input CSV from the command line
- Offer distance or duration as the optimization objective
- Compare against exact solutions on small test cases