import csv
import html
import webbrowser
from pathlib import Path

import folium
import requests


def load_stops(filename):
    stops = []

    with open(filename, newline="", encoding="utf-8-sig") as file:
        reader = csv.DictReader(file)

        for row in reader:
            stops.append({
                "name": row["name"],
                "lat": float(row["lat"]),
                "lon": float(row["lon"]),
            })

    return stops


def get_road_matrices(stops):
    coordinates = ";".join(
        f"{stop['lon']},{stop['lat']}"
        for stop in stops
    )

    url = (
        "https://router.project-osrm.org"
        f"/table/v1/driving/{coordinates}"
    )

    response = requests.get(
        url,
        params={"annotations": "distance,duration"},
        timeout=60,
    )
    response.raise_for_status()

    data = response.json()

    if data.get("code") != "Ok":
        raise RuntimeError(
            data.get("message", "OSRM could not calculate distances.")
        )

    distances = data["distances"]
    durations = data["durations"]

    for i in range(len(stops)):
        for j in range(len(stops)):
            if distances[i][j] is None or durations[i][j] is None:
                raise ValueError(
                    "No driving route found from "
                    f"{stops[i]['name']} to {stops[j]['name']}."
                )

    return distances, durations


def print_distance_matrix(stops, distances):
    print("\nRoad-distance matrix (miles)")
    print("Rows = starting locations; columns = destinations.\n")

    print(f"{'From / To':<16}", end="")

    for index in range(len(stops)):
        print(f"{index:>9}", end="")

    print()

    for index, row in enumerate(distances):
        print(f"{index:<16}", end="")

        for meters in row:
            print(f"{meters / 1609.344:>9.2f}", end="")

        print()

    print("\nLocation key:")

    for index, stop in enumerate(stops):
        print(f"{index}: {stop['name']}")

def nearest_neighbor(distances, start=0):
    route = [start]
    unvisited = set(range(len(distances)))
    unvisited.remove(start)

    while unvisited:
        current = route[-1]

        next_stop = min(
            unvisited,
            key=lambda stop: (distances[current][stop], stop),
        )

        route.append(next_stop)
        unvisited.remove(next_stop)

    route.append(start)
    return route


def print_route(stops, route, distances, durations):
    total_distance = 0
    total_duration = 0

    print("\nDelivery route:")
    print(" -> ".join(stops[index]["name"] for index in route))

    print("\nIndividual legs:")

    for start, end in zip(route, route[1:]):
        meters = distances[start][end]
        seconds = durations[start][end]

        total_distance += meters
        total_duration += seconds

        print(
            f"{stops[start]['name']} -> {stops[end]['name']}: "
            f"{meters / 1609.344:.2f} miles, "
            f"{seconds / 60:.1f} minutes"
        )

    print(f"\nTotal road distance: {total_distance / 1609.344:.2f} miles")
    print(f"Estimated driving time: {total_duration / 60:.1f} minutes")
def route_distance(route, distances):
    return sum(
        distances[start][end]
        for start, end in zip(route, route[1:])
    )


def two_opt(route, distances):
    best_route = route[:]
    best_distance = route_distance(best_route, distances)

    while True:
        improved = False

        # Keep the starting and ending depot fixed.
        for i in range(1, len(best_route) - 2):
            for j in range(i + 1, len(best_route) - 1):
                candidate = (
                    best_route[:i]
                    + best_route[i:j + 1][::-1]
                    + best_route[j + 1:]
                )

                candidate_distance = route_distance(
                    candidate, distances
                )

                if candidate_distance < best_distance - 1e-9:
                    best_route = candidate
                    best_distance = candidate_distance
                    improved = True
                    break

            if improved:
                break

        if not improved:
            return best_route
def create_route_map(stops, route):
    coordinates = ";".join(
        f"{stops[index]['lon']},{stops[index]['lat']}"
        for index in route
    )

    url = (
        "https://router.project-osrm.org"
        f"/route/v1/driving/{coordinates}"
    )

    print("\nRequesting road geometry from OSRM...")

    response = requests.get(
        url,
        params={
            "overview": "full",
            "geometries": "geojson",
            "steps": "false",
            "alternatives": "false",
        },
        timeout=60,
    )
    response.raise_for_status()

    data = response.json()

    if data.get("code") != "Ok":
        raise RuntimeError(
            data.get("message", "OSRM could not create the map route.")
        )

    road_route = data["routes"][0]
    geometry = road_route["geometry"]

    depot = stops[route[0]]

    route_map = folium.Map(
        location=[depot["lat"], depot["lon"]],
        zoom_start=13,
        tiles="OpenStreetMap",
    )

    # GeoJSON already uses the coordinate order Folium.GeoJson expects.
    road_layer = folium.GeoJson(
        {
            "type": "Feature",
            "geometry": geometry,
            "properties": {},
        },
        name="Optimized driving route",
        style_function=lambda feature: {
            "color": "#2563eb",
            "weight": 5,
            "opacity": 0.85,
        },
        tooltip="Optimized driving route",
    ).add_to(route_map)

    folium.Marker(
        location=[depot["lat"], depot["lon"]],
        tooltip="Depot: start and finish",
        popup=folium.Popup(
            f"<b>Start / Finish</b><br>{html.escape(depot['name'])}",
            max_width=250,
        ),
        icon=folium.Icon(color="green", icon="home"),
    ).add_to(route_map)

    # Skip the depot at both ends when numbering deliveries.
    for number, stop_index in enumerate(route[1:-1], start=1):
        stop = stops[stop_index]

        folium.Marker(
            location=[stop["lat"], stop["lon"]],
            tooltip=f"{number}. {stop['name']}",
            popup=folium.Popup(
                f"<b>Delivery {number}</b><br>"
                f"{html.escape(stop['name'])}",
                max_width=250,
            ),
            icon=folium.DivIcon(
                icon_size=(30, 30),
                icon_anchor=(15, 15),
                html=(
                    '<div style="'
                    'background:#2563eb; color:white;'
                    'border:2px solid white; border-radius:50%;'
                    'width:28px; height:28px;'
                    'text-align:center; line-height:28px;'
                    'font-size:14px; font-weight:bold;'
                    'box-shadow:0 1px 5px rgba(0,0,0,0.5);'
                    f'">{number}</div>'
                ),
            ),
        ).add_to(route_map)

    route_map.fit_bounds(road_layer.get_bounds(), padding=(30, 30))

    output_path = Path(__file__).parent / "route_map.html"
    route_map.save(str(output_path))

    print(f"Map saved: {output_path}")
    print(
        "Mapped route: "
        f"{road_route['distance'] / 1609.344:.2f} miles, "
        f"{road_route['duration'] / 60:.1f} minutes"
    )

    webbrowser.open("http://127.0.0.1:8000/route_map.html")        
def main():
    csv_path = Path(__file__).parent / "stops.csv"
    stops = load_stops(csv_path)

    if len(stops) < 2:
        raise ValueError("Include a depot and at least one delivery stop.")

    print(f"Loaded {len(stops)} locations.")
    print("Requesting road distances from OSRM...")

    distances, durations = get_road_matrices(stops)

    print_distance_matrix(stops, distances)

    baseline_route = list(range(len(stops))) + [0]

    initial_route = nearest_neighbor(distances, start=0)
    optimized_route = two_opt(initial_route, distances)

    print("\n--- ORIGINAL CSV ORDER ---")
    print_route(stops, baseline_route, distances, durations)

    print("\n--- NEAREST NEIGHBOR ---")
    print_route(stops, initial_route, distances, durations)

    print("\n--- AFTER 2-OPT ---")
    print_route(stops, optimized_route, distances, durations)

    baseline_distance = route_distance(baseline_route, distances)
    initial_distance = route_distance(initial_route, distances)
    optimized_distance = route_distance(optimized_route, distances)

    saved_distance = baseline_distance - optimized_distance

    saved_percent = (
        100 * saved_distance / baseline_distance
        if baseline_distance > 0
        else 0
    )

    print("\n--- DISTANCE COMPARISON ---")
    print(f"Original CSV order: {baseline_distance / 1609.344:.2f} miles")
    print(f"Nearest neighbor:   {initial_distance / 1609.344:.2f} miles")
    print(f"After 2-opt:        {optimized_distance / 1609.344:.2f} miles")

    print("\nCompared with original CSV order:")
    print(f"Distance saved: {saved_distance / 1609.344:.2f} miles")
    print(f"Reduction: {saved_percent:.1f}%")
    
    create_route_map(stops, optimized_route)

if __name__ == "__main__":
    try:
        main()
    except (requests.RequestException, ValueError, RuntimeError) as error:
        print(f"Error: {error}")