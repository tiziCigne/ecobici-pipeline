# Decisiones del pipeline Ecobici

## 1. Exploración de los archivos (Tarea 1)

Exploré los archivos con el script `explorar.py`, leyendo cada CSV directamente
desde el ZIP con pandas (`nrows=1000`, `dtype=str`) y contando el total de filas
por bloques (`chunksize=500000`).

El ZIP entregado (`DatosEcobici.zip`) contiene los 6 archivos esperados: los
recorridos de cada año vienen en un ZIP propio con un único CSV adentro, y los
usuarios vienen como CSV sueltos. No faltan archivos ni hay archivos de más.

### Recorridos

| Aspecto | 2016 | 2019 | 2024 |
|---|---|---|---|
| Nombre del archivo dentro del ZIP | `recorridos-realizados-2016.zip` → `recorridos-realizados-2016.csv` | `recorridos-realizados-2019.zip` → `trips_2019.csv` | `recorridos-realizados-2024.zip` → `badata_ecobici_recorridos_realizados_2024.csv` |
| Separador de columnas (, o ;) | `,` | `,` | `,` |
| Columnas | 15: `periodo`, `genero_usuario`, `fecha_origen_recorrido`, `id_estacion_origen`, `nombre_estacion_origen`, `long_estacion_origen`, `lat_estacion_origen`, `domicilio_estacion_origen`, `duracion_recorrido`, `fecha_destino_recorrido`, `id_estacion_destino`, `nombre_estacion_destino`, `long_estacion_destino`, `lat_estacion_destino`, `domicilio_estacion_destino` | 18: `Unnamed: 0`, `Id_recorrido`, `duracion_recorrido`, `fecha_origen_recorrido`, `id_estacion_origen`, `nombre_estacion_origen`, `direccion_estacion_origen`, `long_estacion_origen`, `lat_estacion_origen`, `fecha_destino_recorrido`, `id_estacion_destino`, `nombre_estacion_destino`, `direccion_estacion_destino`, `long_estacion_destino`, `lat_estacion_destino`, `id_usuario`, `modelo_bicicleta`, `género` | 17: `id_recorrido`, `duracion_recorrido`, `fecha_origen_recorrido`, `id_estacion_origen`, `nombre_estacion_origen`, `direccion_estacion_origen`, `long_estacion_origen`, `lat_estacion_origen`, `fecha_destino_recorrido`, `id_estacion_destino`, `nombre_estacion_destino`, `direccion_estacion_destino`, `long_estacion_destino`, `lat_estacion_destino`, `id_usuario`, `modelo_bicicleta`, `genero` |
| Formato de fecha y hora | `2016-01-01 02:21:41` (pendiente de verificar el orden mes/día) | `2019-02-27 19:44:42` (AAAA-MM-DD HH:MM:SS) | `2024-01-23 18:36:00` (AAAA-MM-DD HH:MM:SS) |
| ¿Trae la duración del viaje? ¿En qué unidad? | Sí, texto tipo timedelta: `0 days 00:16:29.000000000` | Sí, en segundos, con coma de miles: `2,814` | Sí, en segundos: `568` |
| ¿Trae id de usuario? | No | Sí, con sufijo: `6243BAEcobici` | Sí, con decimal: `992557.0` |
| Cantidad total de filas | 596.807 | 6.217.004 | 3.559.284 |

### Usuarios

| Aspecto | 2016 | 2019 | 2024 |
|---|---|---|---|
| Nombre del archivo dentro del ZIP | `usuarios-ecobici-2016.csv` | `usuarios_ecobici_2019.csv` | `usuarios_ecobici_2024.csv` |
| Separador de columnas (, o ;) | `,` | `,` | `,` |
| Nombres de las columnas | `id_usuario`, `genero_usuario`, `edad_usuario`, `fecha_alta`, `hora_alta` | `ID_usuario`, `genero_usuario`, `edad_usuario`, `fecha_alta`, `hora_alta` | `id_usuario`, `genero_usuario`, `edad_usuario`, `fecha_alta`, `hora_alta` |
| Formato de fecha de alta | `01-01-16` (año de 2 dígitos, pendiente de verificar el orden) | `2019-12-31` (AAAA-MM-DD) | `2024-01-18` (AAAA-MM-DD) |
| Formato de hora de alta | 12 horas con AM/PM: `3:45:19 AM` | 24 horas: `10:46:10` | 24 horas: `09:21:02` |
| Valores de género | `M`, `F` | `MALE`, `FEMALE`, `OTHER` | `MALE`, `FEMALE`, `OTHER` |
| Cantidad de filas | 39.481 | 83.600 | 197.077 |

### Hallazgos que afectan a las capas siguientes

**Identificadores**
- Los recorridos de 2016 no tienen id de viaje ni id de usuario. Por eso los
  viajes de 2016 no se van a poder vincular con los datos de usuarios.
- En 2019 todos los ids de los recorridos (viaje, estación y usuario) tienen el
  sufijo `BAEcobici` (por ejemplo `6243BAEcobici`), y en 2024 el id de usuario
  viene con decimal (`992557.0`). En los archivos de usuarios los ids no tienen
  esos agregados (`627966`).
- Algunos nombres de columna cambian solo en mayúsculas: `ID_usuario` en los
  usuarios de 2019 frente a `id_usuario` en los demás años, e `Id_recorrido`
  (2019) frente a `id_recorrido` (2024).

**Duración**
- En 2019 y 2024 la duración está en segundos y coincide con la diferencia entre
  la fecha de destino y la de origen.
- En 2016 la duración viene como texto tipo `0 days 00:16:29.000000000` y, en las
  filas que revisé, no coincide con esa diferencia (por ejemplo, 02:21:41 →
  02:48:05 son 26:24, pero la columna dice 16:29).
- En 2019 algunas duraciones traen coma de miles (`2,814`), así que hay que
  quitarla antes de convertir a número.

**Género**
- La columna de género tiene un nombre distinto en cada año de recorridos
  (`genero_usuario`, `género`, `genero`). Los valores son `M`/`F` en 2016 y
  `MALE`/`FEMALE`/`OTHER` en 2019 y 2024, y en 2024 aparecen valores vacíos.

**Estaciones y otras columnas**
- Los nombres de estación tienen estilos distintos: sin prefijo en 2016
  (`Tribunales`) y con un código numérico como prefijo en 2019 y 2024
  (`005 - Plaza Italia`, `308 - SAN MARTIN II`). En 2024 encontré un caso en que
  el código del nombre no coincide con el id de la estación (id 513, nombre
  `308 - SAN MARTIN II`); queda pendiente revisar si es un caso aislado.
- 2019 tiene una columna `Unnamed: 0` con valores 1, 2, 3…, que es un índice sin
  significado.
- En 2019 las coordenadas de destino están desplazadas: `long_estacion_destino`
  trae una latitud y `lat_estacion_destino` trae el par latitud,longitud. Estas
  columnas no forman parte del esquema canónico.
- En la muestra de 2024 hay un viaje de 0 segundos entre dos estaciones distintas.

**Volumen**
- La cantidad de viajes varía mucho entre años: 596.807 en 2016, 6.217.004 en
  2019 y 3.559.284 en 2024.

## 2. Decisiones tomadas
  - **Ubicación de los archivos originales.** La cátedra entregó un único ZIP
  (`DatosEcobici.zip`) con los 6 archivos adentro. Saqué esos 6 archivos a
  `data/raw/` sin descomprimir los ZIP de recorridos, para que la carpeta quede
  igual que si se hubieran descargado del portal, como supone el enunciado.
  Verifiqué con `explorar.py` que las columnas y las cantidades de filas no
  cambiaron.