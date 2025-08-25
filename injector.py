import os
import csv
import shutil
from collections import defaultdict

# --- CONFIGURACIÓN ---
CSV_FILE = os.path.join('Textos', 'traducciones.csv')
SOURCE_DIR = 'ingles'
OUTPUT_DIR = 'traducido'
# La columna que el usuario debe añadir con las traducciones
TRANSLATION_COLUMN_NAME = 'translated_text'

def main():
    """
    Función principal del script de inyección por segmentación.
    """
    print("Iniciando el proceso de inyección de textos por segmentación.")

    if not os.path.exists(CSV_FILE):
        print(f"Error: El archivo de traducciones '{CSV_FILE}' no fue encontrado.")
        return

    # 1. Leer el CSV y agrupar todas las filas por archivo de origen
    rows_by_source_file = defaultdict(list)
    try:
        with open(CSV_FILE, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            # Verificar que la columna de traducción exista
            if TRANSLATION_COLUMN_NAME not in reader.fieldnames:
                print(f"Error: El archivo CSV no contiene la columna '{TRANSLATION_COLUMN_NAME}'.")
                print("Por favor, añade una columna con ese nombre y rellénala.")
                return
            for row in reader:
                rows_by_source_file[row['source_file']].append(row)
    except Exception as e:
        print(f"Error leyendo el archivo CSV: {e}")
        return

    # 2. Crear/limpiar el directorio de salida
    if os.path.exists(OUTPUT_DIR):
        shutil.rmtree(OUTPUT_DIR)
    os.makedirs(OUTPUT_DIR)
    print(f"Directorio de salida '{OUTPUT_DIR}' creado/limpiado.")

    # 3. Procesar cada archivo
    for source_file, rows in rows_by_source_file.items():
        dest_file = os.path.join(OUTPUT_DIR, os.path.basename(source_file))
        print(f"\nProcesando archivo: {source_file} -> {dest_file}")

        shutil.copy(source_file, dest_file)

        with open(dest_file, 'r', encoding='utf-8') as f:
            file_content = f.read()

        # Agrupar las filas de este archivo por string_id
        strings_to_reconstruct = defaultdict(list)
        for row in rows:
            strings_to_reconstruct[row['string_id']].append(row)

        modified_count = 0
        # 4. Reconstruir cada cadena de texto para el archivo actual
        for string_id, segments in strings_to_reconstruct.items():
            # Ordenar los segmentos por su secuencia
            segments.sort(key=lambda x: int(x['sequence']))

            # Reconstruir la cadena original y la traducida
            original_string = "".join(seg['text_content'] + seg['marker_content'] for seg in segments)

            new_string_parts = []
            for seg in segments:
                # Si hay contenido de texto, es una fila de texto
                if seg['text_content']:
                    # Usar la traducción si existe y no está vacía, si no, el original
                    translated = seg.get(TRANSLATION_COLUMN_NAME, "").strip()
                    new_string_parts.append(translated if translated else seg['text_content'])
                else: # Es una fila de marcador
                    new_string_parts.append(seg['marker_content'])

            new_string = "".join(new_string_parts)

            # Reemplazar en el contenido del archivo
            # Usamos el patrón completo para el reemplazo seguro
            original_pattern = f'"English":"{original_string}","'
            new_pattern = f'"English":"{new_string}","'

            if original_pattern in file_content:
                file_content = file_content.replace(original_pattern, new_pattern, 1)
                modified_count += 1
            else:
                print(f"  ADVERTENCIA: No se encontró el patrón original para string_id {string_id} en {source_file}.")
                print(f"  Buscando: {original_pattern}")


        # Escribir el contenido modificado de vuelta al archivo
        with open(dest_file, 'w', encoding='utf-8') as f:
            f.write(file_content)

        print(f"  Se han aplicado {modified_count} reconstrucciones de texto.")

    print("\nProceso de inyección completado.")
    print(f"Los archivos traducidos se encuentran en la carpeta: '{OUTPUT_DIR}'")

if __name__ == '__main__':
    main()
