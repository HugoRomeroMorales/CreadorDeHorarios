from  PyQt5 import QtWidgets
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QMessageBox, QInputDialog, QTableWidgetItem

from Vista.Vista_ui import Ui_MainWindow
from Controller.Controller_db import (
    get_profesor,
    insertar_profesor,
    actualizar_profesor,
    eliminar_profesor,
    get_modulo,
    insertar_modulo,
    actualizar_modulo,
    eliminar_modulo,
    )

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        
        self.bloqueo_item_changed_prof = False
        self.bloqueo_item_changed_mod = False

        self.ui.btnCargarTrabajadores.clicked.connect(self.cargar_profesores_en_tabla)
        self.ui.btnAnadirProfesor.clicked.connect(self.anadir_profesor)
        self.ui.btnEliminarProfesor.clicked.connect(self.eliminar_profesor_seleccionado)
        self.ui.tablaProfesores.itemChanged.connect(self.celda_profesor_editada)

        header = self.ui.tablaProfesores.horizontalHeader()
        header.setSectionResizeMode(QtWidgets.QHeaderView.Stretch)

        self.ui.btnCargarModulos.clicked.connect(self.cargar_modulos_en_tabla)
        self.ui.btnAsignarProfesorModulo.clicked.connect(self.asignar_profesor_a_modulo)    
        
        self.ui.tablaModulos.itemChanged.connect(self.celda_modulo_editada)
        
        header_mod = self.ui.tablaModulos.horizontalHeader()
        header_mod.setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
        

    def cargar_profesores_en_tabla(self):
        try:
            profesores = get_profesor()
            modulos = get_modulo()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al cargar profesores:\n{e}") 
            return
             
        mods_por_prof = {} 
        for m in modulos:
            id_prof_mod = m.get("id_prof")
            if id_prof_mod is None:
                continue 
            nombre_mod = m.get("nombre", "")
            mods_por_prof.setdefault(id_prof_mod, []).append(nombre_mod)

        self.bloqueo_item_changed_prof = True
        

        tabla = self.ui.tablaProfesores
        tabla.clearContents()
        tabla.setRowCount(len(profesores))

        for fila, prof in enumerate(profesores):
            id_prof = prof.get("id_prof")
            nombre = prof.get("nombre", "")
            horas_max_dia = prof.get("horas_max_dia", "")
            horas_max_semana = prof.get("horas_max_semana", "")

        # Columna 0: Nombre
            item_nombre = QTableWidgetItem(str(nombre))
            item_nombre.setData(Qt.UserRole, id_prof)
            tabla.setItem(fila, 0, item_nombre)

        # Columna 1: Módulos 
            lista_mods = mods_por_prof.get(id_prof, [])
            texto_mods = ", ".join(lista_mods) if lista_mods else ""
            tabla.setItem(fila, 1, QTableWidgetItem(texto_mods))

        # Columna 2: Horas/semana
            tabla.setItem(fila, 2, QTableWidgetItem(str(horas_max_semana)))

        # Columna 3: Restricciones (horas_max_dia)
            tabla.setItem(fila, 3, QTableWidgetItem(str(horas_max_dia)))

        # Columna 4: Preferencias 
            tabla.setItem(fila, 4, QTableWidgetItem(""))

        self.bloqueo_item_changed_prof = False
        tabla.resizeColumnsToContents()
        
    def anadir_profesor(self):
        nombre, ok = QInputDialog.getText(self, "Nuevo profesor", "Nombre del profesor:")
        if not ok or not nombre.strip():
            return

        horas_dia, ok = QInputDialog.getInt(
            self,
            "Horas máx/día",
            "¿Cuántas horas máximas puede dar al día?",
            value=5,
            min=1,
            max=10,
        )
        if not ok:
            return

        horas_sem, ok = QInputDialog.getInt(
            self,
            "Horas máx/semana",
            "¿Cuántas horas máximas puede dar a la semana?",
            value=18,
            min=1,
            max=40,
        )
        if not ok:
            return

        try:
            insertar_profesor(nombre.strip(), horas_dia, horas_sem)
            QMessageBox.information(self, "OK", "Profesor insertado correctamente.")
            self.cargar_profesores_en_tabla()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al insertar profesor:\n{e}")

    def get_id_prof_de_fila(self, fila: int):
        item = self.ui.tablaProfesores.item(fila, 0)
        if item is None:
            return None
        return item.data(Qt.UserRole)

    def celda_profesor_editada(self, item):
        if self.bloqueo_item_changed_prof:
            return

        fila = item.row()
        columna = item.column()
        nuevo_valor = item.text()

        id_prof = self.get_id_prof_de_fila(fila)
        if id_prof is None:
            return

        campo = None
        if columna == 0:
            campo = "nombre"
        elif columna == 2:
            campo = "horas_max_semana"
        elif columna == 3:
            campo = "horas_max_dia"
        else:
            return

        if campo in ("horas_max_semana", "horas_max_dia"):
            try:
                nuevo_valor = int(nuevo_valor)
            except ValueError:
                QMessageBox.warning(self, "Valor inválido", "Debes introducir un número entero.")
                self.cargar_profesores_en_tabla()
                return

        try:
            actualizar_profesor(id_prof, campo, nuevo_valor)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al actualizar profesor:\n{e}")
            self.cargar_profesores_en_tabla()

    def eliminar_profesor_seleccionado(self):
        tabla = self.ui.tablaProfesores
        fila = tabla.currentRow()
        if fila < 0:
            QMessageBox.warning(self, "Eliminar profesor", "Selecciona un profesor primero.")
            return

        id_prof = self.get_id_prof_de_fila(fila)
        nombre = tabla.item(fila, 0).text() if tabla.item(fila, 0) else ""

        resp = QMessageBox.question(
            self,
            "Confirmar eliminación",
            f"¿Seguro que quieres eliminar al profesor '{nombre}' (id={id_prof})?",
            QMessageBox.Yes | QMessageBox.No,
        )

        if resp != QMessageBox.Yes:
            return

        try:
            eliminar_profesor(id_prof)
            self.cargar_profesores_en_tabla()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al eliminar profesor:\n{e}")
            
    def cargar_modulos_en_tabla(self):
        try:
            modulos = get_modulo()
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"Error al cargar módulos desde Supabase:\n{e}"
            )
            return

        self.bloqueo_item_changed_mod = True

        tabla = self.ui.tablaModulos
        tabla.clearContents()
        tabla.setRowCount(len(modulos))

        for fila, mod in enumerate(modulos):
            id_mod = mod.get("id_modulo")
            nombre = mod.get("nombre", "")
            ciclo = mod.get("ciclo", "")
            horas_sem = mod.get("horas_semana", "")
            horas_max_dia = mod.get("horas_max_dia", "")

            item_nombre = QTableWidgetItem(str(nombre))
            item_nombre.setData(Qt.UserRole, id_mod)
            tabla.setItem(fila, 0, item_nombre)

            tabla.setItem(fila, 1, QTableWidgetItem(str(ciclo)))
            tabla.setItem(fila, 2, QTableWidgetItem(str(horas_sem)))
            tabla.setItem(fila, 3, QTableWidgetItem(str(horas_max_dia)))

        self.bloqueo_item_changed_mod = False
        tabla.resizeColumnsToContents()

    def celda_modulo_editada(self, item):
        if self.bloqueo_item_changed_mod:
            return

        fila = item.row()
        columna = item.column()
        nuevo_valor = item.text()

        id_mod = self.get_id_mod_de_fila(fila)
        if id_mod is None:
            return

        campo = None
        if columna == 0:
            campo = "nombre"
        elif columna == 1:
            campo = "ciclo"
        elif columna == 2:
            campo = "horas_semana"
        elif columna == 3:
            campo = "horas_max_dia"
        else:
            return

        if campo in ("horas_semana", "horas_max_dia"):
            try:
                nuevo_valor = int(nuevo_valor)
            except ValueError:
                QMessageBox.warning(self, "Valor inválido", "Debes introducir un número entero.")
                self.cargar_modulos_en_tabla()
                return

        try:
            actualizar_modulo(id_mod, campo, nuevo_valor)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al actualizar módulo:\n{e}")
            self.cargar_modulos_en_tabla()
            
    def get_id_mod_de_fila(self, fila: int):
        item = self.ui.tablaModulos.item(fila, 0)
        if item is None:
            return None
        return item.data(Qt.UserRole)
    
    def asignar_profesor_a_modulo(self):
        tabla = self.ui.tablaModulos
        fila = tabla.currentRow()

        if fila < 0:
            QMessageBox.warning(self, "Asignar profesor", "Selecciona un módulo primero.")
            return

        id_mod = self.get_id_mod_de_fila(fila)
        if id_mod is None:
            QMessageBox.warning(self, "Asignar profesor", "No se ha podido obtener el id del módulo.")
            return

        # Cargamos los profesores desde Supabase
        try:
            profesores = get_profesor()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudieron cargar los profesores:\n{e}")
            return

        if not profesores:
            QMessageBox.information(self, "Asignar profesor", "No hay profesores en la base de datos.")
            return

        # Preparamos lista de nombres y mapa nombre -> id_prof
        nombres = [p.get("nombre", "") for p in profesores]
        mapa_nombre_id = {p.get("nombre", ""): p.get("id_prof") for p in profesores}

        # Diálogo para elegir profesor
        nombre_sel, ok = QInputDialog.getItem(
            self,
            "Asignar profesor",
            "Elige profesor para este módulo:",
            nombres,
            editable=False
        )

        if not ok:
            return

        id_prof_nuevo = mapa_nombre_id.get(nombre_sel)
        if id_prof_nuevo is None:
            QMessageBox.critical(self, "Error", "No se ha podido obtener el id del profesor seleccionado.")
            return

        # Actualizamos el módulo en Supabase
        try:
            actualizar_modulo(id_mod, "id_prof", id_prof_nuevo)
            QMessageBox.information(self, "OK", "Profesor asignado correctamente.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al asignar profesor:\n{e}")
            return

        # Recargamos tablas para reflejar el cambio
        self.cargar_modulos_en_tabla()
        self.cargar_profesores_en_tabla()



