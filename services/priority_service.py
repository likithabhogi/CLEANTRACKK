import json
from datetime import datetime

def calculate_priority_score(waste_category, description="", address="", hours_elapsed=0, is_in_cluster=False):
    """
    Transparent, rule-based algorithmic priority scoring engine.
    Calculates a score between 1 and 100 and breaks down the exact contributing factors.
    """
    factors = []
    base_score = 0

    # 1. Waste Category Hazard Weight
    category_weights = {
        "Mixed Waste": (30, "High contamination risk and hazardous commingled urban waste"),
        "Organic": (25, "Rapid decomposition, pest attraction, biohazard and foul odor risk"),
        "Metal/Glass": (20, "Physical puncture and laceration hazard for pedestrians/traffic"),
        "Plastic": (15, "Non-biodegradable storm-drain clogging and environmental hazard"),
        "Paper/Cardboard": (10, "Combustible debris and public nuisance hazard"),
        "Other": (20, "Unclassified municipal waste requiring verification")
    }

    cat_points, cat_reason = category_weights.get(waste_category, (15, "Standard municipal waste weight"))
    base_score += cat_points
    factors.append({
        "factor": "Waste Type Hazard",
        "points": cat_points,
        "detail": f"{waste_category}: {cat_reason}"
    })

    # 2. Age of Complaint (SLA Urgency)
    if hours_elapsed >= 48:
        age_points = 25
        age_reason = "Pending over 48 hours - SLA escalation threshold exceeded"
    elif hours_elapsed >= 24:
        age_points = 15
        age_reason = "Pending over 24 hours - standard SLA escalation"
    elif hours_elapsed >= 12:
        age_points = 10
        age_reason = "Pending over 12 hours"
    else:
        age_points = 5
        age_reason = "Recently submitted (< 12 hours)"
    
    base_score += age_points
    factors.append({
        "factor": "Complaint Age Escalation",
        "points": age_points,
        "detail": age_reason
    })

    # 3. Location & Public Sensitivity Keywords
    combined_text = f"{description} {address}".lower()
    sensitive_keywords = {
        "hospital": (15, "Near medical facility / public health priority"),
        "clinic": (15, "Near healthcare facility"),
        "school": (15, "Near educational institution / children safety"),
        "kindergarten": (15, "Near childcare center"),
        "drain": (10, "Drainage blockage or flood risk indicated"),
        "water": (10, "Water body contamination hazard"),
        "market": (10, "High-footfall commercial / food zone"),
        "road": (5, "Obstruction of public roadway / vehicular route"),
        "toxic": (15, "Toxic or pungent substance mentioned"),
        "smell": (8, "Intense odor reported"),
        "rats": (10, "Vermin / rodent infestation reported")
    }

    matched_keywords = []
    keyword_points = 0
    for kw, (pts, note) in sensitive_keywords.items():
        if kw in combined_text:
            matched_keywords.append(note)
            keyword_points = max(keyword_points, pts) # take highest sensitivity match + bonus

    if matched_keywords:
        # cap sensitivity points at 25
        actual_kw_pts = min(25, keyword_points + (len(matched_keywords) - 1) * 3)
        base_score += actual_kw_pts
        factors.append({
            "factor": "Public & Environmental Sensitivity",
            "points": actual_kw_pts,
            "detail": "; ".join(matched_keywords[:2])
        })
    else:
        factors.append({
            "factor": "Public & Environmental Sensitivity",
            "points": 0,
            "detail": "No high-risk public facility keywords detected"
        })

    # 4. Hotspot Cluster Density
    if is_in_cluster:
        cluster_pts = 15
        base_score += cluster_pts
        factors.append({
            "factor": "Hotspot Cluster Proximity",
            "points": cluster_pts,
            "detail": "Location falls inside an active dense municipal waste cluster"
        })
    else:
        factors.append({
            "factor": "Hotspot Cluster Proximity",
            "points": 0,
            "detail": "Isolated report location"
        })

    # Clamp score to 1-100
    final_score = max(1, min(100, base_score))

    # Priority level determination
    if final_score >= 80:
        level = "Urgent"
    elif final_score >= 60:
        level = "High"
    elif final_score >= 40:
        level = "Medium"
    else:
        level = "Low"

    return {
        "score": final_score,
        "level": level,
        "factors": factors
    }
