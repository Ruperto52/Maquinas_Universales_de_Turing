import json
import xml.etree.ElementTree as ET
import math

class Automaton:
    def __init__(self):
        self.states = []
        self.alphabet = []
        self.initial_state = None
        self.final_states = []
        self.transitions = {} # Ahora mapea: (estado, simbolo) -> set(estados_destino)

    def clear(self):
        self.__init__()

    def add_transition(self, src, char, dest):
        if (src, char) not in self.transitions:
            self.transitions[(src, char)] = set()
        self.transitions[(src, char)].add(dest)

    def load_from_json(self, filepath):
        self.clear()
        with open(filepath, 'r') as f:
            data = json.load(f)
            self.states = data['states']
            self.alphabet = data['alphabet']
            self.initial_state = data['initial_state']
            self.final_states = data['final_states']
            for k, v in data['transitions'].items():
                src, char = k.split(',')
                dests = v if isinstance(v, list) else [v]
                for d in dests:
                    self.add_transition(src, char, d)

    def load_from_jff(self, filepath):
        self.clear()
        tree = ET.parse(filepath)
        root = tree.getroot()
        id_map = {}
        for s in root.findall('.//state'):
            name = s.get('name')
            id_map[s.get('id')] = name
            self.states.append(name)
            if s.find('initial') is not None: self.initial_state = name
            if s.find('final') is not None: self.final_states.append(name)
        for t in root.findall('.//transition'):
            f = id_map[t.find('from').text]
            to = id_map[t.find('to').text]
            r_node = t.find('read')
            r = r_node.text if r_node is not None and r_node.text else "λ"
            self.add_transition(f, r, to)
            if r != "λ" and r not in self.alphabet: self.alphabet.append(r)

    def get_lambda_closure(self, states):
        """Calcula la λ-clausura para un conjunto de estados."""
        closure = set(states)
        stack = list(states)
        while stack:
            s = stack.pop()
            if (s, "λ") in self.transitions:
                for dest in self.transitions[(s, "λ")]:
                    if dest not in closure:
                        closure.add(dest)
                        stack.append(dest)
        return closure

    def validate_string(self, string):
        """Valida una cadena manejando ramificaciones y λ-clausuras."""
        if not self.initial_state: return False, ["Error: No inicial"], set()
        current_states = self.get_lambda_closure({self.initial_state})
        path = [f"INICIO: λ-clausura({self.initial_state}) = {current_states}"]
        
        for char in string:
            next_states = set()
            for s in current_states:
                if (s, char) in self.transitions:
                    next_states.update(self.transitions[(s, char)])
            
            path.append(f"Leer '{char}': Transiciones desde {current_states} -> {next_states}")
            current_states = self.get_lambda_closure(next_states)
            path.append(f"λ-clausura actual -> {current_states}")
            
            if not current_states:
                path.append("BLOQUEO: Sin caminos activos.")
                return False, path, current_states
                
        is_accepted = any(s in self.final_states for s in current_states)
        path.append(f"FINAL: {current_states} ({'ACEPTADO' if is_accepted else 'RECHAZADO'})")
        return is_accepted, path, current_states

    def minimize(self):
        """Minimiza un AFD usando el algoritmo de Hopcroft."""
        # 1. Eliminar inalcanzables
        reachable = set()
        stack = [self.initial_state] if self.initial_state else []
        if stack: reachable.add(self.initial_state)
        while stack:
            curr = stack.pop()
            for char in self.alphabet:
                if (curr, char) in self.transitions:
                    for d in self.transitions[(curr, char)]:
                        if d not in reachable:
                            reachable.add(d)
                            stack.append(d)
        
        st = [s for s in self.states if s in reachable]
        fs = [s for s in self.final_states if s in reachable]
        
        # 2. Clases de Equivalencia (Hopcroft)
        P = [set(fs), set(st) - set(fs)]
        P = [p for p in P if p]
        W = [set(fs), set(st) - set(fs)]
        W = [w for w in W if w]
        
        def get_inv(target_set, char):
            inv = set()
            for s in st:
                if (s, char) in self.transitions:
                    if any(d in target_set for d in self.transitions[(s, char)]):
                        inv.add(s)
            return inv

        while W:
            A = W.pop(0)
            for c in self.alphabet:
                X = get_inv(A, c)
                new_P = []
                for Y in P:
                    intersect = Y.intersection(X)
                    diff = Y - X
                    if intersect and diff:
                        new_P.append(intersect)
                        new_P.append(diff)
                        if Y in W:
                            W.remove(Y)
                            W.append(intersect)
                            W.append(diff)
                        else:
                            W.append(intersect if len(intersect) <= len(diff) else diff)
                    else:
                        new_P.append(Y)
                P = new_P
                
        # 3. Construir AFD minimizado
        min_dfa = Automaton()
        min_dfa.alphabet = self.alphabet.copy()
        state_map = {}
        for i, group in enumerate(P):
            g_name = f"q{i}"
            min_dfa.states.append(g_name)
            for s in group:
                state_map[s] = g_name
                if s == self.initial_state: min_dfa.initial_state = g_name
                if s in self.final_states and g_name not in min_dfa.final_states:
                    min_dfa.final_states.append(g_name)
                    
        for s in st:
            for c in self.alphabet:
                if (s, c) in self.transitions:
                    for dest in self.transitions[(s, c)]:
                        min_dfa.add_transition(state_map[s], c, state_map[dest])
        return min_dfa, len(self.states), len(min_dfa.states), P

    def to_dfa(self):
        """Convierte AFN/AFN-λ a AFD (Construcción de Subconjuntos)."""
        dfa = Automaton()
        dfa.alphabet = [a for a in self.alphabet if a != "λ"]
        if not self.initial_state: return dfa
        
        init_closure = frozenset(self.get_lambda_closure({self.initial_state}))
        unmarked = [init_closure]
        dfa_states = {init_closure: "Q0"}
        state_counter = 1
        dfa.states.append("Q0")
        dfa.initial_state = "Q0"
        
        while unmarked:
            T = unmarked.pop(0)
            T_name = dfa_states[T]
            
            if any(s in self.final_states for s in T) and T_name not in dfa.final_states:
                dfa.final_states.append(T_name)
                    
            for a in dfa.alphabet:
                U = set()
                for s in T:
                    if (s, a) in self.transitions:
                        U.update(self.transitions[(s, a)])
                if not U: continue
                U_closure = frozenset(self.get_lambda_closure(U))
                
                if U_closure not in dfa_states:
                    new_name = f"Q{state_counter}"
                    state_counter += 1
                    dfa_states[U_closure] = new_name
                    dfa.states.append(new_name)
                    unmarked.append(U_closure)
                    
                dfa.add_transition(T_name, a, dfa_states[U_closure])
        return dfa

    def draw_on_canvas(self, canvas):
        canvas.delete("all")
        canvas.update_idletasks()
        w, h = canvas.winfo_width(), canvas.winfo_height()
        if w <= 1 or h <= 1: w, h = 400, 300 
        cx, cy = w/2, h/2
        r, dist = 20, min(cx, cy) * 0.7
        if not self.states: return
        pos = {s: (cx + dist*math.cos(2*math.pi*i/len(self.states)), 
                   cy + dist*math.sin(2*math.pi*i/len(self.states))) 
               for i, s in enumerate(self.states)}

        edge_labels = {}
        for (f, char), dests in self.transitions.items():
            for t in dests:
                if (f, t) not in edge_labels: edge_labels[(f, t)] = []
                edge_labels[(f, t)].append(char)

        for (f, t), chars in edge_labels.items():
            x1, y1 = pos[f]; x2, y2 = pos[t]
            color = "#f43f5e" if "λ" in chars else "#38bdf8"
            label = ",".join(chars)
            if f == t:
                canvas.create_oval(x1-20, y1-50, x1+20, y1-10, outline=color)
                canvas.create_text(x1, y1-55, text=label, fill=color)
            else:
                if "λ" in chars:
                    canvas.create_line(x1, y1, x2, y2, arrow="last", fill=color, dash=(4, 4))
                else:
                    canvas.create_line(x1, y1, x2, y2, arrow="last", fill="#94a3b8")
                canvas.create_text((x1+x2)/2, (y1+y2)/2 - 10, text=label, fill=color)

        for s in self.states:
            x, y = pos[s]
            col = "#fbbf24" if s == self.initial_state else "#38bdf8"
            canvas.create_oval(x-r, y-r, x+r, y+r, fill="#1e293b", outline=col, width=2)
            if s in self.final_states: canvas.create_oval(x-r+4, y-r+4, x+r-4, y+r-4, outline=col)
            canvas.create_text(x, y, text=s, fill="white")

    def from_regex(self, regex):
        """
        Construye un AFN a partir de una Expresión Regular usando el Algoritmo de Thompson.
        """
        self.clear() # Limpiamos cualquier estado o transición anterior
        regex = regex.replace(" ", "").replace("ε", "λ")
        
        # Función auxiliar para identificar literales del alfabeto
        def is_literal(c):
            return c not in ['(', ')', '*', '|', '.']

        # 1. Extraemos el alfabeto de la expresión (ignorando operadores lógicos)
        self.alphabet = list(set(c for c in regex if is_literal(c) and c != "λ"))
        if "λ" not in self.alphabet:
            self.alphabet.append("λ")

        # 2. Insertar operador de concatenación explícito '.'
        def insert_concat(re_str):
            res = ""
            for i in range(len(re_str)):
                res += re_str[i]
                if i + 1 < len(re_str):
                    c1, c2 = re_str[i], re_str[i+1]
                    # Si unimos un literal/cierre con otro literal/apertura, hay concatenación implícita
                    if (is_literal(c1) or c1 in ['*', ')']) and (is_literal(c2) or c2 == '('):
                        res += "."
            return res

        # 3. Convertir a notación Postfija (Shunting Yard Algorithm)
        def to_postfix(re_str):
            precedence = {'*': 3, '.': 2, '|': 1}
            output = []
            stack = []
            for c in re_str:
                if is_literal(c):
                    output.append(c)
                elif c == '(':
                    stack.append(c)
                elif c == ')':
                    while stack and stack[-1] != '(':
                        output.append(stack.pop())
                    stack.pop() # Quitar el '(' de la pila
                else:
                    while stack and stack[-1] != '(' and precedence.get(stack[-1], 0) >= precedence.get(c, 0):
                        output.append(stack.pop())
                    stack.append(c)
            while stack:
                output.append(stack.pop())
            return "".join(output)

        regex_concat = insert_concat(regex)
        postfix = to_postfix(regex_concat)

        # 4. Construcción de Thompson (Evaluación usando una pila)
        state_count = 0
        def new_state():
            nonlocal state_count
            name = f"q{state_count}"
            state_count += 1
            self.states.append(name)
            return name

        stack = []
        for c in postfix:
            if c == '*': # Clausura de Kleene
                start, end = stack.pop()
                n_start, n_end = new_state(), new_state()
                self.add_transition(n_start, "λ", start)
                self.add_transition(n_start, "λ", n_end)
                self.add_transition(end, "λ", start)
                self.add_transition(end, "λ", n_end)
                stack.append((n_start, n_end))
                
            elif c == '.': # Concatenación
                start2, end2 = stack.pop()
                start1, end1 = stack.pop()
                self.add_transition(end1, "λ", start2)
                stack.append((start1, end2))
                
            elif c == '|': # Unión
                start2, end2 = stack.pop()
                start1, end1 = stack.pop()
                n_start, n_end = new_state(), new_state()
                self.add_transition(n_start, "λ", start1)
                self.add_transition(n_start, "λ", start2)
                self.add_transition(end1, "λ", n_end)
                self.add_transition(end2, "λ", n_end)
                stack.append((n_start, n_end))
                
            elif is_literal(c): # Símbolo del alfabeto
                start, end = new_state(), new_state()
                self.add_transition(start, c, end)
                stack.append((start, end))

        # El último fragmento en la pila es nuestro AFN completo
        if stack:
            final_start, final_end = stack.pop()
            self.initial_state = final_start
            self.final_states = [final_end]
        else:
            # Seguro por si mandan una cadena vacía
            s = new_state()
            self.initial_state = s
            self.final_states = [s]
            
        print(f"AFN generado exitosamente para: {regex}")

    def to_regex(self):
        """
        Convierte el autómata actual a una Expresión Regular usando eliminación de estados
        (Teorema de Kleene).
        """
        if not self.states or not self.initial_state or not self.final_states:
            return "∅"

        # 1. Crear un diccionario de transiciones: (origen, destino) -> Expresión Regular
        R = {}

        # Inicializar R con las transiciones existentes (Unión si hay múltiples símbolos)
        for q in self.states:
            for char in self.alphabet:
                if (q, char) in self.transitions:
                    for dest in self.transitions[(q, char)]:
                        if (q, dest) not in R: 
                            R[(q, dest)] = char
                        else: 
                            R[(q, dest)] = f"({R[(q, dest)]}+{char})"
        
        # Manejar lambdas si existen en las transiciones originales
        if "λ" in self.alphabet:
            for q in self.states:
                if (q, "λ") in self.transitions:
                    for dest in self.transitions[(q, "λ")]:
                        if (q, dest) not in R: 
                            R[(q, dest)] = "λ"
                        else: 
                            R[(q, dest)] = f"({R[(q, dest)]}+λ)"

        # 2. Agregar un nuevo estado inicial (S) y final (E)
        S, E = "START_NODE", "END_NODE"
        R[(S, self.initial_state)] = "λ"
        for f in self.final_states:
            R[(f, E)] = "λ"
        
        temp_states = list(self.states) + [S, E]

        # 3. Eliminar estados intermedios uno por uno (excepto S y E)
        for q_rem in self.states:
            # Seleccionamos todos los pares (q_i, q_j) que pasan por q_rem
            for q_i in temp_states:
                if q_i == q_rem or q_i == E: continue
                for q_j in temp_states:
                    if q_j == q_rem or q_j == S: continue
                    
                    # Fórmula de eliminación: R_ij = R_ij + R_ik (R_kk)* R_kj
                    r_ij = R.get((q_i, q_j))
                    r_ik = R.get((q_i, q_rem))
                    r_kk = R.get((q_rem, q_rem))
                    r_kj = R.get((q_rem, q_j))

                    # Solo si existe un camino de q_i a q_j a través de q_rem
                    if r_ik and r_kj:
                        # Construir la nueva parte: r_ik(r_kk)*r_kj
                        
                        # Simplificaciones básicas para no tener paréntesis excesivos
                        term_ik = r_ik if len(r_ik) == 1 or r_ik == "λ" else f"({r_ik})"
                        term_kj = r_kj if len(r_kj) == 1 or r_kj == "λ" else f"({r_kj})"
                        
                        term = ""
                        if term_ik != "λ": term += term_ik
                        
                        if r_kk: 
                            if len(r_kk) == 1: term += f"{r_kk}*"
                            else: term += f"({r_kk})*"
                            
                        if term_kj != "λ": term += term_kj
                        
                        if term == "": term = "λ" # Si todo era lambda, el resultado es lambda

                        # Unir con el camino directo existente (si lo hay)
                        if r_ij:
                            R[(q_i, q_j)] = f"({r_ij}+{term})"
                        else:
                            R[(q_i, q_j)] = term
            
            # Limpiar las transiciones del estado eliminado para liberar memoria
            keys_to_del = [k for k in R if q_rem in k]
            for k in keys_to_del: 
                del R[k]

        # 4. El resultado final es la transición del START_NODE al END_NODE
        final_regex = R.get((S, E), "∅")
        
        # Opcional: Reemplazar el símbolo de suma por la barra de unión estándar y λ por ε
        final_regex = final_regex.replace("+", "|").replace("λ", "ε")
        
        return final_regex

    def save_to_json(self, path):
        data = {
            "states": list(self.states), "alphabet": list(self.alphabet),
            "initial_state": self.initial_state, "final_states": list(self.final_states),
            "transitions": {f"{q},{a}": list(dest) for (q, a), dest in self.transitions.items()}
        }
        with open(path, 'w') as f: json.dump(data, f, indent=4)

    def save_to_jff(self, path):
        structure = ET.Element('structure')
        ET.SubElement(structure, 'type').text = 'fa'
        automaton = ET.SubElement(structure, 'automaton')
        state_to_id = {name: str(i) for i, name in enumerate(self.states)}
        for name in self.states:
            state_tag = ET.SubElement(automaton, 'state', id=state_to_id[name], name=name)
            ET.SubElement(state_tag, 'x').text = str(100.0 + 50 * int(state_to_id[name]))
            ET.SubElement(state_tag, 'y').text = str(100.0)
            if name == self.initial_state: ET.SubElement(state_tag, 'initial')
            if name in self.final_states: ET.SubElement(state_tag, 'final')
        for (src, char), dests in self.transitions.items():
            for dest in dests:
                trans = ET.SubElement(automaton, 'transition')
                ET.SubElement(trans, 'from').text = state_to_id[src]
                ET.SubElement(trans, 'to').text = state_to_id[dest]
                read_tag = ET.SubElement(trans, 'read')
                if char != "λ": read_tag.text = str(char)
        ET.ElementTree(structure).write(path, encoding='utf-8', xml_declaration=True)