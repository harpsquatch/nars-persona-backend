def calculate_consultation_result(answers):
    """
    Implements the NARS Persona questionnaire scoring algorithm.
    """
    print(f"Received answers: {answers}")  # Debug print
    
    # Validate input format
    if not isinstance(answers, dict):
        raise ValueError("Answers must be a dictionary")
        
    valid_responses = {'strongly_agree', 'agree', 'neutral', 'disagree', 'strongly_disagree'}
    
    # Validate all answers
    for q_num, answer in answers.items():
        if not isinstance(answer, str):
            raise ValueError(f"Answer for {q_num} must be a string")
        if answer.lower() not in valid_responses:
            raise ValueError(f"Invalid answer '{answer}' for {q_num}. Must be one of: {valid_responses}")
    
    # Step 1: Convert answers to numerical values (-2 to +2)
    answer_values = {
        'strongly_agree': 2,
        'agree': 1,
        'neutral': 0,
        'disagree': -1,
        'strongly_disagree': -2
    }
    
    # Multiplier matrix (questions × traits)
    multiplier_matrix = [
        [1, 0, 0, 1, -1],  # Q1
        [-1, 1, 0, -1, 1], # Q2
        [1, 0, 0, 1, -1],  # Q3
        [0, 1, 0, 0, 0],   # Q4
        [0, 1, 0, 0, 0],   # Q5
        [0, 0, 1, 0, 0],   # Q6
        [-1, 0, 1, -1, 1], # Q7
        [1, 0, 0, 1, -1],  # Q8
        [-1, 1, 0, -1, 1], # Q9
        [1, 0, 0, 1, -1]   # Q10
    ]
    
    # Initialize score vector [self-esteem, introspection, public_image, body_perception, social_anxiety]
    scores = [0, 0, 0, 0, 0]
    
    # Step 2: Calculate raw scores using multiplier matrix
    for q_num, answer in answers.items():
        q_index = int(q_num[1:]) - 1  # Convert q1 to index 0, q2 to 1, etc.
        answer_value = answer_values[answer.lower()]
        
        for trait_index in range(5):
            multiplier = multiplier_matrix[q_index][trait_index]
            scores[trait_index] += (answer_value * multiplier)
    
    # Step 3: Convert to binary
    binary = ['0'] * 5
    
    # Handle first 4 traits (≥0 becomes 1)
    for i in range(4):
        if scores[i] >= 0:
            binary[i] = '1'
    
    # Handle social anxiety differently (≥1 becomes 1)
    if scores[4] >= 1:
        binary[4] = '1'
    
    # Special case: if social anxiety is 1 and public image focus is 0, force public image to 1
    if binary[4] == '1' and binary[2] == '0':
        binary[2] = '1'
    
    # Step 4: Match binary number to persona
    persona_map = {
        '00101': 'Refined Style',
        '01101': 'Modern Elegance',
        '10010': 'Bold Spirit',
        '10110': 'Radiant Simplicity',
        '11010': 'Authentic Beauty',
        '11110': 'Creative Expression'
    }
    
    binary_string = ''.join(binary)
    
    result = {
        'archetype': persona_map.get(binary_string, 'Unknown'),
        'binary': binary_string,
        'scores': scores,  # Including raw scores for debugging
    }
    
    return result 