#!/bin/bash

# 1. Definir la ruta base del proyecto
PROJECT_DIR="/media/ivan-mart/14c29074-e335-44af-8558-d64a3eac9128/AppChino"
cd "$PROJECT_DIR" || exit

echo "--- 🚀 INICIANDO CONFIGURACIÓN COMPLETA DE APPCHINO ---"

# 2. Crear entorno virtual si no existe
if [ ! -d "venv" ]; then
    echo "📦 Creando entorno virtual (venv)..."
    python3 -m venv venv
fi

# 3. Activar entorno virtual
echo "🔄 Activando entorno..."
source venv/bin/activate

# 4. Instalar dependencias
echo "📥 Instalando/Actualizando librerías (esto puede tardar)..."
pip install --upgrade pip
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
else
    echo "⚠️ requirements.txt no encontrado. Instalando básicos..."
    pip install PyQt5 opencv-python openai-whisper jieba pydub requests yt-dlp pypinyin opencc-python-reimplemented pandas
fi

# 5. Asegurar estructura de carpetas
echo "📂 Verificando carpetas de datos..."
mkdir -p src/data
mkdir -p src/core
mkdir -p src/ui
mkdir -p src/scripts

# 6. Gestión de archivos de datos (HSK y Diccionario)
echo "📑 Comprobando bases de datos..."

# Generar HSK si no existe
if [ ! -f "src/data/hsk_data.json" ]; then
    echo "🔨 Creando archivo HSK básico..."
    # Esto crea un archivo HSK mínimo para que la app no explote al iniciar
    echo '{"你好": 1, "谢谢": 1}' > src/data/hsk_data.json
fi

# Verificar el diccionario que bajaste manualmente
if [ ! -f "src/data/cedict.txt" ]; then
    echo "❌ ERROR: No encuentro 'src/data/cedict.txt'."
    echo "Por favor, asegúrate de que el archivo que bajaste esté en:"
    echo "$PROJECT_DIR/src/data/cedict.txt"
    exit 1
else
    echo "✅ Diccionario cedict.txt encontrado."
fi

# 7. Ejecución de la aplicación
echo "--- ✅ TODO LISTO. LANZANDO APP ---"

# Esta línea es CLAVE: le dice a Python dónde buscar tus archivos .py
export PYTHONPATH=$PYTHONPATH:"$PROJECT_DIR":"$PROJECT_DIR/src"

# Lanzar el proceso principal
python3 main.py
