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
        self.word_chinese.setFont(QFont("Arial", 24, QFont.Bold))
        details_layout.addWidget(self.word_chinese)
        
        self.word_pinyin = QLabel("")
        self.word_pinyin.setFont(QFont("Arial", 14))
        details_layout.addWidget(self.word_pinyin)
        
        self.word_translation = QLabel("")
        self.word_translation.setFont(QFont("Arial", 12))
        details_layout.addWidget(self.word_translation)
        
        self.word_hsk = QLabel("")
        details_layout.addWidget(self.word_hsk)
        
        # Status buttons
        status_layout = QHBoxLayout()
        status_layout.addWidget(QLabel("Status:"))
        
        self.btn_known = QPushButton("✓ Known")
        self.btn_known.setStyleSheet("background-color: #4CAF50; color: white;")
        self.btn_known.clicked.connect(lambda: self.set_word_status('known'))
        status_layout.addWidget(self.btn_known)
        
        self.btn_practice = QPushButton("⚡ Practice")
        self.btn_practice.setStyleSheet("background-color: #FFC107; color: white;")
        self.btn_practice.clicked.connect(lambda: self.set_word_status('practice'))
        status_layout.addWidget(self.btn_practice)
        
        self.btn_unknown = QPushButton("? Unknown")
        self.btn_unknown.setStyleSheet("background-color: #F44336; color: white;")
        self.btn_unknown.clicked.connect(lambda: self.set_word_status('unknown'))
        status_layout.addWidget(self.btn_unknown)
        
        details_layout.addLayout(status_layout)
        
        # Example sentences
        details_layout.addWidget(QLabel("Example Sentences:"))
        self.examples_text = QTextEdit()
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
            display_text = f"{word['chinese']} ({word['pinyin']}) - {word['frequency']}x"
            
            item = QListWidgetItem(display_text)
            item.setData(Qt.UserRole, word)
            
            # Color based on status
            if word['status'] == 'known':
                item.setBackground(QColor(200, 255, 200))
            elif word['status'] == 'practice':
                item.setBackground(QColor(255, 255, 200))
            elif word['status'] == 'unknown':
                item.setBackground(QColor(255, 200, 200))
            
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
        
        # Obtener detalles completos de la palabra
        details = self.app.get_word_details(
            word_data['word_id'],
            self.current_video_id
        )
        
        if not details:
            return
        
        # Almacenar ID para actualizaciones de estado
        self.current_word_id = word_data['word_id']
        
        # --- EXTRACCIÓN SEGURA DE DATOS (Evita KeyError) ---
        # Intentamos obtener el texto en chino de varias posibles llaves
        chinese_word = details.get('chinese') or details.get('word') or details.get('hanzi') or "---"
        pinyin = details.get('pinyin') or ""
        # Buscamos la traducción en 'translation', 'meaning' o 'definition'
        translation = details.get('translation') or details.get('meaning') or details.get('definition') or "No disponible"
        hsk_level = details.get('hsk_level') or details.get('hsk')
        status = details.get('status', 'unknown')
        
        # --- ACTUALIZACIÓN DE LA INTERFAZ ---
        self.word_chinese.setText(chinese_word)
        self.word_pinyin.setText(pinyin)
        self.word_translation.setText(translation)
        
        hsk_text = f"Nivel HSK: {hsk_level}" if hsk_level else "No está en HSK"
        # Si tu widget se llama self.word_hsk o self.hsk_badge, asegúrate de que el nombre coincida
        if hasattr(self, 'word_hsk'):
            self.word_hsk.setText(hsk_text)
        
        # Resaltar botones de estado
        self.reset_status_buttons()
        if status == 'known':
            self.btn_known.setStyleSheet("background-color: #2E7D32; color: white; font-weight: bold;")
        elif status == 'practice':
            self.btn_practice.setStyleSheet("background-color: #F57C00; color: white; font-weight: bold;")
        elif status == 'unknown':
            self.btn_unknown.setStyleSheet("background-color: #C62828; color: white; font-weight: bold;")
        
        # Mostrar ejemplos de uso
        examples_html = "<h3>Ejemplos en el video:</h3>"
        occurrences = details.get('occurrences', [])
        
        if not occurrences:
            examples_html += "<p>No se encontraron ejemplos de uso.</p>"
        else:
            for occ in occurrences[:10]:  # Mostrar máximo 10
                sentence = occ.get('sentence', '')
                timestamp = occ.get('timestamp')
                
                # Resaltar la palabra en la oración (si existe la palabra)
                if chinese_word != "---":
                    highlighted = sentence.replace(
                        chinese_word,
                        f"<b style='color: #2196F3; font-size: 16px;'>{chinese_word}</b>"
                    )
                else:
                    highlighted = sentence
                
                time_str = f" <small style='color: gray;'>[{int(timestamp)}s]</small>" if timestamp is not None else ""
                examples_html += f"<p style='margin-bottom: 8px;'>• {highlighted}{time_str}</p>"
        
        self.examples_text.setHtml(examples_html)
    
    def reset_status_buttons(self):
        """Reset status button styles"""
        self.btn_known.setStyleSheet("background-color: #4CAF50; color: white;")
        self.btn_practice.setStyleSheet("background-color: #FFC107; color: white;")
        self.btn_unknown.setStyleSheet("background-color: #F44336; color: white;")
    
    def set_word_status(self, status):
        """Set status for current word"""
        if not hasattr(self, 'current_word_id'):
            return
        
        self.app.update_word_status(self.current_word_id, status)
        
        # Refresh word list to update colors
        self.refresh_word_list()
        
        # Update button highlight
        self.reset_status_buttons()
        if status == 'known':
            self.btn_known.setStyleSheet("background-color: #2E7D32; color: white; font-weight: bold;")
        elif status == 'practice':
            self.btn_practice.setStyleSheet("background-color: #F57C00; color: white; font-weight: bold;")
        elif status == 'unknown':
            self.btn_unknown.setStyleSheet("background-color: #C62828; color: white; font-weight: bold;")
        
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

