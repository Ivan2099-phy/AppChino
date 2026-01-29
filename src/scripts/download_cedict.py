import requests
import os
import gzip

def download_cedict():
    # Link oficial de descarga directa
    URL = "https://www.mdbg.net/chinese/export/cedict/cedict_ts.u8.gz"
    OUTPUT_PATH = "src/data/cedict.txt"
    os.makedirs("src/data", exist_ok=True)

    print("Descargando diccionario CC-CEDICT desde MDBG...")
    headers = {'User-Agent': 'Mozilla/5.0'} # Engañamos al servidor para que nos deje bajarlo
    try:
        r = requests.get(URL, headers=headers, stream=True, timeout=20)
        r.raise_for_status()
        
        with open(OUTPUT_PATH, 'wb') as f:
            f.write(gzip.decompress(r.content))
            
        print("✅ cedict.txt generado con éxito.")
    except Exception as e:
        print(f"❌ Error crítico: No se pudo bajar el diccionario. Verifica tu internet. {e}")

if __name__ == "__main__":
    download_cedict()
