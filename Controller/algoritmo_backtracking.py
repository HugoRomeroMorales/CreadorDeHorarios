import sys

SLOTS_POR_DIA = 6
horas = [
    "8:30-9:25",
    "9:25-10:20",
    "10:20-11:15",
    "11:45-12:20",
    "12:20-13:35",
    "13:35-14:30"
]
dias = [
    "Lunes",
    "Martes",
    "Miercoles",
    "Jueves",
    "Viernes"
]
grupos = [
    "1º DAM",
    "2º DAM"
]

class Prof:
    """
    Clase que representa a un profesor y sus restricciones.

    Atributos:
        _id (int): Identificador único del profesor.
        _disponibilidad (list[bool]): Lista de booleanos indicando disponibilidad por slot horario.
        _preferencia (list): Lista de preferencias (no utilizada en la lógica core actual).
        _nombre (str): Nombre del profesor.
        _modulo (str): Asignatura que imparte.
        _horas_maximas (int): Número máximo de horas que puede impartir.
        _horas_minimas (int): Número mínimo de horas (no utilizada en la lógica actual).
    """
    def __init__(self, id, disponibilidad, preferencia, nombre, modulo, horas_maximas, horas_minimas):
        self._id = id
        self._disponibilidad = disponibilidad  
        self._preferencia = preferencia        
        self._nombre = nombre
        self._modulo = modulo
        self._horas_maximas = horas_maximas
        self._horas_minimas = horas_minimas

    def get_id(self): return self._id
    def get_disponibilidad(self): return self._disponibilidad
    def get_nombre(self): return self._nombre
    def get_modulo(self): return self._modulo
    def get_horas_maximas(self): return self._horas_maximas


# --- CONFIGURACIÓN DE ESCENARIOS ---

# Definición de disponibilidades comunes
TodoElDia = [True, True, True, True, True, True]           
SoloMananas = [True, True, True, False, False, False]
SoloTardes = [False, False, False, True, True, True]


ESCENARIO_ACTIVO = 2 

lista_profesores = []

if ESCENARIO_ACTIVO == 1:
    print("--- CARGANDO ESCENARIO 1: FUNCIONAL (Sobra oferta de horas) ---")
    # Demanda: 60 horas (2 grupos * 30 slots).
    # Oferta: 18*3 + 12 + 10 = 76 horas. Hay margen de sobra.
    p1 = Prof(1, TodoElDia, [], "Juan (Mates)", "Matemáticas", 18, 0)
    p2 = Prof(2, TodoElDia, [], "Ana (Lengua)", "Lengua", 18, 0)
    p3 = Prof(3, TodoElDia, [], "Luis (Prog)", "Programación", 18, 0)
    p4 = Prof(4, TodoElDia, [], "Maria (BBDD)", "Base de Datos", 12, 0)
    p5 = Prof(5, TodoElDia, [], "Pedro (FOL)", "FOL", 10, 0)
    lista_profesores = [p1, p2, p3, p4, p5]

elif ESCENARIO_ACTIVO == 2:
    print("--- CARGANDO ESCENARIO 2: COMPLICADO (Restricciones horarias y horas justas) ---")
    # Demanda: 60 horas.
    # Oferta: 20 + 20 + 10 + 10 + 5 = 65 horas (muy justo).
    # Restricción fuerte: Ana solo puede mañanas, Luis solo tardes.
    # Esto fuerza conflictos si ambos grupos necesitan Lengua por la tarde.
    p1 = Prof(1, TodoElDia,   [], "Juan (Mates)", "Matemáticas", 20, 0) # Flexible
    p2 = Prof(2, SoloMananas, [], "Ana (Lengua)", "Lengua", 20, 0)      # Restricción fuerte
    p3 = Prof(3, SoloTardes,  [], "Luis (Prog)", "Programación", 10, 0) # Restricción fuerte
    p4 = Prof(4, TodoElDia,   [], "Maria (BBDD)", "Base de Datos", 10, 0)
    p5 = Prof(5, TodoElDia,   [], "Pedro (FOL)", "FOL", 5, 0)           # Pocas horas
    lista_profesores = [p1, p2, p3, p4, p5]


tareas_globales = []

for indice_dia, nombre_dia in enumerate(dias):
    for indice_hora, texto_hora in enumerate(horas):
        indice_slot_global = (indice_dia * SLOTS_POR_DIA) + indice_hora
        
        for indice_grupo, nombre_grupo in enumerate(grupos):
            tareas_globales.append({
                "indice_tarea": len(tareas_globales),
                "indice_slot_global": indice_slot_global,
                "nombre_dia": nombre_dia,
                "texto_hora": texto_hora,
                "indice_hora_diaria": indice_hora,
                "nombre_grupo": nombre_grupo
            })

horario = {}
mejor_horario_copia = {}

info_fallo = {
    "profundidad_maxima": -1,
    "razones": {} 
}

def contar_horas_asignadas(id_prof):
    """
    Cuenta el número total de horas que un profesor tiene asignadas en el horario actual.

    Argumentos:
        id_prof (int): El identificador del profesor.

    Devuelve:
        int: La cantidad de veces que el profesor aparece en el diccionario horario.
    """
    cuenta = 0
    for profe_asignado in horario.values():
        if profe_asignado.get_id() == id_prof:
            cuenta += 1
    return cuenta

def esta_ocupado_a_esta_hora(id_prof, slot_objetivo):
    """
    Verifica si un profesor ya está impartiendo clase en otro grupo a la misma hora global.

    Argumentos:
        id_prof (int): El identificador del profesor.
        slot_objetivo (int): El índice global del tiempo (0-29) que se quiere verificar.

    Devuelve:
        bool: True si el profesor ya tiene una asignación en ese slot de tiempo, False en caso contrario.
    """
    for indice_tarea, profe in horario.items():
        if profe.get_id() == id_prof:
            slot_ocupado = tareas_globales[indice_tarea]["indice_slot_global"]
            if slot_ocupado == slot_objetivo:
                return True
    return False

def crear_hueco(prof_id, slot_actual):
    """
    Analiza si asignar un profesor al slot actual generaría un hueco (gap) inválido en su horario personal del día.
    Un hueco se considera inválido si hay una o más horas libres entre dos clases asignadas en el mismo día.

    Argumentos:
        prof_id (int): El identificador del profesor.
        slot_actual (int): El índice global del tiempo (0-29).

    Devuelve:
        bool: True si la asignación crea un hueco no permitido, False en caso contrario.
    """
    indice_dia_actual = slot_actual // SLOTS_POR_DIA
    inicio_dia_indice = indice_dia_actual * SLOTS_POR_DIA
    fin_dia_indice = inicio_dia_indice + SLOTS_POR_DIA
    
    horas_asignadas_hoy = []
    
    for indice_tarea, profe in horario.items():
        if profe.get_id() == prof_id:
            tiempo_indice = tareas_globales[indice_tarea]["indice_slot_global"]
            if inicio_dia_indice <= tiempo_indice < fin_dia_indice:
                horas_asignadas_hoy.append(tiempo_indice % SLOTS_POR_DIA)
    
    hora_candidata = slot_actual % SLOTS_POR_DIA
    horas_asignadas_hoy.append(hora_candidata)
    
    horas_asignadas_hoy = list(set(horas_asignadas_hoy))
    horas_asignadas_hoy.sort()
    
    for k in range(len(horas_asignadas_hoy) - 1):
        actual = horas_asignadas_hoy[k]
        siguiente = horas_asignadas_hoy[k+1]
        if (siguiente - actual) > 1:
            return True 
    return False

def generar_horario(indice_tarea):
    """
    Función recursiva principal que implementa el algoritmo de Backtracking para asignar profesores.

    Argumentos:
        indice_tarea (int): El índice de la tarea actual en la lista `tareas_globales` que se intenta resolver.

    Variables Globales Modificadas:
        horario: Diccionario donde se guardan las asignaciones válidas.
        mejor_horario_copia: Snapshot del horario más completo alcanzado antes de un fallo.
        info_fallo: Registro de diagnóstico sobre por qué falló la rama más profunda.

    Devuelve:
        bool: True si se completa el horario satisfactoriamente, False si no se encuentra solución por esta rama.
    """
    global mejor_horario_copia

    if indice_tarea == len(tareas_globales):
        return True

    if indice_tarea > info_fallo["profundidad_maxima"]:
        info_fallo["profundidad_maxima"] = indice_tarea
        info_fallo["razones"] = {} 
        mejor_horario_copia = horario.copy()

    tarea = tareas_globales[indice_tarea]
    indice_hora_diaria = tarea["indice_hora_diaria"]
    slot_absoluto = tarea["indice_slot_global"]
   
    lista_profesores.sort(key=lambda p: p.get_horas_maximas() - contar_horas_asignadas(p.get_id()), reverse=True)

    for profesor in lista_profesores:
        nombre = profesor.get_nombre()
        pid = profesor.get_id()
        
        if not profesor.get_disponibilidad()[indice_hora_diaria]:
            if indice_tarea == info_fallo["profundidad_maxima"]: 
                info_fallo["razones"][nombre] = "No disponible"
            continue
            
        if esta_ocupado_a_esta_hora(pid, slot_absoluto):
            if indice_tarea == info_fallo["profundidad_maxima"]: 
                info_fallo["razones"][nombre] = "Ocupado con otro grupo"
            continue

        if contar_horas_asignadas(pid) >= profesor.get_horas_maximas():
            if indice_tarea == info_fallo["profundidad_maxima"]: 
                info_fallo["razones"][nombre] = "Tope de horas"
            continue

        if crear_hueco(pid, slot_absoluto):
            if indice_tarea == info_fallo["profundidad_maxima"]: 
                info_fallo["razones"][nombre] = "Genera hueco"
            continue

        horario[indice_tarea] = profesor
        
        if generar_horario(indice_tarea + 1):
            return True 
        
        del horario[indice_tarea]

    return False 

def imprimir_tabla_multi_grupo():
    """
    Imprime el horario generado en formato de tabla por consola, con columnas separadas por grupo.
    Muestra el módulo y el nombre del profesor para cada celda.
    """
    ancho_col = 25
    encabezado = f"{'DÍA/HORA':<15} |"
    for g in grupos:
        encabezado += f" {g:<{ancho_col}} |"
    
    print("\n" + "=" * len(encabezado))
    print(encabezado)
    print("=" * len(encabezado))

    dia_actual = ""
    
    paso = len(grupos)
    
    for i in range(0, len(tareas_globales), paso):
        slot_base = tareas_globales[i]
        dia = slot_base["nombre_dia"]
        hora = slot_base["texto_hora"]
        
        if dia != dia_actual:
            print("-" * len(encabezado))
            dia_actual = dia
            
        fila = f"{dia[:3]} {hora[:5]:<5}    |"
        
        for desplazamiento in range(paso):
            indice_tarea_actual = i + desplazamiento
            if indice_tarea_actual in horario:
                p = horario[indice_tarea_actual]
                texto = f"{p.get_modulo()} ({p.get_nombre().split()[0]})"
                
                if "CONFLICTO" in p.get_nombre():
                    texto = "!! CONFLICTO !!"
            else:
                texto = "---"
            
            fila += f" {texto:<{ancho_col}} |"
        
        print(fila)
        
        if slot_base["indice_hora_diaria"] == 2:
            separador = f"{'RECREO':<15} |" + (f" {'---':<{ancho_col}} |" * len(grupos))
            print("." * len(encabezado))
            print(separador)
            print("." * len(encabezado))

def imprimir_diagnostico():
    """
    Imprime información sobre el punto donde falló el algoritmo, mostrando el slot problemático
    y las razones por las que cada profesor fue descartado.
    """
    indice = info_fallo["profundidad_maxima"]
    if indice < len(tareas_globales):
        slot = tareas_globales[indice]
        print(f"\nFALLO en {slot['nombre_dia']} {slot['texto_hora']} - {slot['nombre_grupo']}")
        for nombre, razon in info_fallo["razones"].items():
            print(f" - {nombre:<15}: {razon}")

print("Generando horario para múltiples grupos...")
exito = generar_horario(0)

if exito:
    print("¡Horario Completo!")
    imprimir_tabla_multi_grupo()
else:
    print("Incompleto. Mostrando mejor intento:")
    horario = mejor_horario_copia
    indice = info_fallo["profundidad_maxima"]
    if indice < len(tareas_globales):
        horario[indice] = Prof(-1, [], [], "CONFLICTO", "ERROR", 0, 0)
        
    imprimir_tabla_multi_grupo()
    imprimir_diagnostico()