import xml.etree.ElementTree as ET
import copy

class Grammar:
    def __init__(self):
        self.productions = []  # Almacena elementos en formato [izq, der]
        self.start_symbol = None

    def clear(self):
        self.productions = []
        self.start_symbol = None

    def load_from_text(self, text):
        self.clear()
        lines = text.strip().split('\n')
        for line in lines:
            if '->' in line:
                left, right_side = line.split('->')
                left = left.strip()
                if not self.start_symbol:
                    self.start_symbol = left
                for prod in right_side.split('|'):
                    self.productions.append([left, prod.strip()])

    def get_grammar_string(self, prods=None):
        target = prods if prods is not None else self.productions
        if not target:
            return "Ø"
        grouped = {}
        for left, right in target:
            if left not in grouped:
                grouped[left] = []
            grouped[left].append(right if (right and right not in ["λ", "ε", ""]) else "λ")
        return "\n".join([f"{l} -> {' | '.join(r)}" for l, r in grouped.items()])

    def to_chomsky(self):
        """
        Algoritmo robusto de conversión a la Forma Normal de Chomsky (FNC).
        Muestra paso a paso todo el proceso en la bitácora.
        """
        history = []
        
        # ==========================================
        # PASO 1: NUEVO SÍMBOLO INICIAL
        # ==========================================
        original_start = self.start_symbol
        new_start = original_start + "'"
        current_prods = [[new_start, original_start]] + copy.deepcopy(self.productions)
        history.append(f"1. NUEVO INICIO:\nSe agrega {new_start} para evitar recursividad al inicio.\n" + self.get_grammar_string(current_prods))

        # ==========================================
        # PASO 2: ELIMINACIÓN DE PRODUCCIONES VACÍAS (λ)
        # ==========================================
        # Encontrar el conjunto de variables anulables
        nullable = {p[0] for p in current_prods if p[1] in ["λ", "ε", ""]}
        changed = True
        while changed:
            changed = False
            for left, right in current_prods:
                if left not in nullable and all(char in nullable for char in right if char.isupper()):
                    nullable.add(left)
                    changed = True

        new_prods = []
        for left, right in current_prods:
            if right not in ["λ", "ε", ""]:
                new_prods.append([left, right])
                # Generar las combinaciones omitiendo los caracteres que son anulables
                for i, char in enumerate(right):
                    if char in nullable:
                        variant = right[:i] + right[i+1:]
                        if variant and [left, variant] not in new_prods:
                            new_prods.append([left, variant])
        current_prods = new_prods
        history.append("2. ELIMINACIÓN DE λ:\nSe generaron variantes por símbolos anulables.\n" + self.get_grammar_string(current_prods))

        # ==========================================
        # PASO 3: ELIMINACIÓN DE PRODUCCIONES UNITARIAS
        # ==========================================
        changed = True
        while changed:
            changed = False
            for i, (left, right) in enumerate(current_prods):
                # Es una producción unitaria clásica: variable única en la derecha (ej. A -> B)
                if len(right) == 1 and right.isupper():
                    target = right
                    current_prods.pop(i)
                    for l, r in current_prods:
                        if l == target and [left, r] not in current_prods:
                            current_prods.append([left, r])
                    changed = True
                    break
        history.append("3. ELIMINACIÓN DE UNITARIAS:\nSe sustituyeron las reglas unitarias A -> B.\n" + self.get_grammar_string(current_prods))

        # ==========================================
        # PASO 4: REEMPLAZO DE TERMINALES Y BINARIZACIÓN
        # ==========================================
        # Paso 4a: Reemplazar terminales en reglas de longitud >= 2 por variables auxiliares T_X
        term_map = {}
        processed_prods = []
        for left, right in current_prods:
            if len(right) == 1:
                # Reglas del tipo A -> a ya están correctas para FNC, se preservan intactas
                processed_prods.append([left, right])
            else:
                new_right = []
                for char in right:
                    if char.islower() or not char.isupper():  # Es un terminal
                        t_var = f"T{char.upper()}"
                        term_map[char] = t_var
                        new_right.append(t_var)
                    else:
                        new_right.append(char)
                processed_prods.append([left, new_right])

        # Paso 4b: Binarizar únicamente los cuerpos que contengan 3 o más variables
        bin_prods = []
        counter = 1
        for left, right in processed_prods:
            # Si right es una lista de elementos (ej: ['Ta', 'A']), evaluamos su longitud
            if len(right) <= 2:
                # Si mide 1 o 2 variables (ej: ['Ta', 'A']), ya cumple FNC
                bin_prods.append([left, "".join(right)])
            else:
                # Si mide 3 o más variables (ej: ['A', 'B', 'C']), las agrupamos secuencialmente con variables C_x
                last_var = left
                for i in range(len(right) - 2):
                    new_v = f"C{counter}"
                    counter += 1
                    bin_prods.append([last_var, right[i] + new_v])
                    last_var = new_v
                bin_prods.append([last_var, right[-2] + right[-1]])

        # Agregar al final de la gramática las reglas de mapeo de terminales (ej: Ta -> a)
        for char, t_var in term_map.items():
            if [t_var, char] not in bin_prods:
                bin_prods.append([t_var, char])

        current_prods = bin_prods
        self.productions = current_prods
        history.append("4. RESULTADO FINAL (FNC):\nProducciones ajustadas a la forma estricta A -> BC o A -> a.\n" + self.get_grammar_string(current_prods))

        return "\n\n---\n\n".join(history)

    def save_to_jff(self, path):
        """
        Exporta las producciones en formato XML compatible con la pestaña 'Grammar' de JFLAP.
        """
        structure = ET.Element('structure')
        ET.SubElement(structure, 'type').text = 'grammar'
        for left, right in self.productions:
            prod_tag = ET.SubElement(structure, 'production')
            ET.SubElement(prod_tag, 'left').text = left
            right_tag = ET.SubElement(prod_tag, 'right')
            if right not in ["λ", "ε", ""]:
                right_tag.text = right
            else:
                right_tag.text = ""  # JFLAP requiere etiqueta vacía para lambdas
        tree = ET.ElementTree(structure)
        tree.write(path, encoding='utf-8', xml_declaration=True)