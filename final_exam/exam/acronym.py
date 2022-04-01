from _pytest.python_api import raises


def acronym_make(inputs):
    if len(inputs) == 0:
        raise ValueError
    arco = []
    for string in inputs:
        char = ""
        for word in string.split():
            if word[0] not in "aeiouAEIOU":
                char = char + word[0].upper()
        if len(char) >= 10:
            char = "N/A"
        arco.append(char)

    return arco

