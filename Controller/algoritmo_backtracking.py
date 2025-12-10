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
 
# Variables globales para el algoritmo
grupos = []
lista_profesores = []
tareas_globales = []
horario = {}
mejor_horario_copia = {}
info_fallo = {
    "profundidad_maxima": -1,
    "razones": {}
}

MAX_NODOS = 30000  
nodos_visitados = 0
 
class Prof:
    """
    Clase que representa una ASIGNACIÓN DOCENTE (Profesor + Módulo + Grupo).
    Si un profesor da clase en dos grupos, habrá DOS objetos Prof distintos
    pero con el mismo ID (para controlar el solapamiento de horas).
    """
    def __init__(self, id, disponibilidad, preferencia, nombre, modulo, grupo, horas_maximas, horas_minimas, id_docente=None):
        self._id = id
        self._id_docente = id_docente or id
        self._disponibilidad = disponibilidad
        self._preferencia = preferencia
        self._nombre = nombre
        self._modulo = modulo
        self._grupo = grupo
        self._horas_maximas = horas_maximas
        self._horas_minimas = horas_minimas
 
    def get_id(self): return self._id
    def get_disponibilidad(self): return self._disponibilidad
    def get_nombre(self): return self._nombre
    def get_modulo(self): return self._modulo
    def get_grupo(self): return self._grupo
    def get_horas_maximas(self): return self._horas_maximas
    def get_horas_minimas(self): return self._horas_minimas
    def get_id_docente(self): return self._id_docente
    
 
def convertir_preferencias_a_disponibilidad(id_prof):
    """
    Consulta las preferencias/restricciones en la BD y genera la lista de 6 booleanos.
    """
    disponibilidad = [True] * SLOTS_POR_DIA
    return disponibilidad
 
def cargar_profesores_desde_bd():
    """
    En vez de coger solo la tabla Profesor, montamos las ASIGNACIONES
    a partir de la tabla Modulo:
      - cada fila de Modulo = (Profesor + Módulo + Ciclo/Grupo)
    Así podemos saber si es DAM1 o DAM2.
    """
    lista_objs = []

    # 1) Cargamos profesores en un diccionario: id_prof -> nombre
    profesores_db = get_profesor()          # lista de dicts
    mapa_profesores = {
        p["id_prof"]: p.get("nombre", f"Prof {p['id_prof']}")
        for p in profesores_db
    }

    # 2) Cargamos módulos (cada módulo está ligado a un profe y a un ciclo)
    modulos_db = get_modulo()               # lista de dicts
    print(f"--- Cargando asignaciones docentes desde la Base de Datos ({len(modulos_db)} registros) ---")

    for m in modulos_db:
        id_prof = m.get("id_prof")
        if id_prof is None:
            # módulo aún sin profesor asignado: lo saltamos
            continue

        id_modulo    = m.get("id_modulo")
        nombre_prof = mapa_profesores.get(id_prof, f"Prof {id_prof}")
        nombre_mod  = m.get("nombre", "Módulo")
        ciclo       = m.get("ciclo", "DAM1")          # DAM1 / DAM2
        horas_sem   = m.get("horas_semana", 4)        # las horas de ese módulo a la semana

        # Disponibilidad del profesor (aquí luego meteremos las preferencias reales)
        disponibilidad = convertir_preferencias_a_disponibilidad(id_prof)

        nuevo_prof = Prof(
            id=id_modulo,
            disponibilidad=disponibilidad,
            preferencia=[],
            nombre=nombre_prof,
            modulo=nombre_mod,
            grupo=ciclo,              
            horas_maximas=horas_sem, 
            horas_minimas=0,
            id_docente=id_prof
        )

        lista_objs.append(nuevo_prof)
        print(f" -> Asignación: {nombre_prof} | {nombre_mod} | {ciclo}")

    return lista_objs

def cargar_grupos_desde_bd(ciclo_filtrado=None):
    """
    Recupera los nombres únicos de los grupos/clases de la BD.
    Usa los diccionarios que devuelve get_modulo().
    """
    nombres_grupos = set()

    try:
        grupos_db = get_modulo()  # lista de dicts
        print(f"--- Cargando clases/grupos desde la BD (Filtro: {ciclo_filtrado}) ---")

        for g_data in grupos_db:
            # aquí uso 'ciclo' como nombre de grupo (DAM1, DAM2, etc.)
            g_ciclo = g_data.get("ciclo", "")
            if not g_ciclo:
                continue

            if ciclo_filtrado and g_ciclo != ciclo_filtrado:
                continue

            nombres_grupos.add(g_ciclo)

    except Exception as e:
        print(f"Error al cargar clases desde BD: {e}")
        return ["DAM1"]

    lista_ordenada = sorted(list(nombres_grupos)) or ["DAM1"]
    print(f" -> Grupos encontrados: {lista_ordenada}")
    return lista_ordenada

 
def contar_horas_asignadas(id_prof):
    """
    Cuenta el número total de horas que un profesor tiene asignadas en el horario actual.
    Suma las horas de TODAS las asignaciones que compartan el mismo ID de profesor.
    """
    cuenta = 0
    for profe_asignado in horario.values():
        if profe_asignado.get_id() == id_prof:
            cuenta += 1
    return cuenta
 
def esta_ocupado_a_esta_hora(id_docente, slot_objetivo):
    """
    Verifica si un profesor ya está impartiendo clase en otro grupo a la misma hora global.
    """
    for indice_tarea, profe in horario.items():
        if profe.get_id_docente() == id_docente:
            slot_ocupado = tareas_globales[indice_tarea]["indice_slot_global"]
            if slot_ocupado == slot_objetivo:
                return True
    return False
 
def crear_hueco(id_docente, slot_actual):
    """
    Analiza si asignar un profesor al slot actual generaría un hueco (gap) inválido.
    """
    indice_dia_actual = slot_actual // SLOTS_POR_DIA
    inicio_dia_indice = indice_dia_actual * SLOTS_POR_DIA
    fin_dia_indice = inicio_dia_indice + SLOTS_POR_DIA
   
    horas_asignadas_hoy = []
   
    for indice_tarea, profe in horario.items():
        if profe.get_id_docente() == id_docente: 
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
 
def generar_horario_recursivo(indice_tarea):
    """
    Algoritmo de Backtracking recursivo (Núcleo lógico).
    """
    global mejor_horario_copia, nodos_visitados 
    
    nodos_visitados += 1
    if nodos_visitados > MAX_NODOS:
        # hemos explorado demasiado, cortamos aquí
        return False
 
    if indice_tarea == len(tareas_globales):
        return True
 
    if indice_tarea > info_fallo["profundidad_maxima"]:
        info_fallo["profundidad_maxima"] = indice_tarea
        info_fallo["razones"] = {}
        mejor_horario_copia = horario.copy()
 
    tarea = tareas_globales[indice_tarea]
    indice_hora_diaria = tarea["indice_hora_diaria"]
    slot_absoluto = tarea["indice_slot_global"]
    nombre_grupo_tarea = tarea["nombre_grupo"]
   
    lista_profesores.sort(key=lambda p: p.get_horas_maximas() - contar_horas_asignadas(p.get_id()), reverse=True)
 
    for profesor in lista_profesores:
        nombre = profesor.get_nombre()
        id_asignacion = profesor.get_id()          # módulo concreto
        id_docente = profesor.get_id_docente()     # persona real
        p_grupo = profesor.get_grupo()
 
        if p_grupo != nombre_grupo_tarea:
            continue
 
        if not profesor.get_disponibilidad()[indice_hora_diaria]:
            if indice_tarea == info_fallo["profundidad_maxima"]:
                info_fallo["razones"][nombre] = "No disponible"
            continue
           
        if esta_ocupado_a_esta_hora(id_docente, slot_absoluto):
            if indice_tarea == info_fallo["profundidad_maxima"]:
                info_fallo["razones"][nombre] = "Ocupado con otro grupo"
            continue
 
        if contar_horas_asignadas(id_asignacion) >= profesor.get_horas_maximas():
            if indice_tarea == info_fallo["profundidad_maxima"]:
                info_fallo["razones"][nombre] = "Tope de horas"
            continue
 
        if crear_hueco(id_docente, slot_absoluto):
            if indice_tarea == info_fallo["profundidad_maxima"]:
                info_fallo["razones"][nombre] = "Genera hueco"
            continue
 
        horario[indice_tarea] = profesor
       
        if generar_horario_recursivo(indice_tarea + 1):
            return True
       
        del horario[indice_tarea]
 
    return False
 
def generar_matriz_horario(ciclo_filtrado=None):
    """
    Función principal exportable para ser usada desde el Controller_main.
    Inicializa datos, ejecuta el algoritmo y devuelve los resultados estructurados.
   
    Argumentos:
        ciclo_filtrado (str): Texto opcional para filtrar grupos (ej: "DAM").
    """
    global lista_profesores, grupos, tareas_globales, horario, info_fallo, mejor_horario_copia, nodos_visitados
    #                                                                                   ^^^^^^^^^^^^^^ añadido

    # 1. Resetear variables globales para evitar estados sucios
    horario = {}
    mejor_horario_copia = {}
    lista_profesores = []
    tareas_globales = []
    info_fallo = {"profundidad_maxima": -1, "razones": {}}
    nodos_visitados = 0   # <-- ahora sí resetea la global
 
    # 2. Cargar Datos
    try:
        lista_profesores = cargar_profesores_desde_bd()
    except Exception as e:
        print(f"Error al conectar con la BD o procesar profesores: {e}")
        lista_profesores = []
 
    # Pasamos el filtro aquí
    grupos = cargar_grupos_desde_bd(ciclo_filtrado)
   
    if not grupos:
        grupos = ["Grupo Único"]
 
    # 3. Preparar Tareas
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
 
    # 4. Ejecutar Algoritmo
    print(f"Iniciando algoritmo de generación para {len(grupos)} grupos...")
    exito = generar_horario_recursivo(0)
 
    # 5. Gestionar Resultado
    resultado_final = horario
    if not exito:
        print("No se encontró solución perfecta. Usando mejor aproximación.")
        resultado_final = mejor_horario_copia
       
        # Marcar el fallo
        indice = info_fallo["profundidad_maxima"]
        if indice < len(tareas_globales):
            resultado_final[indice] = Prof(-1, [], [], "CONFLICTO", "ERROR", "ERROR", 0, 0, id_docente=-1)
 
    # 6. Devolver estructura útil para la interfaz
    return {
        "horario": resultado_final,
        "grupos": grupos,
        "tareas": tareas_globales,
        "exito": exito,
        "info_fallo": info_fallo
    }
 
def imprimir_tabla_multi_grupo():
    """
    Imprime el horario en formato tabla por consola (solo para pruebas).
    """
    if not grupos: return
 
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
 
# Bloque de ejecución solo si se llama directamente al archivo (Testing)
if __name__ == "__main__":
    datos = generar_matriz_horario()
    horario = datos["horario"] # Asignar a global para que imprimir funcione
    imprimir_tabla_multi_grupo()