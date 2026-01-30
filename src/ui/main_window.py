"""
Main Window - PyQt5 GUI for Chinese Video Analyzer
"""
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QLineEdit, QFileDialog, QTabWidget, QListWidget,
    QTextEdit, QProgressBar, QMessageBox, QListWidgetItem,
    QSplitter, QGroupBox, QComboBox, QStatusBar
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont, QColor
import sys
import os

# Add parent directory to path to import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.app_controller import ChineseVideoAnalyzer


class ProcessingThread(QThread):
    """Background thread for video processing"""
    progress_update = pyqtSignal(str, int)
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)
    
    def __init__(self, app_controller, video_source, is_youtube=True):
        super().__init__()
        self.app_controller = app_controller
        self.video_source = video_source
        self.is_youtube = is_youtube
    
    def run(self):
        try:
            if self.is_youtube:
                result = self.app_controller.process_youtube_video(
                    self.video_source,
                    progress_callback=self._progress_callback
                )
            else:
                result = self.app_controller.process_local_video(
                    self.video_source,
                    progress_callback=self._progress_callback
                )
            
            self.finished.emit(result)
            
        except Exception as e:
            self.error.emit(str(e))
    
    def _progress_callback(self, message, progress):
        self.progress_update.emit(message, progress)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # Initialize application controller
        self.app = ChineseVideoAnalyzer()
        
        # Current video data
        self.current_video_id = None
        self.current_words = []
        
        # Setup UI
        self.init_ui()
        
        # Load video history
        self.load_video_history()
    
    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("Chinese Video Analyzer - Learn Chinese from Videos")
        self.setGeometry(100, 100, 1200, 800)
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)
        
        # === Input Section ===
        input_group = QGroupBox("Video Input")
        input_layout = QVBoxLayout()
        
        # YouTube URL input
        youtube_layout = QHBoxLayout()
        youtube_layout.addWidget(QLabel("YouTube URL:"))
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("https://youtube.com/watch?v=...")
        youtube_layout.addWidget(self.url_input)
        
        self.process_url_btn = QPushButton("Process YouTube Video")
        self.process_url_btn.clicked.connect(self.process_youtube)
        youtube_layout.addWidget(self.process_url_btn)
        
        input_layout.addLayout(youtube_layout)
        
        # Local file input
        file_layout = QHBoxLayout()
        file_layout.addWidget(QLabel("Local File:"))
        self.file_path_input = QLineEdit()
        self.file_path_input.setPlaceholderText("Select a video file...")
        self.file_path_input.setReadOnly(True)
        file_layout.addWidget(self.file_path_input)
        
        self.browse_btn = QPushButton("Browse...")
        self.browse_btn.clicked.connect(self.browse_file)
        file_layout.addWidget(self.browse_btn)
        
        self.process_file_btn = QPushButton("Process Local Video")
        self.process_file_btn.clicked.connect(self.process_local)
        file_layout.addWidget(self.process_file_btn)
        
        input_layout.addLayout(file_layout)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        input_layout.addWidget(self.progress_bar)
        
        self.progress_label = QLabel("")
        input_layout.addWidget(self.progress_label)
        
        input_group.setLayout(input_layout)
        main_layout.addWidget(input_group)
        
        # === Main Content Area ===
        content_splitter = QSplitter(Qt.Horizontal)
        
        # Left panel: Video history
        history_widget = QWidget()
        history_layout = QVBoxLayout()
        history_layout.addWidget(QLabel("Video History"))
        
        self.history_list = QListWidget()
        self.history_list.itemClicked.connect(self.load_video)
        history_layout.addWidget(self.history_list)
        
        history_widget.setLayout(history_layout)
        content_splitter.addWidget(history_widget)
        
        # Middle panel: Word list
        words_widget = QWidget()
        words_layout = QVBoxLayout()
        
        # Sort controls
        sort_layout = QHBoxLayout()
        sort_layout.addWidget(QLabel("Sort by:"))
        self.sort_combo = QComboBox()
        self.sort_combo.addItems(["Frequency", "HSK Level", "Alphabetical"])
        self.sort_combo.currentTextChanged.connect(self.refresh_word_list)
        sort_layout.addWidget(self.sort_combo)
        sort_layout.addStretch()
        words_layout.addLayout(sort_layout)
        
        # Word list tabs
        self.word_tabs = QTabWidget()
        
        # All words tab
        self.all_words_list = QListWidget()
        self.all_words_list.itemClicked.connect(self.show_word_details)
        self.word_tabs.addTab(self.all_words_list, "All Words")
        
        # HSK level tabs
        self.hsk_lists = {}
        for level in range(1, 7):
            hsk_list = QListWidget()
            hsk_list.itemClicked.connect(self.show_word_details)
            self.hsk_lists[level] = hsk_list
            self.word_tabs.addTab(hsk_list, f"HSK {level}")
        
        # Non-HSK tab
        self.non_hsk_list = QListWidget()
        self.non_hsk_list.itemClicked.connect(self.show_word_details)
        self.word_tabs.addTab(self.non_hsk_list, "Non-HSK")
        
        words_layout.addWidget(self.word_tabs)
        words_widget.setLayout(words_layout)
        content_splitter.addWidget(words_widget)
        
        # Right panel: Word details
        details_widget = QWidget()
        details_layout = QVBoxLayout()
        details_layout.addWidget(QLabel("Word Details"))
        
        # Word info
        self.word_chinese = QLabel("")
        self.word_chinese.setStyleSheet("color: #FFFFFF; margin-bottom: 5px;")
        self.word_chinese.setFont(QFont("Microsoft YaHei", 32, QFont.Bold))
        details_layout.addWidget(self.word_chinese)
        
        self.word_pinyin = QLabel("")
        self.word_pinyin.setStyleSheet("color: #4CAF50; font-style: italic;")
        self.word_pinyin.setFont(QFont("Arial", 14))
        details_layout.addWidget(self.word_pinyin)
        
        self.word_translation = QLabel("")
        self.word_translation.setFont(QFont("Arial", 12))
        self.word_translation.setStyleSheet("color: #BBBBBB; font-size: 14px;")
        details_layout.addWidget(self.word_translation)
        
        self.word_hsk = QLabel("")
        details_layout.addWidget(self.word_hsk)
        
        # Status buttons
        status_layout = QHBoxLayout()
        status_layout.addWidget(QLabel("Status:"))
        
        self.btn_known = QPushButton("✓ Known")
        #self.btn_known.setStyleSheet("background-color: #4CAF50; color: white;")
        self.btn_known.setStyleSheet("""
            QPushButton {
                background-color: #2D3A2D; color: #81C784; border: 1px solid #4CAF50;
                border-radius: 15px; padding: 6px; font-weight: bold;
            }
            QPushButton:hover { background-color: #4CAF50; color: white; }
        """)
        self.btn_known.clicked.connect(lambda: self.set_word_status('known'))
        status_layout.addWidget(self.btn_known)
        
        self.btn_practice = QPushButton("⚡ Practice")
        #self.btn_practice.setStyleSheet("background-color: #FFC107; color: white;")
        self.btn_practice.setStyleSheet("""
            QPushButton {
                background-color: #3E3520; color: #FFD54F; border: 1px solid #FFC107;
                border-radius: 15px; padding: 6px; font-weight: bold;
            }
            QPushButton:hover { background-color: #FFC107; color: black; }
        """)
        self.btn_practice.clicked.connect(lambda: self.set_word_status('practice'))
        status_layout.addWidget(self.btn_practice)
        
        self.btn_unknown = QPushButton("? Unknown")
        #self.btn_unknown.setStyleSheet("background-color: #F44336; color: white;")
        self.btn_unknown.setStyleSheet("""
            QPushButton {
                background-color: #3E2723; color: #E57373; border: 1px solid #F44336;
                border-radius: 15px; padding: 6px; font-weight: bold;
            }
            QPushButton:hover { background-color: #F44336; color: white; }
        """)
        self.btn_unknown.clicked.connect(lambda: self.set_word_status('unknown'))
        status_layout.addWidget(self.btn_unknown)
        
        details_layout.addLayout(status_layout)
        
        # Example sentences
        details_layout.addWidget(QLabel("Example Sentences:"))
        self.examples_text = QTextEdit()
        self.examples_text.setStyleSheet("""
            QTextEdit {
                background-color: #181818;
                border: none;
                border-radius: 8px;
                color: #AAAAAA;
                line-height: 1.5;
                padding: 10px;
            }
        """)
        self.examples_text.setReadOnly(True)
        details_layout.addWidget(self.examples_text)
        
        details_widget.setLayout(details_layout)
        content_splitter.addWidget(details_widget)
        
        # Set splitter sizes
        content_splitter.setSizes([200, 400, 400])
        
        main_layout.addWidget(content_splitter)
        
        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")
    
        self.setStyleSheet("""
            QMainWindow { background-color: #121212; }
            
            /* Grupos de entrada con bordes suaves */
            QGroupBox {
                color: #E0E0E0;
                font-family: 'Segoe UI', sans-serif;
                font-weight: bold;
                border: 1px solid #333333;
                border-radius: 8px;
                margin-top: 15px;
                padding-top: 10px;
            }
            
            /* Inputs modernos */
            QLineEdit {
                background-color: #1E1E1E;
                border: 1px solid #333333;
                border-radius: 4px;
                color: #FFFFFF;
                padding: 8px;
                selection-background-color: #4CAF50;
            }

            /* Listas con items más espaciosos */
            QListWidget {
                background-color: #1E1E1E;
                border-radius: 6px;
                color: #D1D1D1;
                font-size: 16px; /* Letra más grande */
                outline: none;
                padding: 5px;
            }
            QListWidget::item {
                padding: 10px;
                border-bottom: 1px solid #2A2A2A;
            }
            QListWidget::item:selected {
                background-color: #2D2D2D;
                color: #4CAF50;
                border-left: 3px solid #4CAF50;
            }
                           
            QTextEdit {
                font-size: 18px; /* Texto de ejemplos más legible */
                line-height: 1.6;
            }

            /* Tabs (Pestañas) con mejor visibilidad */
            QTabBar::tab {
                background: #2D2D2D;
                color: #AAA;
                padding: 8px 12px;
                font-size: 13px;
            }
            QTabBar::tab:selected {
                background: #3D3D3D;
                color: #4CAF50;
                border-bottom: 2px solid #4CAF50;
            }
        """)

    def browse_file(self):
        """Open file browser to select video"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Video File",
            "",
            "Video Files (*.mp4 *.avi *.mkv *.mov);;All Files (*)"
        )
        
        if file_path:
            self.file_path_input.setText(file_path)
    
    def process_youtube(self):
        """Process YouTube video"""
        url = self.url_input.text().strip()
        
        if not url:
            QMessageBox.warning(self, "Input Error", "Please enter a YouTube URL")
            return
        
        self.start_processing(url, is_youtube=True)
    
    def process_local(self):
        """Process local video file"""
        file_path = self.file_path_input.text().strip()
        
        if not file_path:
            QMessageBox.warning(self, "Input Error", "Please select a video file")
            return
        
        self.start_processing(file_path, is_youtube=False)
    
    def start_processing(self, source, is_youtube=True):
        """Start video processing in background thread"""
        # Disable input controls
        self.process_url_btn.setEnabled(False)
        self.process_file_btn.setEnabled(False)
        self.browse_btn.setEnabled(False)
        
        # Show progress bar
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        
        # Create and start processing thread
        self.processing_thread = ProcessingThread(
            self.app,
            source,
            is_youtube
        )
        
        self.processing_thread.progress_update.connect(self.update_progress)
        self.processing_thread.finished.connect(self.processing_finished)
        self.processing_thread.error.connect(self.processing_error)
        
        self.processing_thread.start()
    
    def update_progress(self, message, progress):
        """Update progress bar and label"""
        self.progress_label.setText(message)
        self.progress_bar.setValue(progress)
        self.status_bar.showMessage(message)
    
    def processing_finished(self, result):
            """Maneja la finalización del procesamiento de video, con o sin éxito."""
            # Ocultar barra de progreso y limpiar texto
            self.progress_bar.setVisible(False)
            self.progress_label.setText("")
            
            # Rehabilitar botones de la interfaz
            self.process_url_btn.setEnabled(True)
            self.process_file_btn.setEnabled(True)
            self.browse_btn.setEnabled(True)

            # 1. VALIDACIÓN: Si el resultado es None o tiene un error
            if not result or 'error' in result:
                error_msg = result.get('error', 'Error desconocido durante el procesamiento')
                QMessageBox.critical(
                    self, 
                    "Error de Procesamiento", 
                    f"No se pudo procesar el video:\n\n{error_msg}"
                )
                self.status_bar.showMessage("Error al procesar el video.", 5000)
                return

            # 2. PROCESO EXITOSO: Intentar leer los datos de forma segura
            try:
                # Usamos .get() con valores por defecto para evitar KeyErrors
                title = result.get('title', 'Video sin título')
                stats = result.get('stats', {})
                total_words = stats.get('total_words', 0)
                unique_words = stats.get('unique_words', 0)
                video_id = result.get('video_id')

                # Mostrar mensaje de éxito al usuario
                QMessageBox.information(
                    self,
                    "Éxito",
                    f"¡Video procesado correctamente!\n\n"
                    f"Título: {title}\n"
                    f"Palabras totales: {total_words}\n"
                    f"Palabras únicas: {unique_words}"
                )
                
                # Limpiar campos de entrada
                self.url_input.clear()
                self.file_path_input.clear()
                
                # Actualizar historial y cargar datos en la lista
                self.load_video_history()
                
                if video_id:
                    self.current_video_id = video_id
                    # Usamos la función de carga que agregamos anteriormente
                    self.load_video_data(video_id)
                    self.status_bar.showMessage(f"Cargado: {title}", 5000)
                else:
                    self.status_bar.showMessage("Video procesado, pero no se encontró ID.", 5000)

            except Exception as e:
                # Captura cualquier error inesperado al actualizar la UI
                print(f"Error crítico en la interfaz: {e}")
                QMessageBox.warning(self, "Aviso", f"El video se procesó pero hubo un error al mostrarlo: {str(e)}")
    
    def processing_error(self, error_message):
        """Handle processing error"""
        self.progress_bar.setVisible(False)
        self.progress_label.setText("")
        
        # Re-enable controls
        self.process_url_btn.setEnabled(True)
        self.process_file_btn.setEnabled(True)
        self.browse_btn.setEnabled(True)
        
        QMessageBox.critical(self, "Error", f"Error processing video:\n{error_message}")
        self.status_bar.showMessage("Error occurred", 5000)
    
    def load_video_history(self):
        """Load video history into list"""
        self.history_list.clear()
        videos = self.app.get_all_videos()
        
        for video in videos:
            item = QListWidgetItem(video['title'])
            item.setData(Qt.UserRole, video['video_id'])
            self.history_list.addItem(item)
    
    def load_video(self, item):
        """Load selected video from history"""
        video_id = item.data(Qt.UserRole)
        self.current_video_id = video_id
        self.refresh_word_list()
        
        # Get stats
        stats = self.app.get_video_stats(video_id)
        if stats:
            self.status_bar.showMessage(
                f"Loaded video with {stats['unique_words']} unique words"
            )
            
    # PEGAR ESTO EN main_window.py DEBAJO DE def load_video(...)

    def load_video_data(self, video_id):
        """Helper to load data without list item event"""
        self.current_video_id = video_id
        self.refresh_word_list()
        
        # Get stats and update status bar
        stats = self.app.get_video_stats(video_id)
        if stats:
            self.status_bar.showMessage(
                f"Loaded video: {stats['unique_words']} unique words found."
            )
    
    def refresh_word_list(self):
        """Refresh word list based on current video and sort order"""
        if not self.current_video_id:
            return
        
        # Get sort method
        sort_map = {
            "Frequency": "frequency",
            "HSK Level": "hsk",
            "Alphabetical": "alphabetical"
        }
        sort_by = sort_map[self.sort_combo.currentText()]
        
        # Get words
        self.current_words = self.app.get_video_words(
            self.current_video_id,
            sort_by=sort_by
        )
        
        # Clear all lists
        self.all_words_list.clear()
        for hsk_list in self.hsk_lists.values():
            hsk_list.clear()
        self.non_hsk_list.clear()
        
        # Populate lists
        for word in self.current_words:
            # Texto formateado con espacio
            display_text = f"{word['chinese']}   {word['pinyin']}   ({word['frequency']}x)"
            
            item = QListWidgetItem(display_text)
            item.setData(Qt.UserRole, word)
            
            # --- COLORES DINÁMICOS EN LA LISTA ---
            status = word.get('status', 'unknown')
            
            if status == 'known':
                # Fondo verde muy oscuro, texto verde pastel
                item.setBackground(QColor("#152615")) 
                item.setForeground(QColor("#A5D6A7")) 
            elif status == 'practice':
                # Fondo naranja muy oscuro, texto naranja pastel
                item.setBackground(QColor("#262010"))
                item.setForeground(QColor("#FFE082"))
            elif status == 'unknown':
                # Fondo normal (transparente/oscuro), texto rojo pastel suave
                item.setBackground(QColor("#1E1E1E"))
                item.setForeground(QColor("#EF9A9A"))
            
            # Add to all words
            self.all_words_list.addItem(item.clone())
            
            # Add to HSK-specific list
            hsk_level = word.get('hsk_level')
            if hsk_level and 1 <= hsk_level <= 6:
                self.hsk_lists[hsk_level].addItem(item.clone())
            else:
                self.non_hsk_list.addItem(item.clone())
                
    def show_word_details(self, item):
        """Muestra los detalles de la palabra seleccionada de forma segura"""
        word_data = item.data(Qt.UserRole)
        
        if not word_data:
            return
        
        # Guardamos el ID
        self.current_word_id = word_data.get('word_id') or word_data.get('id')
        
        # Obtener detalles completos de la base de datos
        details = self.app.get_word_details(
            self.current_word_id,
            self.current_video_id
        )
        
        # --- CORRECCIÓN HANZI: Respaldo de datos ---
        # Si 'details' falla o viene vacío, usamos 'word_data' que viene de la lista y sabemos que sí tiene datos
        safe_details = details if details else {}
        
        chinese_word = safe_details.get('chinese') or safe_details.get('word') or word_data.get('chinese') or "---"
        pinyin = safe_details.get('pinyin') or word_data.get('pinyin') or ""
        translation = safe_details.get('translation') or safe_details.get('meaning') or safe_details.get('definition') or "No disponible"
        hsk_level = safe_details.get('hsk_level') or word_data.get('hsk_level')
        status = safe_details.get('status') or word_data.get('status') or 'unknown'
        
        # --- ACTUALIZACIÓN DE TEXTOS ---
        self.word_chinese.setText(chinese_word)
        self.word_pinyin.setText(pinyin)
        self.word_translation.setText(translation)
        
        # --- NUEVO: COLOR DEL PINYIN DINÁMICO ---
        # Definimos el color del texto pinyin según el estado
        pinyin_color = "#E0E0E0" # Blanco/Gris por defecto
        if status == 'known':
            pinyin_color = "#81C784" # Verde pastel
        elif status == 'practice':
            pinyin_color = "#FFD54F" # Amarillo pastel
        elif status == 'unknown':
            pinyin_color = "#E57373" # Rojo pastel
            
        self.word_pinyin.setStyleSheet(f"color: {pinyin_color}; font-style: italic; font-size: 18px; margin-bottom: 5px;")

        # Texto HSK
        hsk_text = f"Nivel HSK: {hsk_level}" if hsk_level else "No está en HSK"
        if hasattr(self, 'word_hsk'):
            self.word_hsk.setText(hsk_text)
        
        # --- CORRECCIÓN BOTONES: Estilos Completos ---
        self.reset_status_buttons() # Primero los ponemos en modo "borde"
        
        # Al activarlos, debemos REPETIR el border-radius y padding, si no, se vuelven cuadrados
        if status == 'known':
            self.btn_known.setStyleSheet("""
                QPushButton { background-color: #4CAF50; color: white; border: 1px solid #4CAF50; border-radius: 15px; padding: 6px; font-weight: bold; }
            """)
        elif status == 'practice':
            self.btn_practice.setStyleSheet("""
                QPushButton { background-color: #FFC107; color: black; border: 1px solid #FFC107; border-radius: 15px; padding: 6px; font-weight: bold; }
            """)
        elif status == 'unknown':
            self.btn_unknown.setStyleSheet("""
                QPushButton { background-color: #EF5350; color: white; border: 1px solid #EF5350; border-radius: 15px; padding: 6px; font-weight: bold; }
            """)
        
        # --- MOSTRAR EJEMPLOS ---
        examples_html = "<h3 style='color: #DDD;'>Ejemplos en el video:</h3>"
        occurrences = safe_details.get('occurrences', [])
        
        if not occurrences:
            examples_html += "<p style='color: #888;'>No se encontraron ejemplos de uso.</p>"
        else:
            for occ in occurrences[:10]:
                sentence = occ.get('sentence', '')
                timestamp = occ.get('timestamp')
                
                # Resaltar la palabra en azul claro dentro de la frase
                if chinese_word != "---":
                    highlighted = sentence.replace(
                        chinese_word,
                        f"<b style='color: #64B5F6; font-size: 18px;'>{chinese_word}</b>"
                    )
                else:
                    highlighted = sentence
                
                time_str = f" <span style='color: #666; font-size: 12px;'>[{int(timestamp)}s]</span>" if timestamp is not None else ""
                examples_html += f"<p style='margin-bottom: 12px; color: #BBB;'>• {highlighted}{time_str}</p>"
        
        self.examples_text.setHtml(examples_html)

    def reset_status_buttons(self):
        """Restablece los botones a su estilo base moderno (solo bordes, sin relleno)"""
        # Estilo base para el botón KNOWN (Verde)
        self.btn_known.setStyleSheet("""
            QPushButton {
                background-color: #1E2E1E; 
                color: #81C784; 
                border: 1px solid #4CAF50;
                border-radius: 15px; 
                padding: 6px; 
                font-weight: bold;
            }
            QPushButton:hover { background-color: #2E7D32; color: white; }
        """)
        
        # Estilo base para el botón PRACTICE (Amarillo/Naranja)
        self.btn_practice.setStyleSheet("""
            QPushButton {
                background-color: #2E2810; 
                color: #FFD54F; 
                border: 1px solid #FFC107;
                border-radius: 15px; 
                padding: 6px; 
                font-weight: bold;
            }
            QPushButton:hover { background-color: #FFB300; color: black; }
        """)
        
        # Estilo base para el botón UNKNOWN (Rojo)
        self.btn_unknown.setStyleSheet("""
            QPushButton {
                background-color: #3E2723; 
                color: #E57373; 
                border: 1px solid #F44336;
                border-radius: 15px; 
                padding: 6px; 
                font-weight: bold;
            }
            QPushButton:hover { background-color: #F44336; color: white; }
        """)

    def set_word_status(self, status):
        """Set status for current word y actualiza la UI inmediatamente"""
        if not hasattr(self, 'current_word_id'):
            return
        
        self.app.update_word_status(self.current_word_id, status)
        
        # 1. Actualizar la lista (para que cambie el color en la lista de la izquierda)
        self.refresh_word_list()
        
        # 2. Actualizar visualmente el PINYIN inmediatamente
        pinyin_colors = {'known': "#81C784", 'practice': "#FFD54F", 'unknown': "#E57373"}
        pinyin_color = pinyin_colors.get(status, "#E0E0E0")
        self.word_pinyin.setStyleSheet(f"color: {pinyin_color}; font-style: italic; font-size: 18px; margin-bottom: 5px;")

        # 3. Actualizar BOTONES (Estilos completos para mantener la forma redonda)
        self.reset_status_buttons()
        
        if status == 'known':
            self.btn_known.setStyleSheet("""
                QPushButton { background-color: #4CAF50; color: white; border: 1px solid #4CAF50; border-radius: 15px; padding: 6px; font-weight: bold; }
            """)
        elif status == 'practice':
            self.btn_practice.setStyleSheet("""
                QPushButton { background-color: #FFC107; color: black; border: 1px solid #FFC107; border-radius: 15px; padding: 6px; font-weight: bold; }
            """)
        elif status == 'unknown':
            self.btn_unknown.setStyleSheet("""
                QPushButton { background-color: #EF5350; color: white; border: 1px solid #EF5350; border-radius: 15px; padding: 6px; font-weight: bold; }
            """)
        
        self.status_bar.showMessage(f"Word marked as {status}", 2000)
    
    def closeEvent(self, event):
        """Handle application close"""
        self.app.close()
        event.accept()


if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

