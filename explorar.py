"""
explorar.py - Tarea 1: exploración de los archivos de Ecobici.
Solo LEE los archivos de data/raw/: no extrae, no modifica ni mueve nada.
"""

import io
import sys
import zipfile
from pathlib import Path

import pandas as pd

RUTA_RAW = Path("data/raw")
SALIDA = Path("exploracion_salida.txt")


def listar_zip(zf, nivel=0, cadena=(), csvs=None):
    """Muestra el contenido del ZIP (entrando en los ZIP internos) y junta los CSV."""
    if csvs is None:
        csvs = []
    for info in zf.infolist():
        print("    " * nivel + f"{info.filename}  ({info.file_size / 1024**2:.1f} MB)")
        nombre = info.filename.lower()
        if nombre.endswith(".zip"):
            # El ZIP interno se abre en memoria, sin escribirlo a disco.
            with zipfile.ZipFile(io.BytesIO(zf.read(info.filename))) as interno:
                listar_zip(interno, nivel + 1, cadena + (info.filename,), csvs)
        elif nombre.endswith(".csv") and "__macosx" not in nombre:
            csvs.append(cadena + (info.filename,))
    return csvs


def abrir(cadena):
    """Abre un CSV en modo lectura. cadena[0] es un archivo de data/raw/; si es un ZIP,
    el resto de la cadena indica cómo llegar al CSV dentro de él."""
    archivo = RUTA_RAW / cadena[0]
    if len(cadena) == 1:
        return open(archivo, "rb")  # CSV suelto en data/raw/
    zf = zipfile.ZipFile(archivo)
    for nombre_zip in cadena[1:-1]:
        zf = zipfile.ZipFile(io.BytesIO(zf.read(nombre_zip)))
    return zf.open(cadena[-1])


def leer_muestra(cadena):
    """Lee 1000 filas como texto, probando separador y encoding hasta que funcione."""
    for encoding in ("utf-8", "latin-1"):
        for sep in (",", ";"):
            try:
                with abrir(cadena) as f:
                    # dtype=str: todo como texto. keep_default_na=False: no convertir
                    # celdas vacías o "NA" en nulos; queremos ver los valores tal cual.
                    df = pd.read_csv(f, sep=sep, encoding=encoding, dtype=str,
                                     nrows=1000, keep_default_na=False)
            except UnicodeDecodeError:
                break  # este encoding no sirve: probar el siguiente
            except pd.errors.ParserError:
                continue  # este separador no sirve: probar el siguiente
            if len(df.columns) > 1:  # con el separador equivocado queda una sola columna
                return df, sep, encoding
    raise ValueError("No se pudo leer con ',' ni ';' en utf-8 ni latin-1")


def contar_filas(cadena, sep, encoding):
    """Cuenta todas las filas leyendo de a 500.000, sin cargar el archivo entero."""
    total = 0
    with abrir(cadena) as f:
        for bloque in pd.read_csv(f, sep=sep, encoding=encoding, dtype=str,
                                  usecols=[0], chunksize=500_000):
            total += len(bloque)
    return total


def analizar(cadena):
    print("\n" + "=" * 70)
    print("ARCHIVO:", " -> ".join(cadena))
    df, sep, encoding = leer_muestra(cadena)
    print(f"Separador: {sep!r}   Encoding: {encoding}")
    print("Columnas:", list(df.columns))

    # No sabemos de antemano qué columnas trae cada archivo: mostramos las 3 primeras
    # filas completas para ver los nombres y valores reales (fechas, duración, ids, etc.).
    print("\nPrimeras 3 filas, tal cual vienen:")
    print(df.head(3).T.to_string())

    # Atajo: buscamos columnas de género y edad por palabras probables en el nombre.
    # Si se llaman de otra forma, no se imprimen y lo revisamos a mano con la lista de columnas.
    for col in df.columns:
        nombre = col.lower()
        if any(palabra in nombre for palabra in ("genero", "género", "gender", "sexo")):
            print(f"\nvalue_counts de {col!r}:")
            print(df[col].value_counts().to_string())
        if any(palabra in nombre for palabra in ("edad", "age")):
            print(f"\nEjemplos de {col!r}:", df[col].head(10).tolist())

    print("\nContando filas (puede tardar)...")
    print("Total de filas:", contar_filas(cadena, sep, encoding))


class Tee:
    """Escribe en la consola y en un archivo a la vez, para poder copiar la salida."""

    def __init__(self, *destinos):
        self.destinos = destinos

    def write(self, texto):
        for destino in self.destinos:
            destino.write(texto)

    def flush(self):
        for destino in self.destinos:
            destino.flush()


def main():
    pd.set_option("display.width", 200)
    print("CONTENIDO DE", RUTA_RAW)
    csvs = []
    for archivo in sorted(RUTA_RAW.iterdir()):
        print(f"{archivo.name}  ({archivo.stat().st_size / 1024**2:.1f} MB)")
        if archivo.suffix.lower() == ".zip":
            with zipfile.ZipFile(archivo) as zf:
                listar_zip(zf, nivel=1, cadena=(archivo.name,), csvs=csvs)
        elif archivo.suffix.lower() == ".csv":
            csvs.append((archivo.name,))

    for cadena in csvs:
        try:
            analizar(cadena)
        except Exception as error:
            # Si un archivo falla, se muestra el error exacto y se sigue con el próximo.
            print(f"\n[ERROR] {' -> '.join(cadena)}: {type(error).__name__}: {error}")


if __name__ == "__main__":
    with open(SALIDA, "w", encoding="utf-8") as archivo:
        sys.stdout = Tee(sys.__stdout__, archivo)
        main()
        sys.stdout = sys.__stdout__
    print("Salida guardada en", SALIDA)