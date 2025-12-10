from supabase import create_client
from Controller.KEYBD import Config

supabase_url = Config.URL
supabase_key = Config.KEY
supabase = create_client(Config.URL, Config.KEY)

def get_profesor():
    resp = supabase.table("Profesor").select("*").order("id_prof").execute()
    return resp.data or []

def insertar_profesor(nombre: str, horas_max_dia: int, horas_max_semana: int, color:str = None):
    datos = {
        "nombre": nombre,
        "horas_max_dia": horas_max_dia,
        "horas_max_semana": horas_max_semana,
    }
    if color is not None:
        datos["color"] = color
    supabase.table("Profesor").insert(datos).execute()
   
def actualizar_profesor(id_prof: int, campo: str, valor):
        supabase.table("Profesor").update({campo: valor}).eq("id_prof", id_prof).execute()
        
def eliminar_profesor(id_prof: int):
    supabase.table("Profesor").delete().eq("id_prof", id_prof).execute()
        
        
def get_modulo():
    resp = supabase.table("Modulo").select("*").order("id_modulo").execute()
    return resp.data or []

def insertar_modulo(nombre: str, ciclo: str,  horas_semana: int, horas_max_dia:int, id_prof:int = None):
    datos = {
        "nombre": nombre,
        "ciclo": ciclo,
        "horas_semana": horas_semana,
        "horas_max_dia": horas_max_dia,
    }
    if id_prof is not None:
        datos["id_prof"] = id_prof
        
    supabase.table("Modulo").insert(datos).execute()
    
def actualizar_modulo(id_modulo: int, campo: str, valor):
        supabase.table("Modulo").update({campo: valor}).eq("id_modulo", id_modulo).execute()
        
def eliminar_modulo(id_modulo: int):
    supabase.table("Modulo").delete().eq("id_modulo", id_modulo).execute()
    
    

def get_preferencias_por_profesor(id_prof: int):
    resp = (
        supabase
        .table("Preferencias")
        .select("*")
        .eq("id_prof", id_prof)
        .order("dia_semana") 
        .order("hora_inicio")   
        .execute()
    )
    return resp.data or []


def insertar_preferencia(id_prof: int, dia: str, hora_inicio: int, hora_final: int, nivel: int):
    datos = {
        "id_prof": id_prof,
        "dia_semana": dia,
        "hora_inicio": hora_inicio,
        "hora_final": hora_final,
        "nivel": nivel,
    }
    supabase.table("Preferencias").insert(datos).execute()


def eliminar_preferencia(id_pref: int):
    supabase.table("Preferencias").delete().eq("id_pref", id_pref).execute()
    
def get_horario_ciclo(ciclo: str):
    resp = (
        supabase
        .table("Horario")      
        .select("*")
        .eq("ciclo", ciclo)
        .execute()
    )
    filas = resp.data or []

    profes = {p["id_prof"]: p.get("nombre", "") for p in get_profesor()}
    modulos = {m["id_modulo"]: m.get("nombre", "") for m in get_modulo()}

    for fila in filas:
        id_prof = fila.get("id_prof")
        id_mod  = fila.get("id_mod")

        fila["nombre_prof"] = profes.get(id_prof, "")
        fila["nombre_mod"]  = modulos.get(id_mod, "")

    return filas


def guardar_horario_ciclo(ciclo: str, slots: list[dict]):
    supabase.table("Horario").delete().eq("ciclo", ciclo).execute()
    if slots:
        supabase.table("Horario").insert(slots).execute()

