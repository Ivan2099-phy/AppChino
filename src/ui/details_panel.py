from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QListWidget,
    QListWidgetItem, QGroupBox, QTextEdit
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont

class DetailsPanel(QWidget):
    """
    Muestra detalles completos de una palabra seleccionada.
    """
    statusChanged = pyqtSignal(str, str)   # word_id, new_status
    playRequested = pyqtSignal(float)      # timestamp en segundos

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_word_id = None
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        # 1. Información básica
        self.basic_info_box = QGroupBox("Palabra")
        info_layout = QVBoxLayout()
        
        self.hanzi_label = QLabel("—")
        self.hanzi_label.setAlignment(Qt.AlignCenter)
        self.hanzi_label.setFont(QFont("Arial", 32, QFont.Bold))
        
        self.pinyin_label = QLabel("")
        self.pinyin_label.setAlignment(Qt.AlignCenter)
        self.pinyin_label.setFont(QFont("Arial", 14))
        
        self.meaning_label = QLabel("")
        self.meaning_label.setAlignment(Qt.AlignCenter)
        self.meaning_label.setWordWrap(True)
        
        info_layout.addWidget(self.hanzi_label)
        info_layout.addWidget(self.pinyin_label)
        info_layout.addWidget(self.meaning_label)
        self.basic_info_box.setLayout(info_layout)
        layout.addWidget(self.basic_info_box)

        # 2. Estado (CORREGIDO: usa 'practice')
        self.status_box = QGroupBox("Estado")
        status_layout = QHBoxLayout()
        self.status_buttons = {}
        
        # Definición de botones y colores
        self.status_config = {
            "unknown": ("Desconocida", "#ffcccc"),
            "practice": ("En Práctica", "#fff2cc"), # Clave coincidente con DB
            "known": ("Conocida", "#ccffcc")
        }

        for status, (label, color) in self.status_config.items():
            btn = QPushButton(label)
            # Usamos lambda con default arg para capturar el valor correcto de status
            btn.clicked.connect(lambda checked, s=status: self.on_status_clicked(s))
            self.status_buttons[status] = btn
            status_layout.addWidget(btn)
            
        self.status_box.setLayout(status_layout)
        layout.addWidget(self.status_box)

        # 3. Contextos
        self.context_box = QGroupBox("Contextos en el video")
        ctx_layout = QVBoxLayout()
        self.context_list = QListWidget()
        self.context_list.itemClicked.connect(self._on_context_clicked)
        ctx_layout.addWidget(self.context_list)
        self.context_box.setLayout(ctx_layout)
        layout.addWidget(self.context_box)

        # 4. Ejemplos IA
        self.examples_box = QGroupBox("Ejemplos IA")
        ex_layout = QVBoxLayout()
        self.examples_text = QTextEdit()
        self.examples_text.setReadOnly(True)
        ex_layout.addWidget(self.examples_text)
        self.examples_box.setLayout(ex_layout)
        layout.addWidget(self.examples_box)

    def update_details(self, details):
        """Recibe el diccionario de datos de la palabra y actualiza la UI"""
        if not details:
            return

        self.current_word_id = details['id']
        
        # Info básica
        self.hanzi_label.setText(details['hanzi'])
        self.pinyin_label.setText(details['pinyin'] or "")
        self.meaning_label.setText(details['meaning'] or "")
        
        # Actualizar botones de estado
        current_status = details.get('user_status', 'unknown')
        self._update_status_buttons(current_status)

        # Contextos
        self.context_list.clear()
        for ctx in details.get('contexts', []):
            # Formato: "Frase... [MM:SS]"
            ts = ctx.get('timestamp', 0)
            time_str = f"[{int(ts//60):02d}:{int(ts%60):02d}]"
            item = QListWidgetItem(f"{ctx['sentence']} {time_str}")
            item.setData(Qt.UserRole, ts) # Guardamos el timestamp oculto
            self.context_list.addItem(item)

        # Ejemplos
        examples = details.get('examples', [])
        if examples:
            self.examples_text.setText("\n".join(f"• {ex}" for ex in examples))
        else:
            self.examples_text.setText("Sin ejemplos adicionales.")

    def _update_status_buttons(self, current_status):
        """Ilumina el botón activo y apaga los demás"""
        for status, btn in self.status_buttons.items():
            if status == current_status:
                # Borde grueso y color intenso
                bg_color = self.status_config[status][1]
                btn.setStyleSheet(f"background-color: {bg_color}; border: 2px solid #555; font-weight: bold;")
            else:
                # Estilo normal
                btn.setStyleSheet("")

    def on_status_clicked(self, new_status):
        if self.current_word_id:
            self.statusChanged.emit(str(self.current_word_id), new_status)
            self._update_status_buttons(new_status)

    def _on_context_clicked(self, item):
        timestamp = item.data(Qt.UserRole)
        if timestamp is not None:
            self.playRequested.emit(timestamp)
