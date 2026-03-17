import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import os
from datetime import datetime, timedelta

def classificar_severidade(mm):
    if mm == 0: return 'Sem Chuva'
    elif mm <= 10: return 'Leve'
    elif mm <= 50: return 'Moderada'
    elif mm <= 100: return 'Intensa'
    else: return 'Extrema'
    
def le_nome_cidade(csv):
    with open(csv, encoding='utf-8') as f:
        primeira_linha = f.readline()
        nome_cidade = primeira_linha.split(':')[1].strip()  # Ajuste conforme o formato real da linha
    return nome_cidade

def get_file_paths(folder_path):

    file_paths = []
    nomes = []
    # Percorre todos os arquivos e subdiretórios
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            # Cria o caminho completo do arquivo
            full_path = os.path.join(root, file)
            file_paths.append(full_path)
            nomes.append(le_nome_cidade(full_path))

    return file_paths, nomes

def data_analisys(nome, csv):
    
    #le e filtra arquivo
    db_null = pd.read_csv(csv, sep=';', skiprows=10)
    db_null = db_null[['Data Medicao', 'Hora Medicao','PRECIPITACAO TOTAL, HORARIO(mm)']]

    #DB
    db = db_null.fillna(0)

    # Trata os dados
    db['Data Medicao'] = pd.to_datetime(db['Data Medicao'], errors='coerce')
    colunas_float = ['PRECIPITACAO TOTAL, HORARIO(mm)']
    for col in colunas_float:
        db[col] = db[col].astype(str).str.replace(',', '.').astype(float)
    db['AnoMes'] = db['Data Medicao'].dt.to_period('M')

    # Análise estatística básica
    dados_estatisticos = db.describe(include='all')

    nulos = db_null.isnull().sum()['PRECIPITACAO TOTAL, HORARIO(mm)']
    registros = len(db_null['Data Medicao'])

    info = {
    'nome': nome,
    'qtd_registros': registros,
    'qtd_nulos_chuva': nulos,
    'Relacao_nulos': format(round(nulos / registros * 100, 2), '.2f') + '%',
    'precip_total': float(db['PRECIPITACAO TOTAL, HORARIO(mm)'].sum())
    }
    df_info = pd.DataFrame([info])

    # Chuva diaria 24 horas)
    df_diario = db.groupby('Data Medicao')['PRECIPITACAO TOTAL, HORARIO(mm)'].sum().reset_index()

    ordem_chuva = ['Sem Chuva', 'Leve', 'Moderada', 'Intensa', 'Extrema']

    df_diario['severidade'] = df_diario['PRECIPITACAO TOTAL, HORARIO(mm)'].apply(classificar_severidade)
    df_diario['severidade'] = pd.Categorical(df_diario['severidade'], categories=ordem_chuva, ordered=True)

    df_diario['PrecAc_3dias'] = df_diario['PRECIPITACAO TOTAL, HORARIO(mm)'].rolling(window=3).sum()
    df_diario['PrecAc_3dias'] = df_diario['PrecAc_3dias'].fillna(0)

    df_diario['severidade_3dias'] = df_diario['PrecAc_3dias'].apply(classificar_severidade)

    # Soma a precipitação por mês
    df_mensal = db.groupby('AnoMes')['PRECIPITACAO TOTAL, HORARIO(mm)'].sum().reset_index()

    return db, dados_estatisticos, df_info, df_diario, df_mensal

def plot_Prec_multi(dataframes, labels, coluna_x, coluna_y, titulo):

    fig = go.Figure()

    for df, label in zip(dataframes, labels):
        # Garantindo que o eixo X seja tratado corretamente
        x = df[coluna_x].astype(str)
        y = df[coluna_y]
        
        # Adiciona cada linha individualmente
        fig.add_trace(go.Scatter(
            x=x, 
            y=y, 
            mode='lines+markers', 
            name=label,
            hovertemplate='<b>Data:</b> %{x}<br><b>Precipitação:</b> %{y}mm<extra></extra>'
        ))

    # Configurações de Layout
    fig.update_layout(
        title=titulo,
        xaxis_title='Ano-Mês',
        yaxis_title='Precipitação (mm)',
        hovermode='x unified', # Mostra todos os dados ao passar o mouse em uma data
        legend_title='Localidades/Séries',
        template='plotly_white',
        xaxis=dict(tickangle=45)
    )

    fig.show(renderer="browser")


def gerar_intervalos_g1(data_inicio_str, data_fim_str, intervalo_dias, termo_busca):
    formato_entrada = "%d/%m/%Y"
    formato_g1 = "%Y-%m-%dT03:00:00.000Z" # O G1 usa o formato ISO 8601 com Z (UTC)
    
    data_inicio = datetime.strptime(data_inicio_str, formato_entrada)
    data_fim = datetime.strptime(data_fim_str, formato_entrada)
    
    resultado = {'Data inicio': [], 'urls': []}
    data_atual = data_inicio
    
    while data_atual < data_fim:
        resultado['Data inicio'].append(data_atual.strftime(formato_entrada))
        proxima_data = data_atual + timedelta(days=intervalo_dias)
        
        # Garante que a data final do intervalo não ultrapasse a data limite
        if proxima_data > data_fim:
            proxima_data = data_fim
            
        # Formata as datas para a URL
        de_str = data_atual.strftime(formato_g1)
        ate_str = proxima_data.strftime(formato_g1)
        
        # Substitui os caracteres especiais para ficarem prontos para URL (%3A para o :)
        de_url = de_str.replace(":", "%3A")
        ate_url = ate_str.replace(":", "%3A")
        
        url = (f"https://g1.globo.com/busca/?q={termo_busca}&species=noticias&order=relevant"
               f"&from={de_url}&to={ate_url}")
        
        resultado['urls'].append(url)
        data_atual = proxima_data + timedelta(days=1) # Pula para o dia seguinte para não sobrepor
    return resultado
