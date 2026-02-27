# Panic-buyng

The main idea with this project is the consummer consumption in crises periods analisys.

Para isso de inicio buscamos dados referentes a fatores ambientais como o volume de chuva (mm) e velocidade do vento. Esses dados climáticos são disponibilizados para diversas cidades do brasil pelo intituto nacional de meteorologia INMET, no formato .csv de hora em hora. Assim com a base de dados em mãos foi feito um trabalho de tratamento das informações disponibilizadas.

Leitura, tratamento e filtragem dos dados:
1. Instalação e dos pacotes em requirements.txt
2. Leitura do arquivo .csv com a lib pandas
3. Substituição de valores nulos por 0 (fillna(0)), devido a erro de coleta ou algo do tipo
4. Ajuste da formatação das colunas
    4.1 Data to datetime
    4.2 Precipitação e Vento: .str.replace(',', '.').astype(float)
5. Coluna "AnoMes": Define o mes de cada linha (db['Data Medicao'].dt.to_period('M'))
6. Dataframe "dados_estatisticos" sobre os dados fornecidos
7. Dataframe "info", informações com a quantidade de dados nulos obtidos na base de dados original, para precipitação e vento, além da quantidade total de precipitação no periodo de coleta. As seguites colunas: 'Cidade', 'qtd_nulos_chuva', 'qtd_nulos_vento', 'chuva_total'
8. Através do agrupamento por dia e mês são criados os dataframes "db_diario" e "db_mensal"
8.1 São inseridas mais três colunas no db_diario: 'severidade', 'acumulado_3dias' e 'severidade_3dias'. 'severidade' é inserida com uso da função 'classificar_severidade' de acordo com o volume de precipitação. A coluna 'acumulado_3dias' utiliza a função ntaiva do pandas rolling() com uma janela = 3, assim a coluna armazena para cada dia o volume total de precipitação do dia mais os ultimos dois, e 'severidade_3dias' é o mesmo principio de 'severidade' mas com a coluna 'acumulado_3dias' de argumento na função de classificação. Com isso a análise posterior de severidade fica mais clara, uma vez que periodos de crise normalmente se são devido a sequencia de dias de chiva e não necessariamente um dia só.
8.2 a classificação de severdiade é aplicada ao db_mensal tambem


Os dados fornecidos pelo INMET estruturados de maneira padronizada foi possivel criar uma fução "data_analisys" que contemple essas 9 etapas. "data_analisys" foi a primeira função criada para facilitar e padronizar o tratamento de todas as bases de dado, indepenedente da cidade ou quantidade de dados. Ela recebe dois argumentos (cidade, caminho csv), assim para a cidade fornecida ela retorna os seguintes itens: df da base dados original (bruta) fornecida pelo INMET, dados_estatisticos_df, info_df, df_diario e db_mensal. Com essa rotina é possivel tratar e ajustar diversos arquivos extraidos da plataforma de uma só vez com um laço de repetição.

- le_nome_cidade
Essa função lê o arquivo .csv do INMET e retorna o nome da cidade correspondente ao arquivo.

- get_file_paths(folder_path=None)
Get_file_paths recebe como argumento a pasta com os arquivos .csv e retorna duas listas 'nomes' com todos os nomes das cidades, e 'file_paths' com os repectivos caminhos de cada arquivo.

- plot_prec_diario_interativo(dataframe, nome) e def plot_prec_mensal_interativo_multi(dataframes, labels)
Essa funções recebem os dataframes 'db_diario' e 'db_mensal' de 'data_analisys' e geram um grafico interativo para visualização da precipitação diaria e mensal no periodo contemplado.
Tais graficos são importantes para fazer uma primeira analise a respeito dos periodos mais extremos de precipitação e assim conseguir identificar épocas em que talvez compras de panico e comporatamento do consumidor possam ter sido afetados. 

Assim com todas essas funções com um laço de repetição em nome e file_paths para cada arquivo são gerados todos dataframes ditos anteriormente e tudo isso é salvo em um dicionario em que a chave principal é o nome da cidade (dbs[nome])

Tambem fica facil para identificar dias criticos em que a severidade é extrema
dias_criticos = fln[fln['acumulado_3dias'] >= 100]