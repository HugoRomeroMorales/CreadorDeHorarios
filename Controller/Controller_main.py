from PyQt5 import QtWidgets
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QMessageBox, QInputDialog, QTableWidgetItem
from Controller.algoritmo_backtracking import generar_matriz_horario, Prof
from PyQt5.QtGui import QColor

from PyQt5.QtWidgets import QMessageBox, QInputDialog, QTableWidgetItem, QFileDialog
from PyQt5 import uic

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
    get_preferencias_por_profesor,
    insertar_preferencia,
    eliminar_preferencia,
)

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        
        self.ui.labelGrupoHor.hide()
        self.ui.comboGrupoHorario.hide()

        self.ui.tablaHorario.setRowCount(6)
        self.ui.tablaHorario.setVerticalHeaderLabels(
            ["1ª", "2ª", "3ª", "4ª", "5ª", "6ª"]
        )

        self.bloqueo_item_changed_prof = False
        self.bloqueo_item_changed_mod = False
        self.modulos_cache = []

        self.ui.btnCargarTrabajadores.clicked.connect(self.cargar_profesores_en_tabla)
        self.ui.btnAnadirProfesor.clicked.connect(self.anadir_profesor)
        self.ui.btnEliminarProfesor.clicked.connect(self.eliminar_profesor_seleccionado)
        self.ui.tablaProfesores.itemChanged.connect(self.celda_profesor_editada)
        self.ui.btnAnadirModulo.clicked.connect(self.anadir_modulo)
        self.ui.btnEliminarModulo.clicked.connect(self.eliminar_modulo_seleccionado)

        header = self.ui.tablaProfesores.horizontalHeader()
        header.setSectionResizeMode(QtWidgets.QHeaderView.Stretch)

        self.ui.btnCargarModulos.clicked.connect(self.cargar_modulos_en_tabla)
        self.ui.btnAsignarProfesorModulo.clicked.connect(self.asignar_profesor_a_modulo)

        self.ui.tablaModulos.itemChanged.connect(self.celda_modulo_editada)

        header_mod = self.ui.tablaModulos.horizontalHeader()
        header_mod.setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
        
        self.ui.btnGenerarHorario.clicked.connect(self.on_generar_horario)
        self.cargar_ciclos_en_combobox()

        self.ui.comboDiaPref.clear()
        self.ui.comboDiaPref.addItems(["Lunes", "Martes", "Miércoles", "Jueves", "Viernes"])
        
        self.colores_prof = {}
        self.cargar_colores_profesores()

        horas = {
            "8:30-9:25": 1,
            "9:25-10:20": 2,
            "10:20-11:15": 3,
            "11:45-12:20": 4,
            "12:20-13:35": 5,
            "13:35-14:30": 6,
        }
        self.horas_map = horas

        self.ui.comboHoraPref.clear()
        for texto, valor in horas.items():
            self.ui.comboHoraPref.addItem(texto, valor)

        self.ui.comboTipoPref.clear()
        self.ui.comboTipoPref.addItems([
            "Muy preferida",
            "Neutra",
            "Evitar si es posible",
        ])

        self.cargar_profesores_en_combo_pref()

        self.ui.comboProfesoresPref.currentIndexChanged.connect(self.cargar_preferencias_profesor_seleccionado)
        self.ui.btnAnadirPreferencia.clicked.connect(self.anadir_preferencia)
        self.ui.btnGuardarPreferencias.clicked.connect(self.guardar_preferencias)

        self.ui.tablaPreferencias.cellDoubleClicked.connect(self.eliminar_preferencia_seleccionada)

        self.cargar_modulos_en_tabla()
        self.cargar_ciclos()
        self.ui.comboCicloModulos.currentTextChanged.connect(self.on_ciclo_modulo_cambiado)
        self.ui.comboGrupoModulos.currentTextChanged.connect(self.actualizar_tabla_modulos)

        self.ui.btnExportarCSV.clicked.connect(self.exportar_csv)

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

            item_nombre = QTableWidgetItem(str(nombre))
            item_nombre.setData(Qt.UserRole, id_prof)
            tabla.setItem(fila, 0, item_nombre)

            lista_mods = mods_por_prof.get(id_prof, [])
            texto_mods = ", ".join(lista_mods) if lista_mods else ""
            tabla.setItem(fila, 1, QTableWidgetItem(texto_mods))

            tabla.setItem(fila, 2, QTableWidgetItem(str(horas_max_semana)))
            tabla.setItem(fila, 3, QTableWidgetItem(str(horas_max_dia)))
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
            self.modulos_cache = get_modulo()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al cargar módulos desde Supabase:\n{e}")
            return

        self._cargar_modulos_en_tabla_desde_lista(self.modulos_cache)

    def _cargar_modulos_en_tabla_desde_lista(self, modulos):
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

#        .-----------.
#       /     12      \
#      | 11    •    1  |
#      | 10    |    2  |
#      |  9    |    3  |
#      |  8   A•P   4  |
#       \ 7    H    5 /
#        '-----6-----'

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

        try:
            profesores = get_profesor()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudieron cargar los profesores:\n{e}")
            return

        if not profesores:
            QMessageBox.information(self, "Asignar profesor", "No hay profesores en la base de datos.")
            return

        nombres = [p.get("nombre", "") for p in profesores]
        mapa_nombre_id = {p.get("nombre", ""): p.get("id_prof") for p in profesores}

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

        try:
            actualizar_modulo(id_mod, "id_prof", id_prof_nuevo)
            QMessageBox.information(self, "OK", "Profesor asignado correctamente.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al asignar profesor:\n{e}")
            return

        self.cargar_modulos_en_tabla()
        self.cargar_profesores_en_tabla()
        self.cargar_ciclos()

    def cargar_profesores_en_combo_pref(self):
        try:
            profesores = get_profesor()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudieron cargar los profesores:\n{e}")
            return

        combo = self.ui.comboProfesoresPref
        combo.clear()

        for prof in profesores:
            nombre = prof.get("nombre", "")
            id_prof = prof.get("id_prof")
            combo.addItem(nombre, id_prof)

        if combo.count() > 0:
            self.cargar_preferencias_profesor_seleccionado()
        else:
            self.ui.tablaPreferencias.clearContents()
            self.ui.tablaPreferencias.setRowCount(0)

    def get_id_prof_pref_actual(self):
        idx = self.ui.comboProfesoresPref.currentIndex()
        if idx < 0:
            return None
        return self.ui.comboProfesoresPref.itemData(idx)

    def cargar_preferencias_profesor_seleccionado(self):
        id_prof = self.get_id_prof_pref_actual()
        tabla = self.ui.tablaPreferencias

        if id_prof is None:
            tabla.clearContents()
            tabla.setRowCount(0)
            return

        try:
            prefs = get_preferencias_por_profesor(id_prof)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudieron cargar las preferencias:\n{e}")
            return

        tabla.clearContents()
        tabla.setRowCount(len(prefs))

        mapa_nivel_tipo = {
            1: "Muy preferida",
            2: "Neutra",
            3: "Evitar si es posible",
        }

        horas_invertido = {v: k for k, v in self.horas_map.items()}

        for fila, pref in enumerate(prefs):
            id_pref = pref.get("id_pref")
            dia = pref.get("dia_semana", "")
            hora_inicio = pref.get("hora_inicio", "")
            nivel = pref.get("nivel", None)

            tipo_texto = mapa_nivel_tipo.get(nivel, "")
            texto_hora = horas_invertido.get(hora_inicio, str(hora_inicio))

            item_dia = QTableWidgetItem(str(dia))
            item_dia.setData(Qt.UserRole, id_pref)
            tabla.setItem(fila, 0, item_dia)

            tabla.setItem(fila, 1, QTableWidgetItem(texto_hora))

            tabla.setItem(fila, 2, QTableWidgetItem(tipo_texto))

        tabla.resizeColumnsToContents()

    def anadir_preferencia(self):
        id_prof = self.get_id_prof_pref_actual()
        if id_prof is None:
            QMessageBox.warning(self, "Preferencias", "Selecciona un profesor primero.")
            return

        dia = self.ui.comboDiaPref.currentText()
        tipo_str = self.ui.comboTipoPref.currentText()

        hora_inicio = self.ui.comboHoraPref.currentData()
        if hora_inicio is None:
            QMessageBox.warning(self, "Preferencias", "Selecciona una hora válida.")
            return

        hora_final = hora_inicio + 1

        mapa_tipo_nivel = {
            "Muy preferida": 1,
            "Neutra": 2,
            "Evitar si es posible": 3,
        }
        nivel = mapa_tipo_nivel.get(tipo_str, 2)

        try:
            insertar_preferencia(id_prof, dia, hora_inicio, hora_final, nivel)
            QMessageBox.information(self, "Preferencias", "Preferencia añadida correctamente.")
            self.cargar_preferencias_profesor_seleccionado()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al insertar preferencia:\n{e}")

    def guardar_preferencias(self):
        self.cargar_preferencias_profesor_seleccionado()
        QMessageBox.information(self, "Preferencias", "Preferencias actualizadas.")

    def eliminar_preferencia_seleccionada(self, fila, columna):
        tabla = self.ui.tablaPreferencias
        item = tabla.item(fila, 0)

        if item is None:
            return

        id_pref = item.data(Qt.UserRole)

        resp = QMessageBox.question(
            self,
            "Eliminar preferencia",
            "¿Seguro que quieres eliminar esta preferencia?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if resp != QMessageBox.Yes:
            return

        try:
            eliminar_preferencia(id_pref)
            self.cargar_preferencias_profesor_seleccionado()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al eliminar preferencia:\n{e}")
#Aqui esta el metodo de eliminar el modulo, el funcionamiento de este es que si le das al boton sin haber seleccionar un modulo antes pues no nos dejara y aparecera un mensaje por pantalla
#Luego si lo seleccionamos borraremos la fila del modulo de la tabla y tendremos que confirmar si queremos borrarlo antes de que la acción se ejecute

    def eliminar_modulo_seleccionado(self):
        tabla = self.ui.tablaModulos
        fila = tabla.currentRow()

        if fila < 0:
            QMessageBox.warning(self, "Eliminar módulo", "Selecciona un módulo primero.")
            return

        item = tabla.item(fila, 0)
        if item is None:
            return

        id_mod = item.data(Qt.UserRole)
        nombre = item.text()

        resp = QMessageBox.question(
            self,
            "Confirmar eliminación",
            f"¿Eliminar el módulo '{nombre}' (id={id_mod})?",
            QMessageBox.Yes | QMessageBox.No
        )

        if resp != QMessageBox.Yes:
            return

        try:
            eliminar_modulo(id_mod)
            self.cargar_modulos_en_tabla()
            self.cargar_ciclos()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo eliminar:\n{e}")

#Aqui el metodo de añadir el modulo que en este al darle al boton de añadir ya nos dice que le digamos el nombre y el ciclo del modulo, junto al numero de horas y maximo de horas por dia, si todo esa informacion esta colocada correctamente y no rompe nada se nos deberia de generar el modulo 
    def anadir_modulo(self):
        nombre, ok = QInputDialog.getText(self, "Nuevo módulo", "Nombre del módulo:")
        if not ok or not nombre.strip():
            return

        ciclo, ok = QInputDialog.getText(self, "Ciclo", "Introduce el ciclo del módulo:")
        if not ok or not ciclo.strip():
            return

        horas_sem, ok = QInputDialog.getInt(
            self,
            "Horas por semana",
            "¿Cuántas horas semanales tiene este módulo?",
            value=5,
            min=1,
            max=40,
        )
        if not ok:
            return

        horas_max_dia, ok = QInputDialog.getInt(
            self,
            "Horas máximas por día",
            "Máximo de horas consecutivas por día para este módulo:",
            value=2,
            min=1,
            max=10,
        )
        if not ok:
            return

        try:
            insertar_modulo(nombre.strip(), ciclo.strip(), horas_sem, horas_max_dia)
            self.cargar_modulos_en_tabla()
            self.cargar_ciclos()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo añadir el módulo:\n{e}")

#Aqui el metodo de cargar ciclos  
    def cargar_ciclos(self):
        modulos = self.modulos_cache or []
        ciclos = sorted({m.get("ciclo", "") for m in modulos if m.get("ciclo")})
        self.ui.comboCicloModulos.clear()
        self.ui.comboCicloModulos.addItems(ciclos)
        if ciclos:
            self.cargar_nombres_por_ciclo()
            self.actualizar_tabla_modulos()
#Aqui el metodo de cuando gemos cambiado un modulo y un ciclo 
    def on_ciclo_modulo_cambiado(self):
        self.cargar_nombres_por_ciclo()
        self.actualizar_tabla_modulos()

    def cargar_nombres_por_ciclo(self):
        ciclo_sel = self.ui.comboCicloModulos.currentText()
        modulos = self.modulos_cache or []
        nombres = sorted({m.get("nombre", "") for m in modulos if (not ciclo_sel or m.get("ciclo") == ciclo_sel)})
        self.ui.comboGrupoModulos.clear()
        self.ui.comboGrupoModulos.addItems(nombres)

    def actualizar_tabla_modulos(self):
        ciclo_sel = self.ui.comboCicloModulos.currentText().strip()
        nombre_sel = self.ui.comboGrupoModulos.currentText().strip()
        modulos = self.modulos_cache or []
        filtrados = []

        for m in modulos:
            if ciclo_sel and m.get("ciclo") != ciclo_sel:
                continue
            if nombre_sel and m.get("nombre") != nombre_sel:
                continue
            filtrados.append(m)

        self._cargar_modulos_en_tabla_desde_lista(filtrados)
        
    def on_generar_horario(self):
        print(">>> Botón 'Generar horario' pulsado")

        ciclo = self.ui.comboCicloHorario.currentText().strip()
        if not ciclo:
            QMessageBox.warning(
                self,
                "Generar horario",
                "Selecciona primero un ciclo (DAM1, DAM2, ...)"
            )
            return

        datos = generar_matriz_horario(ciclo_filtrado=ciclo)

        # pintar directamente usando el diccionario devuelto
        self.rellenar_tabla_horario(datos)

    def cargar_ciclos_en_combobox(self):
        combo_ciclo = self.ui.comboCicloHorario
        combo_ciclo.clear()

        try:
            modulos = get_modulo()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudieron cargar los ciclos:\n{e}")
            return

        ciclos = sorted({m.get("ciclo") for m in modulos if m.get("ciclo")})

        combo_ciclo.addItem("")  # opción vacía
        for c in ciclos:
            combo_ciclo.addItem(c)

    def es_slot_preferencia_conflictiva(self, profe, tarea):
        """
        Devuelve True si para este profesor y esta tarea (día + hora)
        hay una preferencia de tipo 'Evitar si es posible' (nivel = 3).
        En ese caso pintaremos la celda en rojo.
        """
        id_prof = profe.get_id_docente()
        if id_prof is None or id_prof < 0:
            # id negativo lo usamos como dummy de conflicto
            return True

        dia_tarea = tarea["nombre_dia"] 
        # En BD seguramente guardas 'Miércoles' con tilde
        if dia_tarea == "Miercoles":
            dia_bd = "Miércoles"
        else:
            dia_bd = dia_tarea

        # En la tabla Preferencias guardas hora_inicio como 1..6
        hora_inicio_tarea = tarea["indice_hora_diaria"] + 1  # 0..5 -> 1..6

        try:
            prefs = get_preferencias_por_profesor(id_prof)
        except Exception as e:
            print(f"[PREF] Error al cargar preferencias de prof {id_prof}: {e}")
            return False

        for pref in prefs:
            dia_pref = pref.get("dia_semana")
            hora_pref = pref.get("hora_inicio")
            nivel = pref.get("nivel", 2)  # 1=Muy pref, 2=Neutra, 3=Evitar

            if dia_pref == dia_bd and hora_pref == hora_inicio_tarea:
                # Si el profe dijo "Evitar si es posible", lo marcamos en rojo
                if nivel == 3:
                    return True

        return False

    def rellenar_tabla_horario(self, datos):
        tabla = self.ui.tablaHorario

        # Limpiar toda la tabla (6 filas x 5 columnas)
        filas = tabla.rowCount()
        cols = tabla.columnCount()
        for f in range(filas):
            for c in range(cols):
                tabla.setItem(f, c, QTableWidgetItem(""))

        horario     = datos.get("horario", {})
        tareas      = datos.get("tareas", [])
        grupos      = datos.get("grupos", [])
        exito       = datos.get("exito", True)
        info_fallo  = datos.get("info_fallo", {})
        indice_conf = info_fallo.get("profundidad_maxima", -1)

        if not horario:
            print(" [INFO] No hay asignaciones en el horario.")
            return

        # De momento, mostramos solo el PRIMER grupo
        grupo_mostrado = grupos[0] if grupos else None

        indice_dia = {
            "Lunes": 0,
            "Martes": 1,
            "Miercoles": 2,
            "Miércoles": 2,  # por si acaso
            "Jueves": 3,
            "Viernes": 4,
        }

        for indice_tarea, profe in horario.items():
            tarea = tareas[indice_tarea]

            # Filtrar por grupo (DAM1 / DAM2)
            if grupo_mostrado and tarea["nombre_grupo"] != grupo_mostrado:
                continue

            fila = tarea["indice_hora_diaria"]           # 0..5
            col  = indice_dia.get(tarea["nombre_dia"], 0)  # 0..4

            if hasattr(profe, "get_modulo"):
                texto = f"{profe.get_modulo()} ({profe.get_nombre().split()[0]})"
            else:
                texto = "ERROR"

            item = QTableWidgetItem(texto)

            # 🎨 1) COLOR BASE DEL PROFESOR (tabla Profesor.color)
            try:
                if hasattr(profe, "get_id_docente"):
                    id_docente = profe.get_id_docente()
                else:
                    id_docente = None

                if id_docente is not None:
                    # por si no se ha cargado aún
                    if not hasattr(self, "colores_prof"):
                        self.cargar_colores_profesores()

                    color_hex = self.colores_prof.get(id_docente)
                    if color_hex:
                        item.setBackground(QColor(color_hex))
            except Exception as e:
                print(f"[COLORES] Error aplicando color al prof {profe.get_nombre()}: {e}")

            # 🔴 2) Si hay preferencia "Evitar si es posible", marcamos en rojito encima
            try:
                if self.es_slot_preferencia_conflictiva(profe, tarea):
                    item.setBackground(QColor(255, 200, 200))
            except Exception as e:
                print(f"[PINTAR PREF] Error comprobando preferencias: {e}")

            # 🔴 3) Si el algoritmo no encontró solución perfecta,
            #      resaltamos la celda conflictiva principal más fuerte.
            if not exito and indice_tarea == indice_conf:
                item.setBackground(QColor(255, 150, 150))

            tabla.setItem(fila, col, item)

            
            
    def cargar_colores_profesores(self):
        self.colores_prof = {}
        try:
            profesores = get_profesor()
        except Exception as e:
            print(f"[COLORES] Error al cargar profesores: {e}")
            return

        for p in profesores:
            pid = p.get("id_prof")
            color = p.get("color")  # campo de tu tabla
            if pid is not None and color:
                self.colores_prof[pid] = color
                
#Aqui tenemos el metodo de exportar csv, la funcionalidad del boton  es que cuando el usuario le da el boton para guardar la tabla en formato CSV, se recorre la tabla entera transformandola en filas y celdas para adaptarlo al csv y se muestra un mensaje de exito o de error al terminar, así completamos unas de las partes y nuestros usuarios saben que han hecho bien la exportación o no. 
    def exportar_csv(self):
        import csv

        path, _ = QFileDialog.getSaveFileName(
            self,
            "Guardar horario como CSV",
            "horario.csv",
            "CSV (*.csv)"
        )
        if not path:
            return

        tabla = self.ui.tablaHorario
        filas = tabla.rowCount()
        columnas = tabla.columnCount()

        try:
            with open(path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)

                headers = [tabla.horizontalHeaderItem(c).text() for c in range(columnas)]
                writer.writerow([""] + headers)

                for r in range(filas):
                    nombre_hora = tabla.verticalHeaderItem(r).text()
                    row = [nombre_hora]

                    for c in range(columnas):
                        item = tabla.item(r, c)
                        row.append(item.text() if item else "")

                    writer.writerow(row)

            QMessageBox.information(self, "Éxito", " El horario ha sido  exportado correctamente ;).")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo exportar este horario :( :\n{e}")
