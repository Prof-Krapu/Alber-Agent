def calculate_variance_experimental(numbers):
    if not numbers:
        return 0
    
    mean = sum(numbers) / len(numbers)
    
    # Calcul de la variance
    squared_differences = [(x - mean) ** 2 for x in numbers]
    variance = sum(squared_differences) / len(numbers)  # Variance populationnelle
    
    return variance