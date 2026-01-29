import sys
import os
import logging

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt

# Import principal UI
from src.ui.main_window import MainWindow


def setup_environment():
    """
    Configura rutas, variables de entorno y logging.
    """
    # Path base del proyecto
    base_dir = os.path.dirname(os.path.abspath(__file__))

    # Añadir src al PYTHONPATH
    src_path = os.path.join(base_dir, "src")
    if src_path not in sys.path:
        sys.path.insert(0, src_path)

    # Directorios necesarios
    required_dirs = [
        "data",
        "temp",
        "exports",
        "models",
        os.path.join("data", "hsk"),
        os.path.join("data", "cedict"),
    ]

    for dir_name in required_dirs:
        os.makedirs(os.path.join(base_dir, dir_name), exist_ok=True)

    # Configuración básica de logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    logging.info("Entorno inicializado correctamente")


def apply_theme(app: QApplication):
    """
    Aplica tema visual básico (oscuro).
    Puede reemplazarse por QSS externo.
    """
    app.setStyle("Fusion")

    dark_palette = app.palette()
    dark_palette.setColor(dark_palette.Window, Qt.black)
    dark_palette.setColor(dark_palette.WindowText, Qt.white)
    dark_palette.setColor(dark_palette.Base, Qt.darkGray)
    dark_palette.setColor(dark_palette.AlternateBase, Qt.black)
    dark_palette.setColor(dark_palette.ToolTipBase, Qt.white)
    dark_palette.setColor(dark_palette.ToolTipText, Qt.white)
    dark_palette.setColor(dark_palette.Text, Qt.white)
    dark_palette.setColor(dark_palette.Button, Qt.darkGray)
    dark_palette.setColor(dark_palette.ButtonText, Qt.white)
    dark_palette.setColor(dark_palette.BrightText, Qt.red)
    dark_palette.setColor(dark_palette.Highlight, Qt.blue)
    dark_palette.setColor(dark_palette.HighlightedText, Qt.black)

    app.setPalette(dark_palette)


def main():
    """
    Punto de entrada principal de la aplicación.
    """
    setup_environment()

    # Crear aplicación Qt
    app = QApplication(sys.argv)
    app.setApplicationName("Chinese Video Analyzer")
    app.setOrganizationName("ChineseLearner")
    app.setOrganizationDomain("chineselearner.local")

    apply_theme(app)

    # Crear ventana principal
    window = MainWindow()
    window.show()

    # Procesar argumentos CLI (ej. archivo de video)
    if len(sys.argv) > 1:
        input_path = sys.argv[1]
        if os.path.exists(input_path):
            logging.info(f"Procesando archivo desde CLI: {input_path}")
            window.process_video_from_cli(input_path)
        else:
            logging.warning(f"Archivo no encontrado: {input_path}")

    # Ejecutar loop principal
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()

