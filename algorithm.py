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
    
    # Step 4: Match binary number to archetype
    # These must match the binary_representation in the Archetype model
    # Primary mappings that exist in the database
    primary_archetype_map = {
        '00000': 'The Minimalist',
        '11111': 'The Bold Innovator',
        '01010': 'The Classic Elegance',
        '10101': 'The Creative Artist',
        '00011': 'The Natural Glow',
        '11100': 'The Glamorous',
        '01100': 'The Versatile Chameleon',
        '10010': 'The Edgy Rebel',
    }
    
    # Map other possible binary combinations to the closest archetype
    # This ensures all generated binaries map to an existing archetype in the database
    fallback_archetype_map = {
        '00001': '00000',  # -> The Minimalist
        '00010': '00000',  # -> The Minimalist
        '00100': '01100',  # -> The Versatile Chameleon
        '00101': '01010',  # -> The Classic Elegance
        '00110': '01100',  # -> The Versatile Chameleon
        '00111': '00011',  # -> The Natural Glow
        '01000': '01100',  # -> The Versatile Chameleon
        '01001': '01010',  # -> The Classic Elegance
        '01011': '01010',  # -> The Classic Elegance
        '01101': '01100',  # -> The Versatile Chameleon
        '01110': '01100',  # -> The Versatile Chameleon
        '01111': '11100',  # -> The Glamorous
        '10000': '10010',  # -> The Edgy Rebel
        '10001': '10101',  # -> The Creative Artist
        '10011': '10101',  # -> The Creative Artist
        '10100': '10101',  # -> The Creative Artist
        '10110': '10101',  # -> The Creative Artist
        '10111': '10101',  # -> The Creative Artist
        '11000': '11100',  # -> The Glamorous
        '11001': '11111',  # -> The Bold Innovator
        '11010': '11111',  # -> The Bold Innovator (maps legacy 11010)
        '11011': '11111',  # -> The Bold Innovator
        '11101': '11111',  # -> The Bold Innovator
        '11110': '11111',  # -> The Bold Innovator
    }
    
    binary_string = ''.join(binary)
    
    # If binary exists in primary map, use it directly
    # Otherwise, map to closest archetype using fallback map
    if binary_string in primary_archetype_map:
        mapped_binary = binary_string
    else:
        mapped_binary = fallback_archetype_map.get(binary_string, '01100')  # Default to Versatile Chameleon
    
    result = {
        'archetype': primary_archetype_map[mapped_binary],
        'archetype_id': mapped_binary,  # Store the mapped binary for database lookup
        'binary': binary_string,  # Keep original binary for reference
        'scores': scores,  # Including raw scores for debugging
    }
    
    return result 