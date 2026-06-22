def get_sigma_n(alphabet, n):
    """Genera recursivamente todas las combinaciones de Sigma a la n."""
    if n == 0:
        return {"λ"}
    if n == 1:
        return set(alphabet)
    
    res = set()
    prev = get_sigma_n(alphabet, n - 1)
    for char in alphabet:
        for word in prev:
            # Evitamos concatenar lambda como texto
            new_word = char + (word if word != "λ" else "")
            res.add(new_word)
    return res

def get_kleene_closure(alphabet, max_n):
    """Calcula la unión de Sigma^0 hasta Sigma^n."""
    closure = set()
    for i in range(max_n + 1):
        closure.update(get_sigma_n(alphabet, i))
    return sorted(list(closure), key=lambda x: (len(x), x))

def get_positive_closure(alphabet, max_n):
    """Calcula la unión de Sigma^1 hasta Sigma^n."""
    closure = set()
    for i in range(1, max_n + 1):
        closure.update(get_sigma_n(alphabet, i))
    return sorted(list(closure), key=lambda x: (len(x), x))