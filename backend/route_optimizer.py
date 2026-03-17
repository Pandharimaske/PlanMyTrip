"""
Route optimization using clustering and TSP for efficient day-wise scheduling.

Components:
1. Geographic clustering - groups nearby places using k-means++
2. Travel time matrix - calculates pairwise travel distances
3. TSP solver - finds efficient routes within each day's cluster
4. Day allocation - distributes activities across days optimally
"""

import math
from typing import List, Dict, Tuple, Set
from itertools import permutations
import random

def haversine_distance(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """
    Calculate great-circle distance between two points (km).
    """
    R = 6371  # Earth radius in km
    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)
    a = (math.sin(dlat/2)**2 + 
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * 
         math.sin(dlng/2)**2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c


def build_distance_matrix(places: List[Dict]) -> List[List[float]]:
    """
    Build pairwise distance matrix between all places.
    
    Args:
        places: List of place dicts with lat/lng
    
    Returns:
        Distance matrix (n x n)
    """
    n = len(places)
    matrix = [[0.0] * n for _ in range(n)]
    
    for i in range(n):
        for j in range(i+1, n):
            dist = haversine_distance(
                places[i]["lat"], places[i]["lng"],
                places[j]["lat"], places[j]["lng"]
            )
            matrix[i][j] = dist
            matrix[j][i] = dist
    
    return matrix


def kmeans_clustering(
    places: List[Dict],
    k: int,
    max_iterations: int = 50,
    random_seed: int = 42
) -> Tuple[List[List[Dict]], List[Tuple[float, float]]]:
    """
    Cluster places using k-means++ for geographic grouping.
    
    Args:
        places: List of place dicts
        k: Number of clusters (ideally num_days)
        max_iterations: Max k-means iterations
        random_seed: For reproducibility
    
    Returns:
        (clusters, centroids) - list of place clusters and their centers
    """
    if not places or k <= 0:
        return [places], [(0, 0)]
    
    random.seed(random_seed)
    k = min(k, len(places))
    
    # k-means++ initialization: pick first center randomly, then farthest points
    centers = []
    place_indices = list(range(len(places)))
    
    # Pick first center
    first_idx = random.choice(place_indices)
    centers.append((places[first_idx]["lat"], places[first_idx]["lng"]))
    remaining = [i for i in place_indices if i != first_idx]
    
    # Pick k-1 more centers, each farthest from existing centers
    for _ in range(k - 1):
        if not remaining:
            break
        
        max_min_dist = -1
        farthest_idx = remaining[0]
        
        for idx in remaining:
            min_dist = min(
                haversine_distance(
                    places[idx]["lat"], places[idx]["lng"],
                    center[0], center[1]
                )
                for center in centers
            )
            if min_dist > max_min_dist:
                max_min_dist = min_dist
                farthest_idx = idx
        
        centers.append((places[farthest_idx]["lat"], places[farthest_idx]["lng"]))
        remaining.remove(farthest_idx)
    
    # K-means iterations
    for iteration in range(max_iterations):
        # Assign points to nearest center
        clusters = [[] for _ in range(len(centers))]
        for i, place in enumerate(places):
            distances = [
                haversine_distance(place["lat"], place["lng"], c[0], c[1])
                for c in centers
            ]
            nearest_cluster = distances.index(min(distances))
            clusters[nearest_cluster].append(i)
        
        # Recompute centers
        new_centers = []
        for cluster_indices in clusters:
            if not cluster_indices:
                new_centers.append(centers[len(new_centers)])
            else:
                avg_lat = sum(places[i]["lat"] for i in cluster_indices) / len(cluster_indices)
                avg_lng = sum(places[i]["lng"] for i in cluster_indices) / len(cluster_indices)
                new_centers.append((avg_lat, avg_lng))
        
        # Check convergence
        old_centers = centers
        centers = new_centers
        if all(
            haversine_distance(old[0], old[1], new[0], new[1]) < 0.1
            for old, new in zip(old_centers, new_centers)
        ):
            break
    
    # Return places grouped by cluster, not indices
    clustered_places = [
        [places[i] for i in cluster_indices]
        for cluster_indices in clusters
    ]
    
    return clustered_places, centers


def tsp_greedy(distance_matrix: List[List[float]], start: int = 0) -> List[int]:
    """
    Solve TSP using greedy nearest-neighbor heuristic.
    Fast approximation suitable for small clusters.
    
    Args:
        distance_matrix: Pairwise distance matrix
        start: Starting point index
    
    Returns:
        List of indices in optimized order
    """
    n = len(distance_matrix)
    if n <= 1:
        return list(range(n))
    
    unvisited = set(range(n)) - {start}
    current = start
    tour = [current]
    
    while unvisited:
        nearest = min(
            unvisited,
            key=lambda x: distance_matrix[current][x]
        )
        tour.append(nearest)
        unvisited.remove(nearest)
        current = nearest
    
    return tour


def tsp_2opt(
    distance_matrix: List[List[float]],
    initial_tour: List[int] = None,
    max_iterations: int = 100
) -> List[int]:
    """
    Improve TSP tour using 2-opt local search.
    
    Args:
        distance_matrix: Pairwise distance matrix
        initial_tour: Starting tour (None = sequential)
        max_iterations: Max iterations
    
    Returns:
        Improved tour
    """
    n = len(distance_matrix)
    
    if initial_tour is None:
        tour = list(range(n))
    else:
        tour = initial_tour[:]
    
    def tour_distance(t):
        return sum(
            distance_matrix[t[i]][t[(i+1) % len(t)]]
            for i in range(len(t))
        )
    
    improved = True
    iteration = 0
    
    while improved and iteration < max_iterations:
        improved = False
        for i in range(1, n - 1):
            for j in range(i + 1, n):
                if j - i == 1:
                    continue
                
                # Reverse segment between i and j
                new_tour = tour[:i] + tour[i:j][::-1] + tour[j:]
                
                if tour_distance(new_tour) < tour_distance(tour):
                    tour = new_tour
                    improved = True
                    break
            if improved:
                break
        
        iteration += 1
    
    return tour


def optimize_itinerary_routes(
    places: List[Dict],
    days: int,
    distance_matrix: List[List[float]] = None
) -> List[List[Dict]]:
    """
    Organize places into efficient day-wise routes.
    
    Args:
        places: All scraped places
        days: Number of trip days
        distance_matrix: Pre-computed distance matrix (optional)
    
    Returns:
        List of day routes, each containing places in optimal order
    """
    if not places:
        return [[] for _ in range(days)]
    
    # Cluster places by geography
    clusters, centroids = kmeans_clustering(places, min(days, len(places)))
    
    # Build distance matrices for each cluster
    day_routes = []
    
    for cluster in clusters:
        if not cluster:
            continue
        
        # Build distance matrix for this cluster
        cluster_dist_matrix = build_distance_matrix(cluster)
        
        # Solve TSP for this cluster
        greedy_tour = tsp_greedy(cluster_dist_matrix)
        optimized_tour = tsp_2opt(cluster_dist_matrix, greedy_tour)
        
        # Reorder cluster by optimized tour
        optimized_cluster = [cluster[i] for i in optimized_tour]
        day_routes.append(optimized_cluster)
    
    # Pad with empty lists if needed
    while len(day_routes) < days:
        day_routes.append([])
    
    return day_routes[:days]


def estimate_travel_time(distance_km: float, mode: str = "local") -> float:
    """
    Estimate travel time based on distance and mode.
    
    Args:
        distance_km: Distance in kilometers
        mode: "local" (city), "highway", "mixed"
    
    Returns:
        Travel time in minutes (rounded)
    """
    # Average speeds (km/h)
    speeds = {
        "local": 15,      # City traffic
        "highway": 60,
        "mixed": 35,
    }
    
    speed = speeds.get(mode, 35)
    time_hours = distance_km / speed if speed > 0 else 0
    return round(time_hours * 60)


def calculate_day_feasibility(
    day_places: List[Dict],
    time_slots: int = 3,  # morning, afternoon, evening
    min_time_per_place: int = 120,  # minutes
    include_travel: bool = True
) -> Dict:
    """
    Check if a day itinerary is feasible time-wise.
    
    Args:
        day_places: Places for the day
        time_slots: Number of time slots available (morning/afternoon/evening)
        min_time_per_place: Minimum time at each place (minutes)
        include_travel: Whether to include travel time
    
    Returns:
        Dict with feasibility info
    """
    total_places = len(day_places)
    
    if total_places == 0:
        return {"feasible": True, "places": 0, "available_slots": time_slots}
    
    # Calculate total travel time if including between-place travel
    total_travel_time = 0
    if include_travel and total_places > 1:
        dist_matrix = build_distance_matrix(day_places)
        # Estimate travel time between consecutive places (greedy order)
        for i in range(len(day_places) - 1):
            travel_min = estimate_travel_time(dist_matrix[i][i+1])
            total_travel_time += travel_min
    
    # Calculate total activity time needed
    total_activity_time = total_places * min_time_per_place
    total_time_needed = total_activity_time + total_travel_time
    
    # Available time: roughly 8 hours per day = 480 minutes
    available_time = 8 * 60
    
    # Allocate time per slot
    time_per_slot = available_time / time_slots  # 160 minutes per slot
    
    return {
        "feasible": total_time_needed <= available_time,
        "places": total_places,
        "available_slots": time_slots,
        "total_time_needed": total_time_needed,
        "available_time": available_time,
        "travel_time": total_travel_time,
        "activity_time": total_activity_time,
        "utilization_percent": round((total_time_needed / available_time) * 100, 1),
    }
