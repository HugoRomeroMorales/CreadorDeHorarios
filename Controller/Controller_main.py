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

        self.ui.btnCargarTrabajadores.clicked.connect(self.cargar_profesores_en_tabla)
        self.ui.btnAnadirProfesor.clicked.connect(self.anadir_profesor)
        self.ui.btnEliminarProfesor.clicked.connect(self.eliminar_profesor_seleccionado)
        self.ui.tablaProfesores.itemChanged.connect(self.celda_profesor_editada)

        self.ui.btnCargarModulos.clicked.connect(self.cargar_modulos_en_tabla)
        

        header = self.ui.tablaProfesores.horizontalHeader()
        header.setSectionResizeMode(QtWidgets.QHeaderView.Stretch)

    def cargar_profesores_en_tabla(self):
    # 1) Traemos profesores
        profesores = get_profesor()

    # 2) Traemos módulos para saber qué da cada profe
        modulos = get_modulo()
        mods_por_prof = {}  # dict: id_prof -> [nombres de módulo]

        for m in modulos:
            id_prof_mod = m.get("id_prof")
            if id_prof_mod is None:
                continue  # módulo aún sin profe asignado
            nombre_mod = m.get("nombre", "")
            mods_por_prof.setdefault(id_prof_mod, []).append(nombre_mod)

        self._bloqueo_item_changed_prof = True

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

        # Columna 1: Módulos (lista separada por comas)
            lista_mods = mods_por_prof.get(id_prof, [])
            texto_mods = ", ".join(lista_mods) if lista_mods else ""
            tabla.setItem(fila, 1, QTableWidgetItem(texto_mods))

        # Columna 2: Horas/semana
            tabla.setItem(fila, 2, QTableWidgetItem(str(horas_max_semana)))

        # Columna 3: Restricciones (horas_max_dia)
            tabla.setItem(fila, 3, QTableWidgetItem(str(horas_max_dia)))

        # Columna 4: Preferencias (de momento vacío)
            tabla.setItem(fila, 4, QTableWidgetItem(""))

        self._bloqueo_item_changed_prof = False
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

    def _get_id_prof_de_fila(self, fila: int):
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

        id_prof = self._get_id_prof_de_fila(fila)
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
            return  # otras columnas de momento no tocan la BBDD

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

        id_prof = self._get_id_prof_de_fila(fila)
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
        modulos = get_modulo()

        tabla = self.ui.tablaModulos
        tabla.clearContents()
        tabla.setRowCount(len(modulos))

        for fila, mod in enumerate(modulos):
            id_mod = mod.get("id_modulo")
            nombre = mod.get("nombre", "")
            ciclo = mod.get("ciclo", "")
            horas_sem = mod.get("horas_semana", "")
            horas_max_dia = mod.get("horas_max_dia", "")

            # Columna 0: Nombre
            item_nombre = QTableWidgetItem(str(nombre))
            item_nombre.setData(Qt.UserRole, id_mod)
            tabla.setItem(fila, 0, item_nombre)

            # Columna 1: Ciclo
            tabla.setItem(fila, 1, QTableWidgetItem(str(ciclo)))

            # Columna 2: Horas/semana
            tabla.setItem(fila, 2, QTableWidgetItem(str(horas_sem)))

            # Columna 3: Horas máx/día
            tabla.setItem(fila, 3, QTableWidgetItem(str(horas_max_dia)))

        tabla.resizeColumnsToContents()