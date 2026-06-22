def get_prefixes(string):
    """Calcula todos los prefijos de una cadena."""
    return [string[:i] for i in range(len(string) + 1)]

def get_suffixes(string):
    """Calcula todos los sufijos de una cadena."""
    return [string[i:] for i in range(len(string) + 1)]

def get_substrings(string):
    """Calcula todas las subcadenas posibles ordenadas por longitud."""
    substrings = {""} 
    n = len(string)
    for i in range(n):
        for j in range(i + 1, n + 1):
            substrings.add(string[i:j])
    return sorted(list(substrings), key=lambda x: (len(x), x))