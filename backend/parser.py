import os
import gpxpy
import gpxpy.gpx
import math
import requests
import time
import json
import geopy.distance
from typing import Dict, Any, Tuple

NOMINATIM_URL = "https://nominatim.openstreetmap.org/reverse"
OPENTOPO_URL = "https://api.opentopodata.org/v1/srtm30m"

USER_AGENT = "HikingAppTracker/1.2.0 (contact: github.com/marti-gravity)" # Nominatim requires a valid user agent

def calculate_difficulty(distance_km: float, elevation_m: float) -> Tuple[float, str]:
    """Calculate difficulty using Shenandoah rating system:
    Rating = sqrt(Elevation_gain_feet * 2 * Distance_miles)
    """
    if elevation_m < 0:
        elevation_m = 0
    distance_miles = distance_km / 1.60934
    elevation_feet = elevation_m * 3.28084
    
    score = math.sqrt(elevation_feet * 2 * distance_miles) if distance_miles > 0 and elevation_feet > 0 else 0.0
    
    if score < 50:
        return score, "Easy"
    elif score < 100:
        return score, "Moderate"
    elif score < 150:
        return score, "Moderately Strenuous"
    elif score < 200:
        return score, "Strenuous"
    else:
        return score, "Very Strenuous"

def get_location_info(lat: float, lon: float) -> Tuple[str, str]:
    """Retrieve country and nearest town from Nominatim."""
    params = {
        'lat': lat,
        'lon': lon,
        'format': 'json',
        'zoom': 10 # Town/City level
    }
    headers = {'User-Agent': USER_AGENT}
    try:
        response = requests.get(NOMINATIM_URL, params=params, headers=headers)
        response.raise_for_status()
        data = response.json()
        address = data.get('address', {})
        
        country = address.get('country', "Unknown")
        town = address.get('town') or address.get('village') or address.get('city') or address.get('municipality') or "Unknown"
        
        # Obey Nominatim 1 request/sec policy
        time.sleep(1.1)
        
        return country, town
    except Exception as e:
        print(f"Error calling Nominatim: {e}")
        return "Unknown", "Unknown"

def get_elevation_gain_from_api(polyline: list) -> float:
    """Fetch elevation data from OpenTopoData if GPX file lacks it."""
    if not polyline:
        return 0.0
        
    sampled = []
    if len(polyline) <= 100:
        sampled = polyline
    else:
        step = len(polyline) / 100.0
        for i in range(100):
            idx = int(i * step)
            if idx < len(polyline):
                sampled.append(polyline[idx])
                
    locations = "|".join([f"{pt[0]},{pt[1]}" for pt in sampled])
    
    try:
        response = requests.get(OPENTOPO_URL, params={'locations': locations})
        response.raise_for_status()
        data = response.json()
        results = data.get('results', [])
        
        gain = 0.0
        prev_ele = None
        for res in results:
            ele = res.get('elevation')
            if ele is not None:
                if prev_ele is not None and ele > prev_ele:
                    gain += (ele - prev_ele)
                prev_ele = ele
        return gain
    except Exception as e:
        print(f"Elevation API error: {e}")
        return 0.0

def extract_gpx_data(file_path: str) -> Dict[str, Any]:
    with open(file_path, 'r', encoding='utf-8') as gpx_file:
        try:
            gpx = gpxpy.parse(gpx_file)
        except Exception as e:
            return {"error": f"Failed to parse GPX: {e}"}

    if not gpx.tracks:
        return {"error": "No tracks found in GPX"}

    track = gpx.tracks[0]
    
    # Calculate length
    length_3d = track.length_3d()
    length_2d = track.length_2d()
    length_m = length_3d if length_3d > 0 else length_2d
    length_km = length_m / 1000.0
    
    # Start and end points & polyline
    start_point, end_point = None, None
    polyline = []
    for segment in track.segments:
        if segment.points:
            if not start_point:
                start_point = segment.points[0]
            end_point = segment.points[-1]
            for pt in segment.points:
                polyline.append([pt.latitude, pt.longitude])

    if not start_point or not end_point:
        return {"error": "Track has no valid points"}

    start_lat, start_lon = start_point.latitude, start_point.longitude
    end_lat, end_lon = end_point.latitude, end_point.longitude

    # Calculate if loop
    # Using geopy to safely calculate the haversine distance
    dist_start_end = geopy.distance.geodesic((start_lat, start_lon), (end_lat, end_lon)).meters
    is_loop = dist_start_end < 200.0 and length_km > 1.0  # Starts & ends within 200m

    # Calculate Elevation Gain
    # gpxpy has get_uphill_downhill() -> (uphill, downhill)
    uphill, downhill = track.get_uphill_downhill()
    elevation_gain_m = uphill if uphill is not None else 0.0
    
    if elevation_gain_m == 0.0:
        elevation_gain_m = get_elevation_gain_from_api(polyline)
    
    # Difficulty
    difficulty_score, difficulty_category = calculate_difficulty(length_km, elevation_gain_m)

    # Location info
    country, nearest_town = get_location_info(start_lat, start_lon)

    return {
        "file_path": file_path,
        "name": track.name or os.basename(file_path),
        "country": country,
        "nearest_town": nearest_town,
        "length_km": length_km,
        "is_loop": is_loop,
        "start_lat": start_lat,
        "start_lon": start_lon,
        "end_lat": end_lat,
        "end_lon": end_lon,
        "elevation_gain_m": elevation_gain_m,
        "difficulty_score": difficulty_score,
        "difficulty_category": difficulty_category,
        "polyline": json.dumps(polyline)
    }
