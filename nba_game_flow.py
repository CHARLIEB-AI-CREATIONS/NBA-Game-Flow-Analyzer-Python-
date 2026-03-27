def evaluate_under(score_total, lead, time_left):
    
    if lead >= 15 and score_total < 200:
        return "GOOD UNDER ✅"
    
    elif 8 <= lead <= 14:
        return "DANGER ⚠️"
    
    elif score_total > 210:
        return "NO BET ❌"
    
    else:
        return "PASS"


# Example test
result = evaluate_under(score_total=190, lead=34, time_left=6)
print(result)
