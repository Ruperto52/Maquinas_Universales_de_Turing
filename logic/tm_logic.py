import math
import xml.etree.ElementTree as ET

class TuringMachine:
    def __init__(self):
        self.states = []
        self.input_alphabet = []
        self.tape_alphabet = []
        self.initial_state = None
        self.blank_symbol = "B"
        self.final_states = []
        self.transitions = {} # (estado, simbolo_leido) -> (nuevo_estado, simbolo_escrito, direccion)
        
        # Estado dinámico de la simulación
        self.tape = {}
        self.head = 0
        self.current_state = None
        self.is_halted = False
        self.history = []

    def clear(self):
        self.__init__()

    def parse_transitions(self, raw_text):
        self.transitions = {}
        lines = raw_text.strip().split('\n')
        for line in lines:
            if not line.strip() or line.startswith('#'): continue
            try:
                # Formato: q0, a ; q1, b, R
                left, right = line.split(';')
                q_in, sym_in = [x.strip() for x in left.split(',')]
                q_out, sym_out, move = [x.strip() for x in right.split(',')]
                self.transitions[(q_in, sym_in)] = (q_out, sym_out, move.upper())
            except Exception as e:
                print(f"Error parseando transición: {line}. Detalle: {e}")

    def load_from_jff(self, filepath):
        """Lee un archivo .jff de Máquina de Turing y extrae sus componentes."""
        self.clear()
        tree = ET.parse(filepath)
        root = tree.getroot()
        id_map = {}
        
        # 1. Parsear estados
        for s in root.findall('.//state'):
            name = s.get('name')
            id_map[s.get('id')] = name
            self.states.append(name)
            if s.find('initial') is not None: self.initial_state = name
            if s.find('final') is not None: self.final_states.append(name)
            
        # 2. Parsear transiciones
        for t in root.findall('.//transition'):
            f = id_map[t.find('from').text]
            to = id_map[t.find('to').text]
            
            # En JFLAP el símbolo blanco a menudo viene como tag vacío o tag inexistente
            r_node = t.find('read')
            r = r_node.text if r_node is not None and r_node.text else self.blank_symbol
            
            w_node = t.find('write')
            w = w_node.text if w_node is not None and w_node.text else self.blank_symbol
            
            m_node = t.find('move')
            m = m_node.text if m_node is not None and m_node.text else "R"
            
            self.transitions[(f, r)] = (to, w, m)
            
            # Registrar al alfabeto de cinta dinámicamente
            if r != self.blank_symbol and r not in self.tape_alphabet: self.tape_alphabet.append(r)
            if w != self.blank_symbol and w not in self.tape_alphabet: self.tape_alphabet.append(w)

    def load_from_encoded_txt(self, filepath):
        """Lee un archivo .txt con la codificación binaria de una MT y su cadena."""
        self.clear()
        with open(filepath, 'r') as f:
            encoded_str = f.read().strip()
            
        # Limpiar espacios o saltos de línea accidentales
        encoded_str = encoded_str.replace(" ", "").replace("\n", "")
        
        # Mapeos basados en la regla de codificación (1 -> '0', 2 -> '1', 3 -> 'B')
        symbol_map = {1: "0", 2: "1", 3: "B"}
        dir_map = {1: "L", 2: "R"}
        
        self.tape_alphabet = ["0", "1", "B"]
        self.blank_symbol = "B"
        states_set = set()
        self.decoded_string = "" # Guardará la cadena si existe
        
        # Separar la Máquina de la Cadena usando '000'
        parts_000 = encoded_str.split("000")
        tm_raw = parts_000[0]
        cadena_raw = parts_000[1] if len(parts_000) > 1 else ""
        
        # 1. DECODIFICAR MÁQUINA (Transiciones separadas por '00')
        transitions_raw = tm_raw.split("00")
        for t_raw in transitions_raw:
            if not t_raw: continue
            
            parts = t_raw.split("0")
            if len(parts) != 5:
                print(f"Advertencia: Transición malformada ignorada -> {t_raw}")
                continue
                
            i, j, k, l, m = [len(p) for p in parts]
            
            q_in = f"q{i}"
            sym_in = symbol_map.get(j, f"sym{j}")
            q_out = f"q{k}"
            sym_out = symbol_map.get(l, f"sym{l}")
            move = dir_map.get(m, "R")
            
            states_set.update([q_in, q_out])
            if sym_in not in self.tape_alphabet: self.tape_alphabet.append(sym_in)
            if sym_out not in self.tape_alphabet: self.tape_alphabet.append(sym_out)
            
            self.transitions[(q_in, sym_in)] = (q_out, sym_out, move)
            
        self.states = sorted(list(states_set), key=lambda x: int(x[1:]))
        if self.states: self.initial_state = "q1" 

        # 2. DECODIFICAR CADENA (Símbolos separados por '0')
        if cadena_raw:
            decoded_chars = []
            for sym_raw in cadena_raw.split("0"):
                if sym_raw: # Ignorar vacíos
                    num_ones = len(sym_raw)
                    decoded_chars.append(symbol_map.get(num_ones, ""))
            self.decoded_string = "".join(decoded_chars)

    def load_string(self, string):
        self.tape = {i: char for i, char in enumerate(string)}
        if not string:
            self.tape = {0: self.blank_symbol}
        self.head = 0
        self.current_state = self.initial_state
        self.is_halted = False
        self.history = []
        self.record_state("Inicio")

    def get_tape_symbol(self, pos):
        return self.tape.get(pos, self.blank_symbol)

    def record_state(self, action):
        self.history.append({
            'action': action,
            'state': self.current_state,
            'head': self.head
        })

    def step(self):
        if self.is_halted:
            return False, "La máquina ya está detenida."
            
        sym_in = self.get_tape_symbol(self.head)
        
        if (self.current_state, sym_in) not in self.transitions:
            self.is_halted = True
            is_accepted = self.current_state in self.final_states
            msg = f"ACEPTADA (Estado final {self.current_state})" if is_accepted else f"RECHAZADA (Sin transición para {self.current_state}, {sym_in})"
            return False, msg

        new_state, sym_out, move = self.transitions[(self.current_state, sym_in)]
        
        # Ejecutar acción
        self.tape[self.head] = sym_out
        self.current_state = new_state
        
        if move == 'R': self.head += 1
        elif move == 'L': self.head -= 1
            
        action_msg = f"Lee '{sym_in}' -> Escribe '{sym_out}', Mueve '{move}', Va a '{new_state}'"
        self.record_state(action_msg)
        return True, action_msg

    def draw_tape(self, canvas):
        canvas.delete("all")
        canvas.update_idletasks()
        w, h = canvas.winfo_width(), canvas.winfo_height()
        if w <= 1 or h <= 1: w, h = 800, 150
        
        cell_w = 50
        # Efecto "cámara": centramos la vista en el cabezal mostrando celdas a los lados
        view_radius = int((w / cell_w) / 2) 
        min_i = self.head - view_radius + 1
        max_i = self.head + view_radius - 1
        
        start_x = w/2 - ((max_i - min_i + 1) * cell_w)/2
        y = h / 2

        # Dibujar celdas de la cinta
        for i in range(min_i, max_i + 1):
            x = start_x + (i - min_i) * cell_w
            sym = self.get_tape_symbol(i)
            
            bg_color = "#06b6d4" if i == self.head else "#1e293b"
            fg_color = "black" if i == self.head else "white"
            
            # Celda
            canvas.create_rectangle(x, y-25, x+cell_w, y+25, fill=bg_color, outline="#334155", width=2)
            canvas.create_text(x+cell_w/2, y, text=sym, fill=fg_color, font=("Consolas", 18, "bold"))
            
            # Puntero del cabezal
            if i == self.head:
                canvas.create_polygon(x+cell_w/2, y+35, x+cell_w/2-10, y+50, x+cell_w/2+10, y+50, fill="#ef4444")
                canvas.create_text(x+cell_w/2, y+65, text=f"q: {self.current_state}", fill="white", font=("Arial", 12, "bold"))

    def draw_automaton(self, canvas):
        canvas.delete("all")
        canvas.update_idletasks()
        w, h = canvas.winfo_width(), canvas.winfo_height()
        if w <= 1 or h <= 1: w, h = 600, 400 
        cx, cy = w/2, h/2
        r, dist = 25, min(cx, cy) * 0.7
        if not self.states: return
        pos = {s: (cx + dist*math.cos(2*math.pi*i/len(self.states)), 
                   cy + dist*math.sin(2*math.pi*i/len(self.states))) 
               for i, s in enumerate(self.states)}

        edge_labels = {}
        for (f, sym_in), (t, sym_out, mov) in self.transitions.items():
            if (f, t) not in edge_labels: edge_labels[(f, t)] = []
            edge_labels[(f, t)].append(f"{sym_in}/{sym_out},{mov}")

        for (f, t), chars in edge_labels.items():
            x1, y1 = pos[f]; x2, y2 = pos[t]
            color = "#06b6d4"
            label = " | ".join(chars)
            if f == t:
                canvas.create_oval(x1-20, y1-60, x1+20, y1-20, outline=color)
                canvas.create_text(x1, y1-70, text=label, fill=color)
            else:
                canvas.create_line(x1, y1, x2, y2, arrow="last", fill="#94a3b8")
                canvas.create_text((x1+x2)/2, (y1+y2)/2 - 15, text=label, fill=color, font=("Arial", 9, "bold"))

        for s in self.states:
            x, y = pos[s]
            # Estado actual en verde, inicial en amarillo, normales en cian
            col = "#10b981" if s == self.current_state else ("#fbbf24" if s == self.initial_state else "#06b6d4")
            
            canvas.create_oval(x-r, y-r, x+r, y+r, fill="#0f172a", outline=col, width=3)
            if s in self.final_states: canvas.create_oval(x-r+5, y-r+5, x+r-5, y+r-5, outline=col)
            canvas.create_text(x, y, text=s, fill="white", font=("Arial", 10, "bold"))