def solve(input_data):
    intervals = input_data["intervals"]
    return {
        "merged": intervals,
        "covered_length": sum(b - a + 1 for a, b in intervals),
        "target_covered": False,
    }

