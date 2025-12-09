import sys

from Controller.Controller_db import (
    get_profesor,
    get_modulo,
    get_preferencias_por_profesor
)

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

grupos = []

class Prof:
    """
    Clase que representa a un profesor y sus restricciones.
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

def convertir_preferencias_a_disponibilidad(id_prof):
    """
    Consulta las preferencias/restricciones en la BD y genera la lista de 6 booleanos.
    Por defecto devuelve 'Disponible todo el día' si no hay datos.
    """
    disponibilidad = [True] * SLOTS_POR_DIA
    
    return disponibilidad

def cargar_profesores_desde_bd():
    """
    Recupera los profesores de la base de datos usando el Controller
    y crea la lista de objetos 'Prof'.
    """
    lista_objs = []
    
    profesores_db = get_profesor() 
    
    print(f"--- Cargando {len(profesores_db)} profesores desde la Base de Datos ---")

    for p_data in profesores_db:
        
        p_id = p_data[0]
        p_nombre = p_data[1]
        
        p_modulo = "Módulo Genérico"
        
        p_horas_max = p_data[4] if len(p_data) > 4 else 20
        p_horas_min = 0

        p_disponibilidad = convertir_preferencias_a_disponibilidad(p_id)
        
        nuevo_prof = Prof(
            id=p_id,
            disponibilidad=p_disponibilidad,
            preferencia=[],
            nombre=p_nombre,
            modulo=p_modulo,
            horas_maximas=p_horas_max,
            horas_minimas=p_horas_min
        )
        
        lista_objs.append(nuevo_prof)
        print(f" -> Prof cargado: {nuevo_prof.get_nombre()}")
        
    return lista_objs

def cargar_grupos_desde_bd():
    """
    Recupera los grupos (clases) de la base de datos usando get_modulo.
    """
    lista_nombres_grupos = []
    
    try:
        grupos_db = get_modulo() 
        print(f"--- Cargando {len(grupos_db)} clases/grupos desde la Base de Datos ---")
        
        for g_data in grupos_db:
            g_nombre = g_data[1] 
            lista_nombres_grupos.append(g_nombre)
            print(f" -> Clase cargada: {g_nombre}")
            
    except Exception as e:
        print(f"Error al cargar clases desde BD: {e}")
        lista_nombres_grupos = ["Clase A (Fallback)", "Clase B (Fallback)"]
        
    return lista_nombres_grupos

try:
    lista_profesores = cargar_profesores_desde_bd()
except Exception as e:
    print(f"Error al conectar con la BD o procesar profesores: {e}")
    lista_profesores = [] 

grupos = cargar_grupos_desde_bd()

if not grupos:
    grupos = ["Grupo Único"]


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
    """
    cuenta = 0
    for profe_asignado in horario.values():
        if profe_asignado.get_id() == id_prof:
            cuenta += 1
    return cuenta

def esta_ocupado_a_esta_hora(id_prof, slot_objetivo):
    """
    Verifica si un profesor ya está impartiendo clase en otro grupo a la misma hora global.
    """
    for indice_tarea, profe in horario.items():
        if profe.get_id() == id_prof:
            slot_ocupado = tareas_globales[indice_tarea]["indice_slot_global"]
            if slot_ocupado == slot_objetivo:
                return True
    return False

def crear_hueco(prof_id, slot_actual):
    """
    Analiza si asignar un profesor al slot actual generaría un hueco (gap) inválido.
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
    Algoritmo de Backtracking recursivo.
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
    Imprime el horario en formato tabla.
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
                    texto = "CONFLICTO"
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
    indice = info_fallo["profundidad_maxima"]
    if indice < len(tareas_globales):
        slot = tareas_globales[indice]
        print(f"\nFALLO en {slot['nombre_dia']} {slot['texto_hora']} - {slot['nombre_grupo']}")
        for nombre, razon in info_fallo["razones"].items():
            print(f" - {nombre:<15}: {razon}")

print("Generando horario utilizando datos de Base de Datos...")
exito = generar_horario(0)

if exito:
    print("Horario Completo Generado")
    imprimir_tabla_multi_grupo()
else:
    print("Incompleto. Mostrando mejor intento:")
    horario = mejor_horario_copia
    indice = info_fallo["profundidad_maxima"]
    if indice < len(tareas_globales):
        horario[indice] = Prof(-1, [], [], "CONFLICTO", "ERROR", 0, 0)
        
    imprimir_tabla_multi_grupo()
    imprimir_diagnostico()