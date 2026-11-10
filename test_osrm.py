import requests

url = (
    "https://router.project-osrm.org/route/v1/driving/"
    "-116.2023,43.6150;-116.2150,43.6000"
)

try:
    print("Requesting a driving route from OSRM...")

    response = requests.get(
        url,
        params={"overview": "false"},
        timeout=30,
    )
    response.raise_for_status()

    data = response.json()

    if data.get("code") != "Ok":
        raise RuntimeError(
            data.get("message", "OSRM could not calculate a route.")
        )

    route = data["routes"][0]

    miles = route["distance"] / 1609.344
    minutes = route["duration"] / 60

    print("OSRM connection successful!")
    print(f"Road distance: {miles:.2f} miles")
    print(f"Estimated driving time: {minutes:.1f} minutes")

except (requests.RequestException, ValueError, RuntimeError) as error:
    print(f"Could not complete the request: {error}")