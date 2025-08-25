import os
import re
import csv

# --- CONFIGURACIÓN ---
INPUT_DIR = 'ingles'
OUTPUT_DIR = 'Textos'
OUTPUT_CSV_FILE = os.path.join(OUTPUT_DIR, 'traducciones.csv')

# Regex para encontrar la cadena de texto completa a extraer.
# "English":"<contenido>",
TEXT_PATTERN = re.compile(r'"English":"(.*?)","')

# Regex para dividir la cadena en texto y marcadores.
# El paréntesis captura los marcadores y re.split los conserva en la lista.
SEGMENT_PATTERN = re.compile(r'(<[^>]+>)')

def main():
    """
    Función principal del script de extracción por segmentación.
    """
    print("Iniciando el proceso de extracción por segmentación.")

    if not os.path.isdir(INPUT_DIR):
        print(f"Error: El directorio de entrada '{INPUT_DIR}' no fue encontrado.")
        return

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    print(f"Directorio de salida: '{OUTPUT_DIR}'")

    csv_rows = []
    string_id_counter = 0

    # Iterar sobre todos los archivos del directorio de entrada
    for filename in os.listdir(INPUT_DIR):
        if not filename.endswith('.txt'):
            continue

        filepath = os.path.join(INPUT_DIR, filename)
        print(f"Procesando archivo: {filepath}")

        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        # Encontrar todas las cadenas de texto que coincidan con el patrón
        for match in TEXT_PATTERN.finditer(content):
            string_id_counter += 1
            full_string = match.group(1)

            # Dividir la cadena en segmentos de texto y marcadores
            segments = SEGMENT_PATTERN.split(full_string)

            sequence_counter = 0
            for i, segment in enumerate(segments):
                # Ignorar segmentos vacíos que pueden resultar del split
                if not segment:
                    continue

                # Determinar si el segmento es texto o marcador
                # re.split con un grupo de captura alterna texto y delimitador
                # Los textos están en los índices pares, los marcadores en los impares.
                segment_type = 'marker' if i % 2 != 0 else 'text'

                csv_rows.append([
                    filepath,
                    string_id_counter,
                    sequence_counter,
                    segment_type,
                    segment
                ])
                sequence_counter += 1

    if not csv_rows:
        print("No se encontraron textos que coincidan con el patrón.")
        return

    # Escribir todas las filas en el archivo CSV
    header = ['source_file', 'string_id', 'sequence', 'type', 'content']
    with open(OUTPUT_CSV_FILE, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(csv_rows)

    print(f"\nProceso de extracción completado.")
    print(f"Se han procesado {string_id_counter} cadenas de texto.")
    print(f"Los segmentos para traducir han sido guardados en: {OUTPUT_CSV_FILE}")

if __name__ == '__main__':
    main()
