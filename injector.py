import os
import csv
import shutil
from collections import defaultdict

# --- CONFIGURACIÓN ---
CSV_FILE = os.path.join('Textos', 'traducciones.csv')
SOURCE_DIR = 'ingles'
OUTPUT_DIR = 'traducido'
# La columna que el usuario debe añadir con las traducciones
TRANSLATION_COLUMN_NAME = 'translated_content'

def get_original_full_string(rows):
    """Reconstruye la cadena de texto original completa a partir de sus segmentos."""
    # Primero, obtenemos el patrón original completo para poder encontrarlo luego.
    # Esto es necesario porque el split puede haber alterado los patrones de comillas.
    text_pattern = re.compile(r'"English":"(.*?)","')

    with open(rows[0]['source_file'], 'r', encoding='utf-8') as f:
        content = f.read()

    string_id = rows[0]['string_id']

    # Encontramos todas las cadenas y nos quedamos con la que corresponde a nuestro ID.
    # Asumimos que el orden de finditer es el mismo que el de la extracción.
    found_strings = [match.group(1) for match in text_pattern.finditer(content)]

    # El string_id empieza en 1, los índices de lista en 0.
    if int(string_id) <= len(found_strings):
        return found_strings[int(string_id) - 1]

    # Fallback por si algo falla (no debería ocurrir)
    print(f"Advertencia: No se pudo reconstruir la cadena original para string_id {string_id}. Usando método de fallback.")
    return "".join(row['content'] for row in rows)


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
            original_string = "".join(seg['content'] for seg in segments)

            new_string_parts = []
            for seg in segments:
                if seg['type'] == 'text':
                    # Usar la traducción si existe, si no, el original
                    translated = seg.get(TRANSLATION_COLUMN_NAME, seg['content']).strip()
                    # Si la traducción está vacía, usar el texto original.
                    new_string_parts.append(translated if translated else seg['content'])
                else: # Es un 'marker'
                    new_string_parts.append(seg['content'])

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
    # Necesitamos importar 're' para la función get_original_full_string
    import re
    main()
