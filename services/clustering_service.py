import numpy as np
from sklearn.cluster import DBSCAN
import math

EARTH_RADIUS_METERS = 6371000.0

def run_dbscan_clustering(reports, eps_meters=600.0, min_samples=2):
    """
    Executes Scikit-learn DBSCAN clustering on geographical report coordinates.
    Converts coordinates to radians for the Haversine metric.
    Separates detected spatial clusters from isolated noise points.
    
    Parameters:
        reports: List of dicts, each containing 'id', 'complaint_id', 'latitude', 'longitude',
                 'priority_level', 'status', 'waste_category', etc.
        eps_meters: Epsilon neighborhood radius in meters (default 600m)
        min_samples: Minimum number of samples to form a dense core cluster (default 2)
        
    Returns:
        Dictionary with:
            - clusters: List of cluster objects (cluster_id, centroid, radius_meters, reports, count, high_priority_count)
            - noise_points: List of isolated reports with label -1
            - total_clustered_reports: Count of reports belonging to valid clusters
            - cluster_count: Total number of distinct dense clusters detected
            - parameters: {eps_meters, min_samples}
    """
    valid_reports = []
    coords = []
    
    for r in reports:
        try:
            lat = float(r['latitude'])
            lng = float(r['longitude'])
            if -90 <= lat <= 90 and -180 <= lng <= 180:
                valid_reports.append(r)
                coords.append([lat, lng])
        except (ValueError, TypeError, KeyError):
            continue

    if len(coords) < min_samples:
        return {
            "clusters": [],
            "noise_points": valid_reports,
            "total_clustered_reports": 0,
            "cluster_count": 0,
            "parameters": {"eps_meters": eps_meters, "min_samples": min_samples}
        }

    # Convert coordinates [lat, lon] to radians for Haversine metric
    coords_rad = np.radians(coords)
    eps_rad = eps_meters / EARTH_RADIUS_METERS

    # Run DBSCAN
    db = DBSCAN(eps=eps_rad, min_samples=min_samples, metric='haversine')
    labels = db.fit_predict(coords_rad)

    cluster_groups = {}
    noise_reports = []

    for idx, label in enumerate(labels):
        report_item = dict(valid_reports[idx])
        report_item['cluster_id'] = int(label)
        
        if label == -1:
            noise_reports.append(report_item)
        else:
            if label not in cluster_groups:
                cluster_groups[label] = []
            cluster_groups[label].append(report_item)

    clusters_list = []
    for cluster_id, items in cluster_groups.items():
        # Compute centroid
        lats = [item['latitude'] for item in items]
        lngs = [item['longitude'] for item in items]
        centroid_lat = float(np.mean(lats))
        centroid_lng = float(np.mean(lngs))

        # Compute max distance from centroid as estimated cluster radius (min 80m for visibility)
        max_dist = 80.0
        for item in items:
            d_lat = math.radians(item['latitude'] - centroid_lat)
            d_lng = math.radians(item['longitude'] - centroid_lng)
            a = math.sin(d_lat / 2)**2 + math.cos(math.radians(centroid_lat)) * math.cos(math.radians(item['latitude'])) * math.sin(d_lng / 2)**2
            c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
            dist = EARTH_RADIUS_METERS * c
            if dist > max_dist:
                max_dist = dist

        # Summary statistics for this cluster
        high_priority_count = sum(1 for it in items if it.get('priority_level') in ['High', 'Urgent'])
        pending_count = sum(1 for it in items if it.get('status') in ['Pending', 'Reviewed'])
        
        # Calculate cluster density severity
        if high_priority_count >= 2 or len(items) >= 4:
            severity = 'Critical'
            color = '#ef4444' # Red
        elif len(items) >= 3 or pending_count >= 2:
            severity = 'Moderate'
            color = '#f59e0b' # Amber
        else:
            severity = 'Low'
            color = '#10b981' # Green

        clusters_list.append({
            "cluster_id": int(cluster_id),
            "name": f"Hotspot Zone #{int(cluster_id) + 1}",
            "centroid": {"lat": centroid_lat, "lng": centroid_lng},
            "radius_meters": round(max_dist + 50, 1),
            "report_count": len(items),
            "high_priority_count": high_priority_count,
            "pending_count": pending_count,
            "severity": severity,
            "color": color,
            "reports": items
        })

    # Sort clusters by report count descending
    clusters_list.sort(key=lambda c: (c['high_priority_count'], c['report_count']), reverse=True)

    return {
        "clusters": clusters_list,
        "noise_points": noise_reports,
        "total_clustered_reports": sum(c['report_count'] for c in clusters_list),
        "cluster_count": len(clusters_list),
        "parameters": {"eps_meters": eps_meters, "min_samples": min_samples}
    }
