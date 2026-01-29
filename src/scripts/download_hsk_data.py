import requests, json, os

def fix_hsk():
    # Fuente alternativa muy estable
    url = "https://raw.githubusercontent.com/pujandev/hsk-vocabulary/master/hsk_vocab.json"
    path = "src/data/hsk_data.json"
    try:
        r = requests.get(url, timeout=10)
        data = r.json() # Estructura: {"hsk1": [{"hanzi": "我", ...}, ...]}
        final_hsk = {}
        for level_key, words in data.items():
            level = int(level_key.replace("hsk", ""))
            for entry in words:
                final_hsk[entry['hanzi']] = level
        with open(path, "w", encoding="utf-8") as f:
            json.dump(final_hsk, f, ensure_ascii=False)
        print("✅ HSK cargado correctamente.")
    except:
        print("❌ Error en descarga. Usa la Opción A (copiar/pegar).")

if __name__ == "__main__": fix_hsk()
