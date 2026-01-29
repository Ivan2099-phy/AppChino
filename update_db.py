#!/usr/bin/env python3
import sqlite3
import json
import os
import re

json_path = "src/data/hsk_data.json"
db_path = "data/chinese_video.db"

def extract_level(level_data):
    """Extrae el número de nivel de formatos como ['new-1', 'old-3'] o '1'"""
    if isinstance(level_data, list) and len(level_data) > 0:
        # Priorizamos el nivel 'new' si existe, si no el primero que tenga un número
        for l in level_data:
            num = re.findall(r'\d+', str(l))
            if num: return int(num[0])
    elif isinstance(level_data, (int, str)):
        num = re.findall(r'\d+', str(level_data))
        if num: return int(num[0])
    return None

def run_update():
    if not os.path.exists(json_path):
        print(f"❌ No se encuentra {json_path}")
        return

    hsk_map = {}
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        
        print(f"Procesando {len(data)} entradas del JSON...")
        for entry in data:
            # En complete.min.json: 's' es simplified, 'l' es level
            # En complete.json: 'simplified' es el campo, 'level' es el campo
            hanzi = entry.get('s') or entry.get('simplified')
            raw_lvl = entry.get('l') or entry.get('level')
            
            if hanzi and raw_lvl:
                level = extract_level(raw_lvl)
                if level:
                    hsk_map[hanzi] = level

    if not hsk_map:
        print("❌ Sigo sin encontrar palabras. Asegúrate de que el archivo no esté vacío.")
        return

    if not os.path.exists(db_path):
        print(f"❌ No se encuentra la DB en {db_path}")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print(f"Sincronizando {len(hsk_map)} palabras con la base de datos...")
    cursor.execute("BEGIN TRANSACTION")
    for hanzi, level in hsk_map.items():
        cursor.execute("UPDATE words SET hsk_level = ? WHERE chinese = ?", (level, hanzi))
    conn.commit()

    cursor.execute("SELECT COUNT(*) FROM words WHERE hsk_level > 0")
    count = cursor.fetchone()[0]
    conn.close()

    print(f"✅ ¡Éxito total!")
    print(f"📊 Se actualizaron {count} palabras en tu base de datos.")

if __name__ == "__main__":
    run_update()
