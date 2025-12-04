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
    