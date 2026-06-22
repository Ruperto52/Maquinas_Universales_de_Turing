class ContextFreeGrammar:
    def __init__(self):
        self.productions = {}
        self.start_symbol = 'S'

    def load_from_text(self, text):
        self.productions = {}
        lines = text.strip().split('\n')
        for line in lines:
            if '->' not in line: continue
            head, body = line.split('->')
            head = head.strip()
            
            if not self.productions:
                self.start_symbol = head
                
            rules = [r.strip().replace(" ", "") for r in body.split('|')]
            rules = [r if r.lower() not in ['e', 'ε', 'lambda'] else '' for r in rules]
            
            if head in self.productions:
                self.productions[head].extend(rules)
            else:
                self.productions[head] = rules

    def validate_string(self, target_string, max_depth=15):
        """
        Simulación educativa de derivación top-down usando DFS.
        Límite de profundidad (max_depth) para evitar bucles infinitos en recursión izquierda.
        """
        if not self.productions:
            return False, "No hay producciones cargadas."

        # Pila de búsqueda: (cadena_actual_derivada, historial_derivaciones, profundidad)
        stack = [(self.start_symbol, f"Derivación inicial: {self.start_symbol}", 0)]
        
        while stack:
            current_form, trace, depth = stack.pop()
            
            if current_form == target_string:
                return True, trace
                
            if depth >= max_depth:
                continue # Evitar derivaciones infinitas
                
            if len(current_form) > len(target_string) * 2: 
                continue # Poda heurística si la derivación excede el tamaño lógico esperado
                
            # Buscar la primera variable (No Terminal) en la forma actual
            for i, char in enumerate(current_form):
                if char in self.productions:
                    # Encontramos una variable, aplicamos todas sus producciones posibles
                    for prod in self.productions[char]:
                        new_form = current_form[:i] + prod + current_form[i+1:]
                        new_trace = trace + f"\n => {new_form}  (Aplicando {char} -> {prod if prod else 'λ'})"
                        stack.append((new_form, new_trace, depth + 1))
                    break # Derivación más a la izquierda (Leftmost derivation)

        return False, f"La cadena '{target_string}' no pudo ser derivada desde el símbolo inicial '{self.start_symbol}'.\n(Límite de profundidad alcanzado o no hay ruta estructural válida)."