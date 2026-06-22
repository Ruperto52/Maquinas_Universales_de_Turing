import xml.etree.ElementTree as ET
import math
import tkinter as tk

class PushdownAutomaton:
    def __init__(self):
        self.states = []
        self.alphabet = set()
        self.stack_alphabet = set()
        self.transitions = []  # Lista de tuplas: (estado_actual, input, pop, estado_sig, push)
        self.initial_state = None
        self.final_states = []

    def load_from_jff(self, filepath):
        tree = ET.parse(filepath)
        root = tree.getroot()
        
        self.states = []
        self.final_states = []
        self.transitions = []
        
        for state in root.findall('.//state'):
            s_id = state.get('id')
            self.states.append(s_id)
            if state.find('initial') is not None:
                self.initial_state = s_id
            if state.find('final') is not None:
                self.final_states.append(s_id)
                
        for trans in root.findall('.//transition'):
            fro = trans.find('from').text
            to = trans.find('to').text
            read = trans.find('read').text or ""  # "" representa lambda/epsilon
            pop = trans.find('pop').text or ""
            push = trans.find('push').text or ""
            
            self.transitions.append((fro, read, pop, to, push))
            if read: self.alphabet.add(read)
            if pop: self.stack_alphabet.add(pop)
            for char in push: self.stack_alphabet.add(char)

    def save_to_jff(self, filepath):
        root = ET.Element("structure")
        type_elem = ET.SubElement(root, "type")
        type_elem.text = "pda"
        
        automaton = ET.SubElement(root, "automaton")
        
        # Agregamos los estados
        for s in self.states:
            state_elem = ET.SubElement(automaton, "state", id=str(s), name=f"q{s}")
            if s == self.initial_state:
                ET.SubElement(state_elem, "initial")
            if s in self.final_states:
                ET.SubElement(state_elem, "final")
                
        # Agregamos las transiciones
        for t in self.transitions:
            trans_elem = ET.SubElement(automaton, "transition")
            ET.SubElement(trans_elem, "from").text = t[0]
            ET.SubElement(trans_elem, "to").text = t[3]
            ET.SubElement(trans_elem, "read").text = t[1] if t[1] else ""
            ET.SubElement(trans_elem, "pop").text = t[2] if t[2] else ""
            ET.SubElement(trans_elem, "push").text = t[4] if t[4] else ""
            
        tree = ET.ElementTree(root)
        tree.write(filepath, encoding="utf-8", xml_declaration=True)

    def validate_string(self, input_string):
        """
        Simulación usando DFS para manejar el no-determinismo del PDA.
        Devuelve (Booleano_Aceptación, Traza_de_Ejecución)
        """
        stack = ['Z'] # Asumiendo Z como símbolo inicial de la pila estándar
        # path almacena: (cadena_restante, estado_actual, estado_de_la_pila, traza_histórica)
        paths = [(input_string, self.initial_state, stack, f"Inicio: q{self.initial_state}, Pila: {stack}")]
        
        while paths:
            current_str, current_state, current_stack, trace = paths.pop()
            
            # Criterio de aceptación: Consumió la cadena y está en estado final
            if current_str == "" and current_state in self.final_states:
                return True, trace + f"\n[ACEPTADO] Alcanzó estado final q{current_state} con pila {current_stack}"
                
            for trans in self.transitions:
                t_from, t_read, t_pop, t_to, t_push = trans
                
                if t_from == current_state:
                    # Validar coincidencia de lectura (lambda o símbolo exacto)
                    can_read = (t_read == "") or (current_str.startswith(t_read))
                    
                    # Validar coincidencia de pila (lambda o tope de pila exacto)
                    can_pop = (t_pop == "") or (len(current_stack) > 0 and current_stack[-1] == t_pop)
                    
                    if can_read and can_pop:
                        new_str = current_str[len(t_read):] if t_read else current_str
                        new_stack = current_stack.copy()
                        
                        if t_pop != "":
                            new_stack.pop()
                        
                        if t_push != "":
                            # Insertamos en orden inverso para que el primer carácter quede en el tope
                            for char in reversed(t_push):
                                new_stack.append(char)
                                
                        new_trace = trace + f"\n -> Lee '{t_read if t_read else 'λ'}', Pop '{t_pop}', Push '{t_push}' -> Estado: q{t_to}, Pila: {new_stack}"
                        paths.append((new_str, t_to, new_stack, new_trace))
                        
        return False, "[RECHAZADO] No se encontró una ruta de aceptación válida.\nÚltimo estado analizado:\n" + trace
    
    def draw_on_canvas(self, canvas):
        canvas.delete("all")
        if not self.states: return
        
        # Obtener dimensiones del canvas
        canvas.update_idletasks()
        width = canvas.winfo_width()
        height = canvas.winfo_height()
        if width <= 1: width = 800
        if height <= 1: height = 400
        
        center_x, center_y = width / 2, height / 2
        radius = min(width, height) / 3
        node_r = 22
        
        # 1. Posicionar estados en círculo
        pos = {}
        n = len(self.states)
        for i, state in enumerate(self.states):
            angle = 2 * math.pi * i / n - math.pi / 2
            x = center_x + radius * math.cos(angle)
            y = center_y + radius * math.sin(angle)
            pos[state] = (x, y)
            
        # 2. Agrupar y dibujar transiciones
        trans_dict = {}
        for t in self.transitions:
            fro, read, pop, to, push = t
            label = f"{read if read else 'λ'}, {pop if pop else 'λ'} ; {push if push else 'λ'}"
            pair = (fro, to)
            if pair not in trans_dict: trans_dict[pair] = []
            trans_dict[pair].append(label)
            
        for (fro, to), labels in trans_dict.items():
            label_str = "\n".join(labels)
            if fro not in pos or to not in pos: continue
            
            x1, y1 = pos[fro]
            if fro == to:
                # Bucle (Self-loop)
                canvas.create_oval(x1-20, y1-node_r-35, x1+20, y1-node_r, outline="#3b82f6", width=2)
                canvas.create_text(x1, y1-node_r-45, text=label_str, fill="#93c5fd", font=("Arial", 9))
            else:
                x2, y2 = pos[to]
                # Flecha entre nodos
                canvas.create_line(x1, y1, x2, y2, arrow=tk.LAST, fill="#3b82f6", width=2)
                mx, my = (x1 + x2)/2, (y1 + y2)/2
                canvas.create_text(mx, my-15, text=label_str, fill="#93c5fd", font=("Arial", 9))
                
        # 3. Dibujar los Nodos encima de las líneas
        for state, (x, y) in pos.items():
            bg_color = "#10b981" if state in self.final_states else "#1e293b"
            out_color = "#38bdf8" if state == self.initial_state else "white"
            out_width = 3 if state == self.initial_state else 1
            
            if state in self.final_states: # Doble círculo final
                canvas.create_oval(x-node_r-4, y-node_r-4, x+node_r+4, y+node_r+4, outline="#10b981", width=2)
                
            canvas.create_oval(x-node_r, y-node_r, x+node_r, y+node_r, fill=bg_color, outline=out_color, width=out_width)
            canvas.create_text(x, y, text=state, fill="white", font=("Arial", 11, "bold"))
            
            # Flecha de estado inicial
            if state == self.initial_state:
                canvas.create_line(x-node_r-30, y, x-node_r, y, arrow=tk.LAST, fill="#38bdf8", width=3)