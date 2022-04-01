def filter_string(inp):   
    output = ""
    punctuation_spec = '''.,"':?!'''
    for char in inp:
        if char.isnumeric() == True:
            raise ValueError
    if inp[0] not in punctuation_spec:
        output = output + inp[0]
    for ch in inp[1:]:
        if ch not in punctuation_spec:
            if len(output) == 0:
                output = output + ch.upper()
            else: 
                output = output + ch.lower()
    return output