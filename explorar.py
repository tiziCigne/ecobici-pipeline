"""
explorar.py - Tarea 1: exploración de los archivos de Ecobici.
Solo LEE data/raw/DatosEcobici.zip: no extrae, no modifica ni mueve nada.
"""

import io
import sys
import zipfile
from pathlib import Path

import pandas as pd

RUTA_ZIP = Path("data/raw/DatosEcobici.zip")
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
    """Abre un CSV en modo lectura, entrando en los ZIP anidados si hace falta."""
    zf = zipfile.ZipFile(RUTA_ZIP)
    for nombre_zip in cadena[:-1]:
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

    # Las 3 primeras filas muestran ejemplos crudos de fecha, hora, duración e id de usuario.
    print("\nPrimeras 3 filas, tal cual vienen:")
    print(df.head(3).T.to_string())

    for col in df.columns:
        nombre = col.lower()
        if "genero" in nombre or "género" in nombre or "gender" in nombre:
            print(f"\nvalue_counts de {col!r}:")
            print(df[col].value_counts().to_string())
        if "edad" in nombre or "age" in nombre:
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
    print("CONTENIDO DE", RUTA_ZIP.name)
    with zipfile.ZipFile(RUTA_ZIP) as zf:
        csvs = listar_zip(zf)
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