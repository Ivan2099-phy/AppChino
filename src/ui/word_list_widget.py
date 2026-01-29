from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QTabWidget,
    QTableWidget, QTableWidgetItem,
    QTreeWidget, QTreeWidgetItem,
    QToolBar, QComboBox
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor


# ===============================
# Configuración visual por estado
# ===============================

WORD_STATUS_COLORS = {
    "unknown": QColor("#ffcccc"),   # rojo claro
    "practice": QColor("#fff2cc"),  # amarillo
    "known": QColor("#ccffcc"),     # verde
}


# ===============================
# Widget principal
# ===============================

class WordListWidget(QWidget):
    """
    Muestra palabras analizadas con:
    - Vista por frecuencia (tabla)
    - Vista por HSK (árbol)
    - Filtros por estado y HSK
    """

    wordSelected = pyqtSignal(str)   # emite word_id

    def __init__(self, parent=None):
        super().__init__(parent)

        self.words = []           # lista completa
        self.filtered_words = []  # lista filtrada

        self._setup_ui()

    # ===============================
    # UI base
    # ===============================

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        # Toolbar
        self.toolbar = QToolBar()
        self._setup_toolbar()
        layout.addWidget(self.toolbar)

        # Tabs
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)

        self.setup_frequency_tab()
        self.setup_hsk_tab()

    # ===============================
    # Toolbar (filtros)
    # ===============================

    def _setup_toolbar(self):
        self.status_filter = QComboBox()
        self.status_filter.addItems(["Todos", "unknown", "practice", "known"])
        self.status_filter.currentTextChanged.connect(self._apply_filters)

        self.hsk_filter = QComboBox()
        self.hsk_filter.addItems(
            ["Todos"] + [f"HSK {i}" for i in range(1, 7)] + ["Fuera de HSK"]
        )
        self.hsk_filter.currentTextChanged.connect(self._apply_filters)

        self.toolbar.addWidget(self.status_filter)
        self.toolbar.addWidget(self.hsk_filter)

    # ===============================
    # TAB 1: Por frecuencia (tabla)
    # ===============================

    def setup_frequency_tab(self):
        self.freq_table = QTableWidget()
        self.freq_table.setColumnCount(5)
        self.freq_table.setHorizontalHeaderLabels([
            "Palabra", "Frecuencia", "Estado", "HSK", "Pinyin"
        ])
        self.freq_table.setSortingEnabled(True)
        self.freq_table.cellClicked.connect(self.on_word_clicked)

        self.tabs.addTab(self.freq_table, "Por Frecuencia")

    # ===============================
    # TAB 2: Por HSK (árbol)
    # ===============================

    def setup_hsk_tab(self):
        self.hsk_tree = QTreeWidget()
        self.hsk_tree.setHeaderLabels([
            "Palabra", "Frecuencia", "Estado", "Pinyin"
        ])
        self.hsk_tree.itemClicked.connect(self._on_tree_item_clicked)

        self.tabs.addTab(self.hsk_tree, "Por HSK")

    # ===============================
    # Poblar datos
    # ===============================

    def populate_table(self, words: list, sort_by="frequency"):
        """
        words: lista de dicts con estructura:
        {
            "id": str,
            "word": str,
            "frequency": int,
            "hsk": int | "Fuera de HSK",
            "pinyin": str,
            "status": "unknown" | "practice" | "known"
        }
        """
        self.words = words
        self.filtered_words = words

        self._populate_frequency_table()
        self._populate_hsk_tree()

    # ===============================
    # Tabla de frecuencia
    # ===============================

    def _populate_frequency_table(self):
        table = self.freq_table
        table.setRowCount(len(self.filtered_words))

        for row, w in enumerate(self.filtered_words):
            table.setItem(row, 0, QTableWidgetItem(w["word"]))
            table.setItem(row, 1, QTableWidgetItem(str(w["frequency"])))
            table.setItem(row, 2, QTableWidgetItem(w["status"]))
            table.setItem(row, 3, QTableWidgetItem(str(w["hsk"])))
            table.setItem(row, 4, QTableWidgetItem(w["pinyin"]))

            # Guardar ID en la palabra
            table.item(row, 0).setData(Qt.UserRole, w["id"])

            # Color por estado
            color = WORD_STATUS_COLORS.get(w["status"])
            if color:
                for col in range(table.columnCount()):
                    table.item(row, col).setBackground(color)

        table.resizeColumnsToContents()

    # ===============================
    # Árbol por HSK
    # ===============================

    def _populate_hsk_tree(self):
        tree = self.hsk_tree
        tree.clear()

        groups = {}

        for w in self.filtered_words:
            hsk = w["hsk"]
            key = f"HSK {hsk}" if isinstance(hsk, int) else "Fuera de HSK"

            if key not in groups:
                groups[key] = QTreeWidgetItem([key])
                tree.addTopLevelItem(groups[key])

            item = QTreeWidgetItem([
                w["word"],
                str(w["frequency"]),
                w["status"],
                w["pinyin"]
            ])

            item.setData(0, Qt.UserRole, w["id"])

            color = WORD_STATUS_COLORS.get(w["status"])
            if color:
                for i in range(4):
                    item.setBackground(i, color)

            groups[key].addChild(item)

        tree.expandAll()

    # ===============================
    # Interacción
    # ===============================

    def on_word_clicked(self, row, column):
        item = self.freq_table.item(row, 0)
        if not item:
            return
        word_id = item.data(Qt.UserRole)
        self.wordSelected.emit(word_id)

    def _on_tree_item_clicked(self, item, column):
        word_id = item.data(0, Qt.UserRole)
        if word_id:
            self.wordSelected.emit(word_id)

    # ===============================
    # Filtros
    # ===============================

    def _apply_filters(self):
        status = self.status_filter.currentText()
        hsk = self.hsk_filter.currentText()

        self.filtered_words = []

        for w in self.words:
            if status != "Todos" and w["status"] != status:
                continue

            if hsk != "Todos":
                if hsk == "Fuera de HSK" and w["hsk"] != "Fuera de HSK":
                    continue
                if hsk.startswith("HSK"):
                    level = int(hsk.split()[-1])
                    if w["hsk"] != level:
                        continue

            self.filtered_words.append(w)

        self._populate_frequency_table()
        self._populate_hsk_tree()

    # ===============================
    # Cambio de estado
    # ===============================

    def change_word_status(self, word_id: str, new_status: str):
        """
        Actualiza estado local y refresca UI.
        La DB debe actualizarse fuera de este widget.
        """
        for w in self.words:
            if w["id"] == word_id:
                w["status"] = new_status
                break

        self._apply_filters()
