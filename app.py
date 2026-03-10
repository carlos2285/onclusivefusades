import io
import os
import re
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title='Explorador Onclusive', layout='wide')

EXPECTED_COLUMNS = [
    'id', 'Title', 'Detail', 'Link', 'Source', 'Update date', 'Publish date',
    'Sentiment', 'Ranking', 'Media type', 'Tags', 'Country', 'Language',
    'Audience', 'Reach', 'Interactions', 'Notes', 'Author name',
    'Author handle (@username)', 'Author URL', 'Gender', 'Age', 'Bio', 'City', 'fecha'
]


def normalize_text(value: str) -> str:
    if value is None:
        return ''
    text = str(value).strip()
    return re.sub(r'\s+', ' ', text)


def extract_month_from_path(path_text: str) -> str:
    path_text = str(path_text)
    match = re.search(r'(\d{1,2}-[A-Za-zÁÉÍÓÚáéíóúÑñ]+)', path_text)
    return match.group(1) if match else 'Sin mes'


def extract_topic_from_filename(filename: str) -> str:
    name = Path(filename).stem
    name = name.replace('Onclusive_Social_-_', '').replace('Onclusive_Social_', '')
    name = name.replace('_', ' ').replace('-', ' ')
    name = re.sub(r'\s+', ' ', name).strip()
    return name if name else 'Sin tema'


def standardize_columns(df: pd.DataFrame) -> pd.DataFrame:
    rename_map = {col: normalize_text(col) for col in df.columns}
    df = df.rename(columns=rename_map).copy()

    for col in EXPECTED_COLUMNS:
        if col not in df.columns:
            df[col] = pd.NA

    df = df[EXPECTED_COLUMNS]

    for date_col in ['Update date', 'Publish date', 'fecha']:
        df[date_col] = pd.to_datetime(df[date_col], errors='coerce', dayfirst=True)

    for num_col in ['Audience', 'Reach', 'Interactions', 'Ranking']:
        df[num_col] = pd.to_numeric(df[num_col], errors='coerce')

    text_cols = ['Title', 'Detail', 'Source', 'Sentiment', 'Media type', 'Tags', 'Country', 'Language',
                 'Author name', 'Author handle (@username)', 'Gender', 'City']
    for col in text_cols:
        df[col] = df[col].astype('string').fillna('')

    return df


@st.cache_data(show_spinner=False)
def load_uploaded_files(file_bytes_list):
    frames = []
    metadata_rows = []

    for item in file_bytes_list:
        file_name = item['name']
        month_name = item.get('month', 'Sin mes')
        content = item['content']
        excel = pd.read_excel(io.BytesIO(content), engine='openpyxl')
        df = standardize_columns(excel)
        df['mes'] = month_name
        df['tema'] = extract_topic_from_filename(file_name)
        df['archivo'] = file_name
        frames.append(df)
        metadata_rows.append({'mes': month_name, 'archivo': file_name, 'tema': extract_topic_from_filename(file_name), 'filas': len(df)})

    if not frames:
        return pd.DataFrame(), pd.DataFrame()

    return pd.concat(frames, ignore_index=True), pd.DataFrame(metadata_rows)


@st.cache_data(show_spinner=False)
def load_from_folder(folder_path: str):
    frames = []
    metadata_rows = []

    for root, _, files in os.walk(folder_path):
        for file in files:
            if file.lower().endswith(('.xlsx', '.xls')) and not file.startswith('~$'):
                full_path = os.path.join(root, file)
                month_name = extract_month_from_path(full_path)
                excel = pd.read_excel(full_path, engine='openpyxl')
                df = standardize_columns(excel)
                df['mes'] = month_name
                df['tema'] = extract_topic_from_filename(file)
                df['archivo'] = file
                df['ruta'] = full_path
                frames.append(df)
                metadata_rows.append({'mes': month_name, 'archivo': file, 'tema': extract_topic_from_filename(file), 'filas': len(df), 'ruta': full_path})

    if not frames:
        return pd.DataFrame(), pd.DataFrame()

    return pd.concat(frames, ignore_index=True), pd.DataFrame(metadata_rows)


def filter_dataframe(df: pd.DataFrame):
    with st.sidebar:
        st.header('Filtros')
        months = st.multiselect('Mes', sorted(df['mes'].dropna().unique().tolist()))
        topics = st.multiselect('Tema', sorted(df['tema'].dropna().unique().tolist()))
        sentiments = st.multiselect('Sentimiento', sorted([x for x in df['Sentiment'].dropna().unique().tolist() if x]))
        sources = st.multiselect('Fuente / dominio', sorted([x for x in df['Source'].dropna().unique().tolist() if x]))
        media_types = st.multiselect('Tipo de medio', sorted([x for x in df['Media type'].dropna().unique().tolist() if x]))
        countries = st.multiselect('País', sorted([x for x in df['Country'].dropna().unique().tolist() if x]))
        languages = st.multiselect('Idioma', sorted([x for x in df['Language'].dropna().unique().tolist() if x]))

        min_date = df['fecha'].min() if df['fecha'].notna().any() else None
        max_date = df['fecha'].max() if df['fecha'].notna().any() else None
        date_range = None
        if min_date is not None and max_date is not None:
            date_range = st.date_input('Rango de fecha', value=(min_date.date(), max_date.date()))

        keyword = st.text_input('Buscar palabra clave en título / detalle / tags')
        min_reach = st.number_input('Reach mínimo', min_value=0, value=0, step=100)

    filtered = df.copy()
    if months:
        filtered = filtered[filtered['mes'].isin(months)]
    if topics:
        filtered = filtered[filtered['tema'].isin(topics)]
    if sentiments:
        filtered = filtered[filtered['Sentiment'].isin(sentiments)]
    if sources:
        filtered = filtered[filtered['Source'].isin(sources)]
    if media_types:
        filtered = filtered[filtered['Media type'].isin(media_types)]
    if countries:
        filtered = filtered[filtered['Country'].isin(countries)]
    if languages:
        filtered = filtered[filtered['Language'].isin(languages)]
    if min_reach:
        filtered = filtered[filtered['Reach'].fillna(0) >= min_reach]

    if date_range and len(date_range) == 2:
        start_date = pd.to_datetime(date_range[0])
        end_date = pd.to_datetime(date_range[1])
        filtered = filtered[(filtered['fecha'].isna()) | ((filtered['fecha'] >= start_date) & (filtered['fecha'] <= end_date))]

    if keyword:
        pattern = keyword.strip()
        mask = (
            filtered['Title'].str.contains(pattern, case=False, na=False)
            | filtered['Detail'].str.contains(pattern, case=False, na=False)
            | filtered['Tags'].str.contains(pattern, case=False, na=False)
            | filtered['Author name'].str.contains(pattern, case=False, na=False)
        )
        filtered = filtered[mask]

    return filtered


def to_excel_bytes(df: pd.DataFrame) -> bytes:
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='datos_filtrados')
    return output.getvalue()


def render_kpis(df: pd.DataFrame):
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric('Menciones', f"{len(df):,}")
    c2.metric('Reach total', f"{int(df['Reach'].fillna(0).sum()):,}")
    c3.metric('Interacciones', f"{int(df['Interactions'].fillna(0).sum()):,}")
    c4.metric('Autores únicos', f"{df['Author handle (@username)'].replace('', pd.NA).dropna().nunique():,}")
    c5.metric('Fuentes únicas', f"{df['Source'].replace('', pd.NA).dropna().nunique():,}")


def render_charts(df: pd.DataFrame):
    left, right = st.columns(2)

    tema_counts = df.groupby('tema', dropna=False).size().reset_index(name='menciones').sort_values('menciones', ascending=False)
    if not tema_counts.empty:
        fig = px.bar(tema_counts, x='tema', y='menciones', title='Menciones por tema')
        left.plotly_chart(fig, use_container_width=True)

    senti = df[df['Sentiment'].str.len() > 0].groupby(['tema', 'Sentiment']).size().reset_index(name='menciones')
    if not senti.empty:
        fig = px.bar(senti, x='tema', y='menciones', color='Sentiment', barmode='group', title='Sentimiento por tema')
        right.plotly_chart(fig, use_container_width=True)

    trend = df.dropna(subset=['fecha']).groupby(df['fecha'].dt.date).size().reset_index(name='menciones')
    if not trend.empty:
        fig = px.line(trend, x='fecha', y='menciones', markers=True, title='Menciones por día')
        st.plotly_chart(fig, use_container_width=True)

    c1, c2, c3 = st.columns(3)

    tags_series = (
        df['Tags'].fillna('').str.split(',').explode().str.strip()
    )
    tags_counts = tags_series[tags_series != ''].value_counts().head(15).reset_index()
    tags_counts.columns = ['tag', 'menciones']
    if not tags_counts.empty:
        fig = px.bar(tags_counts, x='tag', y='menciones', title='Top tags')
        c1.plotly_chart(fig, use_container_width=True)

    source_counts = df['Source'].replace('', pd.NA).dropna().value_counts().head(15).reset_index()
    source_counts.columns = ['fuente', 'menciones']
    if not source_counts.empty:
        fig = px.bar(source_counts, x='fuente', y='menciones', title='Top fuentes')
        c2.plotly_chart(fig, use_container_width=True)

    author_counts = df['Author name'].replace('', pd.NA).dropna().value_counts().head(15).reset_index()
    author_counts.columns = ['autor', 'menciones']
    if not author_counts.empty:
        fig = px.bar(author_counts, x='autor', y='menciones', title='Top autores')
        c3.plotly_chart(fig, use_container_width=True)


def render_quality_report(df: pd.DataFrame):
    quality = pd.DataFrame({
        'columna': df.columns,
        'nulos': [int(df[col].isna().sum()) for col in df.columns],
        'vacios': [int((df[col].astype('string').fillna('').str.strip() == '').sum()) for col in df.columns],
        'tipo': [str(df[col].dtype) for col in df.columns],
    })
    st.dataframe(quality, use_container_width=True)


def main():
    st.title('Explorador de datos Onclusive')
    st.caption('Carga múltiples archivos Excel por mes o apunta a una carpeta local con subcarpetas mensuales.')

    tab1, tab2 = st.tabs(['Carga de datos', 'Exploración'])

    if 'df_master' not in st.session_state:
        st.session_state['df_master'] = pd.DataFrame()
        st.session_state['df_meta'] = pd.DataFrame()

    with tab1:
        st.subheader('Opción A: subir archivos desde la interfaz')
        month_name = st.text_input('Nombre del mes de los archivos que vas a subir', placeholder='Ejemplo: 12-Diciembre')
        uploaded_files = st.file_uploader('Selecciona uno o varios Excel del mismo mes', type=['xlsx', 'xls'], accept_multiple_files=True)

        c1, c2 = st.columns(2)
        with c1:
            if st.button('Agregar archivos subidos al consolidado', use_container_width=True):
                if not uploaded_files:
                    st.warning('Primero sube al menos un archivo.')
                else:
                    payload = [{'name': f.name, 'content': f.getvalue(), 'month': month_name or 'Sin mes'} for f in uploaded_files]
                    df_new, df_meta = load_uploaded_files(payload)
                    if df_new.empty:
                        st.error('No se pudieron leer los archivos.')
                    else:
                        st.session_state['df_master'] = pd.concat([st.session_state['df_master'], df_new], ignore_index=True)
                        st.session_state['df_meta'] = pd.concat([st.session_state['df_meta'], df_meta], ignore_index=True)
                        st.success(f'Se agregaron {len(df_new):,} filas.')
        with c2:
            if st.button('Limpiar consolidado', use_container_width=True):
                st.session_state['df_master'] = pd.DataFrame()
                st.session_state['df_meta'] = pd.DataFrame()
                st.success('Consolidado reiniciado.')

        st.divider()
        st.subheader('Opción B: leer una carpeta local completa')
        st.info('Esta opción funciona cuando ejecutas Streamlit en tu computadora o servidor, no cuando el app está desplegado en la nube.')
        folder_path = st.text_input('Ruta local de la carpeta raíz', placeholder=r'C:\ruta\a\EscuchaSocial')
        if st.button('Cargar carpeta local completa', use_container_width=True):
            if not folder_path:
                st.warning('Ingresa una ruta válida.')
            elif not os.path.exists(folder_path):
                st.error('La ruta no existe en esta máquina.')
            else:
                df_folder, meta_folder = load_from_folder(folder_path)
                if df_folder.empty:
                    st.error('No se encontraron archivos Excel válidos.')
                else:
                    st.session_state['df_master'] = df_folder
                    st.session_state['df_meta'] = meta_folder
                    st.success(f'Se cargaron {len(df_folder):,} filas desde carpeta.')

        if not st.session_state['df_meta'].empty:
            st.subheader('Archivos cargados')
            st.dataframe(st.session_state['df_meta'], use_container_width=True)

    with tab2:
        df_master = st.session_state['df_master']
        if df_master.empty:
            st.info('Primero carga archivos en la pestaña "Carga de datos".')
            return

        filtered = filter_dataframe(df_master)
        render_kpis(filtered)
        st.divider()
        render_charts(filtered)
        st.divider()

        st.subheader('Vista de datos')
        display_cols = ['mes', 'tema', 'fecha', 'Sentiment', 'Source', 'Media type', 'Tags', 'Title', 'Detail', 'Author name', 'Author handle (@username)', 'Reach', 'Interactions', 'archivo']
        st.dataframe(filtered[display_cols], use_container_width=True, height=450)

        st.subheader('Descargas')
        c1, c2 = st.columns(2)
        with c1:
            st.download_button(
                'Descargar CSV filtrado',
                data=filtered.to_csv(index=False).encode('utf-8-sig'),
                file_name='onclusive_filtrado.csv',
                mime='text/csv',
                use_container_width=True,
            )
        with c2:
            st.download_button(
                'Descargar Excel filtrado',
                data=to_excel_bytes(filtered),
                file_name='onclusive_filtrado.xlsx',
                mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                use_container_width=True,
            )

        st.divider()
        st.subheader('Reporte de calidad')
        render_quality_report(filtered)


if __name__ == '__main__':
    main()
