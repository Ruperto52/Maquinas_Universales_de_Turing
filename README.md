# Maquinas_Universales_de_Turing
Se hace el desarrollo en conjunto con mi compañera Venegas Martinez Maria Jose, del ejercicio 3 acerca del desarrollo y la ampliacion del software desarrollado a lo largo del semestre con las maquinas de turing universales

## Información de los Integrantes
* **Institución:** Instituto Politécnico Nacional (IPN)
* **Escuela:** Escuela Superior de Cómputo (ESCOM) 
* **Unidad de Aprendizaje:** Teoría de la Computación 
* **Programa Académico:** Ingeniería en Sistemas Computacionales / Plan 2020 
* **Grupo:** 4CM4
* **Alumnos:** 
   * Diego Ruperto Hernandez (Boleta: 2024630696)
   * Maria Jose Venegas Martinez (Boleta: 2024630831)

---

## Objetivo
En esta práctica se explorará la capacidad de las Máquinas de Turing para simular el comportamiento de otras Máquinas de Turing. Además, se implementará una Máquina de Turing Universal en el software interactivo desarrollado anteriormente. En concreto, al terminar la práctica deberás ser capaz de: (1) explicar qué hace que una máquina sea universal; (2) codificar una Máquina de Turing como una cadena de entrada; y (3) usar una Máquina de Turing Universal para ejecutar esa codificación.

## 1. Introduccion 
Este repositorio contiene el código fuente y el desarrollo correspondiente al **Ejercicio 3** de la práctica de laboratorio. El objetivo principal de este módulo es extender las capacidades de un software interactivo de autómatas para dotarlo de la lógica de una **Máquina de Turing Universal (MTU)**.

### Máquina de Turing Convencional vs. Máquina de Turing Universal

La distinción entre una Máquina de Turing (MT) convencional y una Máquina de Turing Universal (MTU) radica fundamentalmente en su arquitectura lógica y su grado de abstracción:

* **Máquina de Turing Convencional:** Es un dispositivo de propósito específico. Su estructura formal —definida por un conjunto rígido de estados y una función de transición $\delta$ fija— está "cableada" abstractamente para resolver un único problema o reconocer un lenguaje particular. Si se desea cambiar el algoritmo, se debe rediseñar por completo la máquina.
* **Máquina de Turing Universal:** Es un sistema de propósito general que actúa como un intérprete o meta-algoritmo. En lugar de ejecutar una lógica estática, una MTU es capaz de simular a *cualquier* otra Máquina de Turing arbitraria ($M$). Para lograrlo, la MTU no altera sus propias transiciones; en su lugar, recibe como datos en su cinta tanto la descripción formal codificada de la máquina a emular ($M$) como la cadena de entrada original ($w$) que dicha máquina debe procesar.

### Esquema de Codificación Basado en Unos y Ceros

Para que la MTU pueda interpretar la estructura de la máquina simulada, toda su definición matemática (estados, alfabeto, movimientos y transiciones) se mapea por completo a una cadena homogénea compuesta exclusivamente por **unos ($1$) y ceros ($0$)** . El motor de simulación de este proyecto procesa las transiciones utilizando bloques de unos consecutivos para los valores indexados, empleando el carácter `0` estrictamente como el delimitador y separador de control:

1. **Estados:** Cada estado $q_i$ se representa con una cantidad secuencial de unos relacionada con su índice (donde $q_0 = 1$, $q_1 = 11$, $q_2 = 111$, etc.) .
2. **Alfabeto de la Cinta:** Los símbolos se indexan de manera homóloga mediante bloques de unos consecutivos (por ejemplo, el símbolo $0 = 1$, el símbolo $1 = 11$ y el blanco o variables de control se expanden incrementalmente como $111$, $1111$, etc.)  .
3. **Direcciones de Movimiento:** Las acciones físicas del cabezal se digitalizan asignando un único uno a la izquierda ($L = 1$) y un par de unos a la derecha ($R = 11$) .
4. **Estructura de una Transición ($\delta$):** Una regla de tipo $\delta(q_i, a) = (q_j, b, D)$ se construye uniendo sus componentes mediante un único `0` como separador intermedio:
   $$\text{código}(q_i)0\text{código}(a)0\text{código}(q_j)0\text{código}(b)0\text{código}(D)$$
5. **Delimitación de la Máquina ($M$):** Para agrupar las transiciones que conforman al autómata completo, las reglas individuales se concatenan utilizando un doble cero (`00`) como divisor estructural, mientras que un triple cero (`000`) sirve como la frontera crítica que aísla la descripción completa de la máquina $M$ de su respectiva cadena de trabajo $w$ . El ordenamiento de estas reglas determina la existencia de múltiples combinaciones válidas ($n!$) para mapear una misma máquina en el sistema.

## Metodo para la decodificacion de la MTU (load_from_encoded_txt)

## 2. Arquitectura del Motor Computacional (`TuringMachine`)

La clase `TuringMachine` gestiona de forma aislada la lógica matemática del autómata, la carga y parsing de datos, y el ciclo de ejecución de la simulación. A continuación, se desglosan en detalle sus componentes críticos:

### 2.1. Inicialización y Estado Dinámico
Este bloque define la estructura base donde se almacenan las quintuplas lógicas del autómata, así como los elementos necesarios para rastrear el estado físico de la simulación paso a paso.

```python
def __init__(self):
    self.states = []
    self.input_alphabet = []
    self.tape_alphabet = []
    self.initial_state = None
    self.blank_symbol = "B"
    self.final_states = []
    self.transitions = {} # Mapeo: (estado, simbolo_leido) -> (nuevo_estado, simbolo_escrito, direccion)
    
    # Estado dinámico de la simulación
    self.tape = {}
    self.head = 0
    self.current_state = None
    self.is_halted = False
    self.history = []
```
Explicación de este Algoritmo: 
* Definición Estática: Modela el autómata mediante listas y diccionarios nativos. El diccionario self.transitions utiliza llaves indexadas por tuplas (estado, símbolo) para garantizar búsquedas en tiempo constante $O(1)$.
* Control de Memoria Dinámica: La cinta (self.tape) se modela mediante un diccionario en lugar de una lista indexada. Esto permite emular una cinta infinita en ambas direcciones sin necesidad de reestructurar arreglos en memoria, asociando posiciones enteras negativas o positivas directamente con los símbolos correspondientes.


# 2.2. Aislamiento y Separación de Bloques de la MTU
Este fragmento dentro de la decodificación se encarga de segmentar la cadena binaria utilizando los delimitadores de control estructurados.

```Python
# Segmentación y limpieza inicial de la cadena binaria
encoded_str = encoded_str.replace(" ", "").replace("\n", "")

# Separar la Máquina de la Cadena usando la frontera crítica '000'
parts_000 = encoded_str.split("000")
tm_raw = parts_000[0]
cadena_raw = parts_000[1] if len(parts_000) > 1 else ""

# Segmentación de transiciones individuales mediante el delimitador '00'
transitions_raw = tm_raw.split("00")
```

Explicación de este Algoritmo:
* Frontera de Datos (000): Divide el flujo binario de entrada para aislar el "software" (las transiciones de la máquina a simular) del "input" (la palabra de trabajo $w$).
* Extracción de Instrucciones (00): Genera sub-bloques de ejecución independientes. Cada cadena resultante representa una única instrucción $\delta$, la cual será procesada de manera secuencial por el intérprete unitario.

# 2.3. Decodificación Unaria de TransicionesUna vez separadas las instrucciones
Este fragmento procesa cada bloque individual para mapear los conteos de unos (1) hacia la lógica interna de transiciones de Python.

```Python
for t_raw in transitions_raw:
    if not t_raw: continue
    
    parts = t_raw.split("0")
    if len(parts) != 5: continue
        
    # El número de unos determina el índice del componente matemático
    i, j, k, l, m = [len(p) for p in parts]
    
    q_in = f"q{i}"
    sym_in = symbol_map.get(j, f"sym{j}")
    q_out = f"q{k}"
    sym_out = symbol_map.get(l, f"sym{l}")
    move = dir_map.get(m, "R")
    
    states_set.update([q_in, q_out])
    self.transitions[(q_in, sym_in)] = (q_out, sym_out, move)
```
Explicación de este Algoritmo:
* Conteo de Unos por Posición: Divide el sub-bloque usando el separador lógico 0. Al evaluar len(p), transforma la codificación unaria del archivo de texto en variables enteras con significado conceptual.
* Mapeo de Control: Traduce enteros a identificadores de texto plano compatibles con la clase (ej. 3 unos en la posición del símbolo se transforman en "B", 1 uno en la dirección se traduce como "L"). Al finalizar, inyecta la regla decodificada en el diccionario global de ejecución.

# 2.4. Decodificación Dinámica de la Cadena de Entrada
Este segmento interpreta la sección posterior al delimitador triple cero para montar los caracteres válidos sobre la estructura lógica del visualizador.

```Python
if cadena_raw:
    decoded_chars = []
    for sym_raw in cadena_raw.split("0"):
        if sym_raw:
            num_ones = len(sym_raw)
            decoded_chars.append(symbol_map.get(num_ones, ""))
    self.decoded_string = "".join(decoded_chars)
```
Explicación de este Algoritmo:
* Procesamiento de Símbolos: Recorre los bloques unarios de la palabra de trabajo separados por ceros. Cada ráfaga de unos es traducida mediante un diccionario estático para reconstruir los caracteres primitivos (0, 1 o B). El resultado se empaqueta en una sola cadena que se transfiere directamente a la interfaz de usuario.

# 2.5. Validación y Parada Computacional (Halt)
Este bloque lógico dentro de cada paso elemental determina si el procesamiento debe continuar o si la simulación ha finalizado de forma definitiva.

```Python
sym_in = self.get_tape_symbol(self.head)

# Validación de existencia de la regla de transición
if (self.current_state, sym_in) not in self.transitions:
    self.is_halted = True
    is_accepted = self.current_state in self.final_states
    msg = f"ACEPTADA (Estado {self.current_state})" if is_accepted else f"RECHAZADA (Sin transición para {self.current_state}, {sym_in})"
    return False, msg
```
Explicación de este Algoritmo:
* Recuperación de Símbolo: Consulta la posición actual del cabezal físico mediante un método seguro que intercepta celdas vacías y retorna el Blanco por defecto.
* Criterio de Parada (Halt): Modela el comportamiento de parada clásico de una Máquina de Turing. Si la configuración actual carece de una directiva de movimiento, detiene el reloj lúdico (self.is_halted = True) y discrimina el resultado validando si el estado final se encuentra dentro del conjunto de estados de aceptación preconfigurados.

# 2.6. Mutación del Estado Físico y Desplazamiento Si la regla es válida
Este segmento altera físicamente los valores de la cinta virtual y redefine las coordenadas del puntero.

```Python
new_state, sym_out, move = self.transitions[(self.current_state, sym_in)]

# Ejecución de escritura y actualización de control
self.tape[self.head] = sym_out
self.current_state = new_state

# Control del movimiento del cabezal
if move == 'R': self.head += 1
elif move == 'L': self.head -= 1
    
action_msg = f"Lee '{sym_in}' -> Escribe '{sym_out}', Mueve '{move}', Va a '{new_state}'"
self.record_state(action_msg)
return True, action_msg
```
Explicación de este Algoritmo:
* Mutación de Cinta: Sobrescribe el símbolo en la posición del cabezal por la nueva entidad calculada sym_out y transiciona el puntero de control de estado.
* Ajuste de Coordenadas Físicas: Altera aritméticamente el valor numérico de self.head. Un movimiento "R" incrementa la coordenada en una unidad, permitiendo el renderizado dinámico hacia la derecha, mientras que un movimiento "L" la decrementa.

# 3. Arquitectura del Entorno Gráfico (AppTercerParcial)
La clase AppTercerParcial define el entorno interactivo construyendo los componentes visuales de control y renderizado mediante Tkinter.

# 3.1. Inicialización y Particionado Visual (Split-Frame)
Configura la ventana principal y segmenta el espacio interactivo utilizando contenedores distribuidos de forma asimétrica.

```Python
def __init__(self, root):
    self.root = root
    self.root.title("Tercer Parcial - Máquina de Turing Universal")
    self.root.geometry("1400x950")
    self.root.configure(bg="#0f172a")
    
    self.tm_logic = TuringMachine()
    self.t_accent = "#06b6d4"

    # Título Principal
    tk.Label(self.root, text="MÁQUINA DE TURING UNIVERSAL", bg="#0f172a", fg=self.t_accent, font=("Arial", 22, "bold")).pack(pady=15)

    # Contenedor Principal Split
    main_f = tk.Frame(self.root, bg="#1e293b")
    main_f.pack(fill="both", expand=True, padx=20, pady=10)
```
Explicación de este Algoritmo:

* Estructura Base: Determina las dimensiones físicas (1400x950) y la estética visual oscura. Actúa como el lienzo raíz que aloja las referencias cruzadas de eventos y enlaza las llamadas del motor lógico (self.tm_logic).

* Contenedor Maestro (main_f): Instancia un panel contenedor (Frame) que encapsula el área total de interacción, aislando los elementos del título para mitigar parpadeos o fallas de redibujado durante simulaciones rápidas.

# 3.2. Panel del Constructor y Carga de Archivos
Este bloque de código construye la barra lateral izquierda dedicada a la captura, parametrización e importación de la configuración de la máquina de manera textual o mediante archivos externos.

```Python
# === PANEL IZQUIERDO: CONSTRUCTOR ===
p_left = tk.Frame(main_f, bg="#1e293b", width=350)
p_left.pack(side="left", fill="y", padx=(0, 15))
p_left.pack_propagate(False)

self.c_tm_in = {}
etiquetas = [
    ("Estados Q (ej: q0,q1):", "q"), 
    ("Alf. Cinta Γ (ej: a,b,B):", "g"), 
    ("Estado Inicial:", "i"), 
    ("Estados Finales F:", "f")
]

for txt, key in etiquetas:
    tk.Label(p_left, text=txt, bg="#1e293b", fg=self.t_accent, font=("bold", 10)).pack(anchor="w")
    e = tk.Entry(p_left, bg="#0f172a", fg="white", insertbackground="white", relief="flat", font=("Consolas", 11))
    e.pack(fill="x", pady=5)
    self.c_tm_in[key] = e
```
Explicación de este Algoritmo:

* Control de Propagación: El uso de p_left.pack_propagate(False) fija estrictamente el ancho del panel a 350 píxeles, previniendo que los componentes internos colapsen o alteren el tamaño de la ventana gráfica al importar textos extensos.

* Mapeo Automatizado: Utiliza un bucle iterativo para instanciar campos de texto de manera dinámica, almacenando las referencias directas dentro del diccionario indexado self.c_tm_in para simplificar la extracción de datos en métodos subsecuentes.

# 3.3. Controles de Operación y Simulación Animada
Configura la barra de herramientas superior del panel derecho, vinculando las acciones físicas del usuario con la ejecución paso a paso o automatizada de la MTU.

```Python
# Controles de Simulación del Panel Derecho
ctrl_f = tk.Frame(p_right, bg="#0f172a", pady=10)
ctrl_f.pack(fill="x")

self.ent_tm_cadena = tk.Entry(ctrl_f, font=("Consolas", 14), bg="#1e293b", fg="white", relief="flat", width=25)
self.ent_tm_cadena.pack(side="left", padx=10)

tk.Button(ctrl_f, text="CARGAR EN CINTA", command=self.load_string, bg="#3b82f6", fg="white", font=("bold", 10), padx=10).pack(side="left", padx=5)
tk.Button(ctrl_f, text="▶ PASO A PASO", command=self.step_tm, bg="#10b981", fg="white", font=("bold", 10), padx=10).pack(side="left", padx=5)
tk.Button(ctrl_f, text="▶▶ EJECUTAR TODO", command=self.run_all_tm, bg="#f59e0b", fg="white", font=("bold", 10), padx=10).pack(side="left", padx=5)
```
Explicación de este Algoritmo:

* Consola de Control: Dispone los componentes interactivos horizontalmente utilizando la propiedad side="left". Cada botón está enlazado mediante la directiva command hacia métodos disparadores. El campo self.ent_tm_cadena sirve como el búfer de entrada directo de la palabra a evaluar en el autómata.

# 3.4. Lienzos de Renderizado Gráfico (Canvas Síncronos)
Instancia los dos espacios vectoriales independientes dedicados a dibujar en tiempo real la cinta infinita y el diagrama de estados.

```Python
# Cinta Canvas
self.can_tm_tape = tk.Canvas(p_right, bg="#020617", height=150, highlightthickness=1, highlightbackground=self.t_accent)
self.can_tm_tape.pack(fill="x", pady=5)

# Automata Canvas
self.can_tm_graph = tk.Canvas(p_right, bg="#020617", highlightthickness=1, highlightbackground=self.t_accent)
self.can_tm_graph.pack(fill="both", expand=True, pady=5)

# Monitor de Estado Informativo
self.lbl_tm_status = tk.Label(p_right, text="Estado: Esperando construcción...", bg="#0f172a", fg="white", font=("Arial", 12, "bold"))
self.lbl_tm_status.pack(pady=10)
```
Explicación de este Algoritmo:

* Áreas Vectoriales (Canvas): Define zonas aisladas con aceleración gráfica elemental por software. El canvas de la cinta posee una altura fija (150px) ideal para el desplazamiento de las celdas, mientras que el canvas del autómata utiliza fill="both" para expandir dinámicamente el grafo de estados según la resolución del monitor del usuario.

# 3.5. Ciclo de Animación Recursivo Asíncrono
Este fragmento controla la automatización continua de la máquina mediante llamadas diferidas por hardware, evitando congelar la interfaz de usuario.

```Python
def run_all_tm(self):
    success, msg = self.tm_logic.step()
    self.update_visuals()
    
    if success:
        self.lbl_tm_status.config(text=msg, fg="#f59e0b")
        # Temporizador asíncrono recursivo (400 milisegundos de delay)
        self.root.after(400, self.run_all_tm) 
    else:
        color = "#10b981" if "ACEPTADA" in msg else "#ef4444"
        self.lbl_tm_status.config(text=f"FIN: {msg}", fg=color)
```
Explicación de este Algoritmo:

* Lógica No Bloqueante (after): En lugar de utilizar bucles tradicionales de control (while o for) con llamadas restrictivas como time.sleep(), el sistema utiliza el método interactivo self.root.after(400, ...). Esto agenda la ejecución del siguiente ciclo en la cola de eventos nativa de Tkinter, permitiendo que la interfaz siga respondiendo a clics de pausa o redibujado mientras la máquina corre de forma automática.

# Descripción de la Interfaz Gráfica del Módulo de Usuario

A continuación, se detalla el flujo visual y la organización de las dos ventanas principales que componen el entorno interactivo del sistema:

---

### 1. Pantalla de Selección de Módulo (Menú Principal)
Al iniciar la aplicación, se presenta una ventana de bienvenida con una interfaz simplificada y un fondo oscuro industrial. El componente central de esta pantalla consiste en una distribución vertical de tres botones de acceso directo para las distintas fases del curso:

* **Botón "PRIMER PARCIAL":** Reservado para los módulos de simulación iniciales del sistema.
* **Botón "SEGUNDO PARCIAL":** Dedicado a las arquitecturas de autómatas intermedias.
* **Botón "TERCER PARCIAL":** Se debe presionar este botón para inicializar y desplegar la interfaz extendida de la Máquina de Turing Universal (MTU).

---

### 2. Pantalla del Simulador de la Máquina de Turing Universal
Una vez seleccionado el módulo del tercer parcial, la aplicación transiciona hacia el entorno operativo principal. Este espacio de trabajo está optimizado mediante un diseño de doble panel (*split-frame*) asimétrico que divide las tareas del sistema:

* **Panel Izquierdo (Módulo de Configuración):** Reúne las herramientas de parametrización formal del autómata. Cuenta con casillas de texto alineadas para capturar manualmente los Estados ($Q$), el Alfabeto de la Cinta ($\Gamma$), el Estado Inicial y los Estados Finales ($F$). Incluye un editor de texto plano optimizado con tipografía monoespaciada para listar las funciones de transición $\delta$, y tres botones de comando inferiores para construir la máquina manualmente o realizar la importación automatizada de archivos en formatos externos `.jff` (JFLAP) y `.txt` (Codificado binario).
* **Panel Derecho (Módulo de Visualización y Control):** Aloja en la franja superior los campos de inserción de la palabra de trabajo ("Cadena Inicial") junto con los botones de control de la simulación (`CARGAR EN CINTA`, `▶ PASO A PASO` y `▶▶ EJECUTAR TODO`). La región central dispone de dos lienzos vectoriales síncronos: el canvas superior ("CINTA INFINITA") renderiza las celdas de memoria dinámicas y la posición del cabezal, mientras que el canvas inferior ("DIAGRAMA DE ESTADOS") dibuja en tiempo real el grafo dirigible de la máquina simulada. La base del panel integra un monitor de texto que reporta el estado actual y la última acción computacional ejecutada.
