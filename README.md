# Panic-Buying Analysis

## 📌 Descrição do Projeto

Este projeto tem como objetivo analisar o comportamento do consumidor em períodos de crise, investigando possíveis episódios de *panic-buying* a partir de variáveis ambientais.

A hipótese central é que eventos climáticos extremos — como chuvas intensas e ventos fortes — podem influenciar padrões de consumo, especialmente em contextos de incerteza ou risco percebido pela população.

Os dados meteorológicos utilizados são disponibilizados pelo Instituto Nacional de Meteorologia (INMET), em formato `.csv`, com frequência horária e estrutura padronizada para diversas cidades brasileiras.

---

# 📊 Fonte de Dados

- Instituição: INMET  
- Frequência: Horária  
- Formato: `.csv`  
- Variáveis principais utilizadas:
  - Precipitação (mm)
  - Velocidade do vento
  - Data da medição

Os dados brutos passam por um processo de tratamento e padronização antes de serem utilizados na análise.

---

# ⚙️ Estrutura Geral do Pipeline

Foi desenvolvida uma função principal chamada `data_analisys(cidade, caminho_csv)` com o objetivo de:

- Padronizar o tratamento de dados
- Automatizar o processamento para múltiplas cidades
- Garantir reprodutibilidade
- Reduzir redundância de código

Essa função executa todas as etapas de leitura, limpeza, transformação e geração de bases derivadas.

---

# 🔄 Etapas Detalhadas do Processamento

## 1️⃣ Instalação de dependências

Os pacotes necessários estão listados no arquivo `requirements.txt`, garantindo reprodutibilidade do ambiente.

---

## 2️⃣ Leitura do arquivo

O arquivo `.csv` é lido utilizando a biblioteca `pandas`, preservando a estrutura original fornecida pelo INMET.

---

## 3️⃣ Tratamento de valores nulos

```python
fillna(0)
```

Valores nulos são substituídos por `0`.

**Justificativa:**  
Grande parte dos valores ausentes está relacionada a falhas de coleta. Para variáveis como precipitação, a ausência frequentemente representa ausência de chuva. Essa decisão evita distorções em agregações posteriores.

---

## 4️⃣ Padronização e tipagem das colunas

### Conversão de Data

```python
pd.to_datetime()
```

Permite:
- Agrupamentos temporais
- Cálculo de períodos
- Ordenação cronológica

---

### Conversão de Precipitação e Vento

```python
.str.replace(',', '.').astype(float)
```

**Justificativa:**  
Os dados do INMET utilizam vírgula como separador decimal. A conversão garante consistência numérica para cálculos estatísticos.

---

## 5️⃣ Criação da coluna `AnoMes`

```python
db['Data Medicao'].dt.to_period('M')
```

Permite agregações mensais e análises sazonais.

---

# 📈 DataFrames Gerados

A função `data_analisys()` retorna múltiplas bases derivadas:

---

## 📊 1. `dados_estatisticos_df`

Contém estatísticas descritivas gerais da base tratada:

- Média
- Desvio padrão
- Valores máximos
- Valores mínimos
- Quartis

Objetivo: permitir uma visão exploratória inicial da distribuição dos dados.

---

## 📋 2. `info_df`

Resume informações sobre qualidade dos dados:

| Coluna | Descrição |
|--------|-----------|
| Cidade | Nome da cidade |
| qtd_nulos_chuva | Total de valores ausentes na precipitação |
| qtd_nulos_vento | Total de valores ausentes na velocidade do vento |
| chuva_total | Volume total acumulado de precipitação |

Objetivo: avaliar confiabilidade da base e intensidade do período analisado.

---

## 📆 3. `db_diario`

Obtido a partir do agrupamento diário.

Além da soma diária da precipitação, três colunas adicionais são criadas:

### 🔹 `severidade`

Classificação baseada no volume diário de precipitação, utilizando a função:

```python
classificar_severidade()
```

Essa função categoriza o nível de risco (ex: leve, moderado, severo, extremo).

---

### 🔹 `acumulado_3dias`

```python
rolling(window=3)
```

Armazena a soma da precipitação do dia atual com os dois dias anteriores.

**Justificativa técnica:**

Eventos de crise raramente são causados por um único dia de chuva intensa, mas sim por sequências de dias chuvosos. O acumulado móvel captura melhor esse efeito sistêmico.

---

### 🔹 `severidade_3dias`

Classificação aplicada ao `acumulado_3dias`.

Permite identificar períodos críticos prolongados.

---

## 📅 4. `db_mensal`

Base agregada mensalmente.

A classificação de severidade também é aplicada para análise de sazonalidade e comparação intermensal.

---

# 🛠 Funções Auxiliares

---

## 🔎 `le_nome_cidade(caminho_csv)`

Lê o arquivo `.csv` do INMET e extrai automaticamente o nome da cidade correspondente.

**Objetivo:**  
Evitar inserção manual de nomes e garantir consistência no armazenamento dos dados.

---

## 📂 `get_file_paths(folder_path=None)`

Recebe como argumento a pasta contendo múltiplos arquivos `.csv`.

Retorna duas listas:

- `nomes` → nomes das cidades
- `file_paths` → caminhos completos dos arquivos

**Objetivo:**  
Permitir processamento em lote através de laço de repetição.

---

# 📊 Funções de Visualização

---

## 📈 `plot_prec_diario_interativo(dataframe, nome)`

Gera gráfico interativo da precipitação diária.

Permite:

- Identificar picos extremos
- Detectar padrões temporais
- Explorar visualmente eventos críticos

---

## 📊 `plot_prec_mensal_interativo_multi(dataframes, labels)`

Gera gráfico comparativo mensal entre múltiplas cidades.

Permite:

- Comparação regional
- Análise sazonal
- Identificação de períodos atípicos

---

# 🧠 Armazenamento Estruturado

Todos os resultados são armazenados em um dicionário estruturado:

```python
dbs[nome_cidade] = {
    'bruto': df_original,
    'estatisticas': dados_estatisticos_df,
    'info': info_df,
    'diario': db_diario,
    'mensal': db_mensal
}
```

Isso permite escalabilidade e fácil acesso às informações processadas.

---

# 🚨 Identificação de Dias Críticos

Exemplo de filtro para eventos extremos:

```python
dias_criticos = db_diario[db_diario['acumulado_3dias'] >= 100]
```

O limiar pode ser ajustado conforme critérios técnicos ou literatura meteorológica.

---

# 🎯 Objetivo Analítico Final

A estrutura desenvolvida permite:

- Identificar eventos climáticos extremos
- Medir intensidade e duração desses eventos
- Criar variáveis explicativas para futura modelagem estatística
- Investigar possíveis relações entre clima extremo e comportamento de consumo

O pipeline modular permite expansão futura para:

- Inclusão de dados de vendas
- Modelos econométricos
- Séries temporais
- Machine Learning