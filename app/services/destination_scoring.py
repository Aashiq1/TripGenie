def score_destination(destination: dict, group_profile: dict, trip_length: int) -> int:
    """
    Scores a destination based on how well it matches the group's preferences.

    The score is based on:
    - How many group-preferred vibes the destination matches (weighted ×3)
    - How many group-preferred interests it matches (weighted ×2)
    - Whether the estimated trip cost fits within the group's budget range

    Args:
        destination (dict): A destination with keys:
            - "vibes": list of vibes the destination offers
            - "interests": list of interests supported
            - "cost_per_day": estimated cost per person per day
        group_profile (dict): Aggregated group preferences including:
            - "vibes": dict of vibe weights
            - "interests": dict of interest weights
            - "budget_min": highest of all users' minimum budgets
            - "budget_max": lowest of all users' max budgets
        trip_length (int): Number of days in the proposed trip

    Returns:
        int: A score representing how well the destination fits the group
    """
    score = 0

    # Score based on vibe alignment (weight = 3)
    for vibe in destination["vibes"]:
        score += group_profile["vibes"].get(vibe, 0) * 3

    # Score based on interest alignment (weight = 2)
    for interest in destination["interests"]:
        score += group_profile["interests"].get(interest, 0) * 2

    # Estimate total trip cost
    total_cost = destination["cost_per_day"] * trip_length

    # Budget alignment
    if total_cost <= group_profile["budget_min"]:
        score += 5  # Excellent fit
    elif total_cost <= group_profile["budget_max"]:
        score += 2  # Acceptable fit
    else:
        score -= 5  # Outside budget range

    return score

