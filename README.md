# Explorador de datos Onclusive en Streamlit

Aplicación sencilla para consolidar y explorar bases mensuales de menciones exportadas desde Onclusive.

## Qué hace

- Permite subir varios archivos Excel por mes.
- También puede leer una carpeta local con subcarpetas mensuales.
- Consolida todo en una sola tabla.
- Detecta el tema desde el nombre del archivo.
- Filtra por mes, tema, sentimiento, fuente, tipo de medio, país, idioma, fecha, reach mínimo y palabra clave.
- Genera gráficos rápidos y permite descargar los resultados filtrados.

## Estructura sugerida de carpetas

```text
Explorador-Onclusive/
├── .streamlit/
│   └── config.toml
├── app.py
├── requirements.txt
├── README.md
├── .gitignore
├── data/
└── exports/
```

## Formato esperado de archivos

Cada archivo Excel debe contener, idealmente, columnas como estas:

`id, Title, Detail, Link, Source, Update date, Publish date, Sentiment, Ranking, Media type, Tags, Country, Language, Audience, Reach, Interactions, Notes, Author name, Author handle (@username), Author URL, Gender, Age, Bio, City, fecha`

La app intenta completar columnas faltantes para evitar errores.

## Ejecutar localmente

### 1) Crear entorno virtual

**Windows (PowerShell):**

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

**Windows (CMD):**

```cmd
python -m venv .venv
.venv\Scripts\activate.bat
```

### 2) Instalar dependencias

```bash
pip install -r requirements.txt
```

### 3) Ejecutar la app

```bash
streamlit run app.py
```

## Uso recomendado

### Opción A: Carga manual por mes
1. Escribe el nombre del mes, por ejemplo `12-Diciembre`.
2. Sube todos los Excel de ese mes.
3. Pulsa **Agregar archivos subidos al consolidado**.
4. Repite con cada mes.

### Opción B: Leer carpeta local completa
Si ejecutas la app en tu computadora o servidor, escribe una ruta como:

```text
C:\PROYECTOS_CIE\SmartDataIAFUSADES\EscuchaSocial
```

La app buscará Excel en subcarpetas como `4-Abril`, `5-Mayo`, etc.

## Subir a GitHub

Sube estos archivos y carpetas:
- `app.py`
- `requirements.txt`
- `README.md`
- `.gitignore`
- `.streamlit/config.toml`
- `data/.gitkeep`
- `exports/.gitkeep`

No subas las bases reales si contienen datos sensibles o si el repositorio será público.

## Despliegue sugerido

Puedes desplegarlo en Streamlit Community Cloud o ejecutarlo en un servidor interno.
