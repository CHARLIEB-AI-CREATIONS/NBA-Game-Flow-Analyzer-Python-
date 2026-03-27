def evaluate_game(total_score, lead, time_left):
    """
    Evaluates NBA game flow conditions.

    Args:
        total_score (int): Combined score of both teams
        lead (int): Point difference between teams
        time_left (int): Minutes remaining

    Returns:
        str: Decision category
    """

    if lead >= 15 and total_score < 200:
        return "GOOD UNDER ✅"
    
    elif 8 <= lead <= 14:
        return "DANGER ⚠️"
    
    elif total_score > 210:
        return "NO BET ❌"
    
    else:
        return "PASS"


# Example usage
if __name__ == "__main__":
    total_score = int(input("Enter total score: "))
    lead = int(input("Enter lead: "))
    time_left = int(input("Enter minutes left: "))

    result = evaluate_game(total_score, lead, time_left)
    print(f"\nDecision: {result}")
