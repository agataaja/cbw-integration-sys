import pandas as pd

from cache_manager import *
from fuzzywuzzy import process
from utils.save_files import save_df


def find_similar_names(international_name, df_referencia, threshold=90):

    international_name = international_name.upper()

    similar_names = process.extract(international_name, df_referencia['nome_completo'], limit=None)

    result = []

    for name_score_tuple in similar_names:
        if name_score_tuple[1] >= threshold:
            result.append(name_score_tuple)

    return result[0][0]


def merge_cnpj_cbc(df_a_analisar):

    df_estabelecimento = CACHE(cache_file_name='df_estabelecimentos_data').load_dataframe_from_cache()
    cbc_merged = pd.merge(df_a_analisar, df_estabelecimento, how='outer', right_on='descricao', left_on='Clube')

    save_df(cbc_merged, 'xlsx')


def incluir_cabecas_de_chave(df_inscritos):

    df_inscritos['Weight Category'] = df_inscritos['Weight Category'].astype(str)

    df_inscritos['Full Name'] = df_inscritos['Full Name'].str.upper()

    ranking_data = CACHE(cache_file_name='RANKING_NACIONAL_2025').load_dataframe_from_cache()

    ranking_data['weight'] = ranking_data['peso'].str.replace("kg", "")

    ranking_data = ranking_data[ranking_data['colocacao'] <= 4]

    merged = pd.merge(df_inscritos,
                      ranking_data,
                      how='left',
                      left_on=['Age Group', 'Discipline', 'Weight Category', 'Custom Id'],
                      right_on=['categoria', 'estilo', 'weight', 'id_atleta'])

    # Create a copy of `merged` to store the seed numbers
    merged['Seed Number'] = None  # Initialize with NaN

    for classe_id in merged['id_classe_peso'].dropna().unique():
        # Filter only the current weight class
        filtered_merged = merged[merged['id_classe_peso'] == classe_id].copy()

        # Get the ranking information
        dict_ranking_id = filtered_merged.loc[
            filtered_merged['colocacao'].notna(),## & (filtered_merged['colocacao'] <= 4),
            ['id_atleta', 'colocacao']
        ].set_index('id_atleta')['colocacao'].to_dict()

        # Assign seed numbers to the original `merged` dataframe
        merged.loc[merged['id_classe_peso'] == classe_id, 'Seed Number'] = \
            merged.loc[merged['id_classe_peso'] == classe_id, 'Custom Id'].map(dict_ranking_id)

    # Ensure seed numbers are ranked correctly
    merged['Seed Number'] = merged.groupby('id_classe_peso')['Seed Number'].rank(method='dense', na_option='bottom')

    # Save final dataframe with all athletes and rankings
    save_df(merged, 'xlsx')


def wo_por_equipes_base(sheet_path, sheet_name, estilo, idade):

    # Carrega o arquivo Excel
    df = pd.read_excel(sheet_path, sheet_name=sheet_name)

    # Lista de categorias obrigatórias
    categorias_obrigatorias_fs = [
        ("u20", "FS", "74"),
        ("u20", "FS", "86"),
        ("u17", "FS", "51"),
        ("u17", "FS", "60"),
        ("u17", "FS", "92"),
        ("u20", "FS", "125"),
        ("u20", "FS", "57"),
        ("u15", "FS", "44"),
        ("u15", "FS", "62"),
        ("u15", "FS", "75"),
        ("u17", "FS", "71"),
        ("u20", "FS", "65"),
        ("u15", "FS", "52"),
        ("u20", "FS", "97"),
        ("u17", "FS", "45"),
    ]

    categorias_obrigatorias_gr = [
        ('u15', 'GR', '68'),
        ('u17', 'GR', '80'),
        ('u17', 'GR', '65'),
        ('u15', 'GR', '57'),
        ('u20', 'GR', '97'),
        ('u20', 'GR', '87'),
        ('u15', 'GR', '85'),
        ('u17', 'GR', '48'),
        ('u20', 'GR', '77'),
        ('u20', 'GR', '60'),
        ('u17', 'GR', '55'),
        ('u17', 'GR', '110'),
        ('u20', 'GR', '67'),
        ('u15', 'GR', '48'),
        ('u20', 'GR', '130'),
    ]

    categorias_obrigatorias_ww = [
        ('u20', 'WW', '62'),
        ('u20', 'WW', '57'),
        ('u20', 'WW', '53'),
        ('u17', 'WW', '57'),
        ('u17', 'WW', '65'),
        ('u15', 'WW', '50'),
        ('u15', 'WW', '66'),
        ('u15', 'WW', '46'),
        ('u15', 'WW', '58'),
        ('u20', 'WW', '68'),
        ('u17', 'WW', '69'),
        ('u17', 'WW', '49'),
        ('u17', 'WW', '73'),
        ('u20', 'WW', '50'),
        ('u20', 'WW', '76'),
    ]

    categorias_obrigatorias_fs_senior = [
        ("seniors", "FS", "74"),
        ("seniors", "FS", "86"),
        ("seniors", "FS", "57"),
        ("seniors", "FS", "65"),
        ("seniors", "FS", "97"),
        ("seniors", "FS", "125"),
    ]

    categorias_obrigatorias_gr_senior = [
        ('seniors', 'GR', '60'),
        ('seniors', 'GR', '67'),
        ('seniors', 'GR', '77'),
        ('seniors', 'GR', '87'),
        ('seniors', 'GR', '97'),
        ('seniors', 'GR', '130'),
    ]

    categorias_obrigatorias_ww_senior = [
        ('seniors', 'WW', '50'),
        ('seniors', 'WW', '53'),
        ('seniors', 'WW', '57'),
        ('seniors', 'WW', '62'),
        ('seniors', 'WW', '68'),
        ('seniors', 'WW', '76'),

    ]

    # Garante que Weight Category é string (caso esteja como número)
    df["Weight Category"] = df["Weight Category"].astype(str)

    # Lista onde vamos guardar novos atletas W.O
    novos_rows = []
    if idade == 'seniors':

        if estilo == 'fs':
            categorias = categorias_obrigatorias_fs_senior
        elif estilo == 'ww':
            categorias = categorias_obrigatorias_ww_senior
        elif estilo == 'gr':
            categorias = categorias_obrigatorias_gr_senior
        else:
            categorias = categorias_obrigatorias_ww_senior + categorias_obrigatorias_gr_senior + categorias_obrigatorias_fs_senior
    else:
        if estilo == 'fs':
            categorias = categorias_obrigatorias_fs
        elif estilo == 'ww':
            categorias = categorias_obrigatorias_ww
        elif estilo == 'gr':
            categorias = categorias_obrigatorias_gr
        else:
            categorias = categorias_obrigatorias_ww + categorias_obrigatorias_gr + categorias_obrigatorias_fs

    # Agrupar por time usando 'Code' (ou 'Code Alt', se preferir)
    for team, team_df in df.groupby("Code"):

        for age_group, discipline, weight in categorias:
            # Verifica se a combinação existe nesse time
            existe = (
                ((team_df["Age Group"] == age_group) &
                 (team_df["Discipline"] == discipline) &
                 (team_df["Weight Category"] == weight))
                .any()
            )
            if not existe:
                # Criar um atleta W.O
                novos_rows.append({
                    "Code": team,
                    "Code Alt": team_df['Code Alt'].iloc[0],
                    "Full Name": "W.O",
                    "Short Name": "W.O",
                    "Age Group": age_group,
                    "Discipline": discipline,
                    "Weight Category": weight
                    # outras colunas como 'Draw Number', 'Custom Id', etc. ficarão em branco
                })

    # Adiciona os atletas W.O ao DataFrame original
    df_completo = pd.concat([df, pd.DataFrame(novos_rows)], ignore_index=True)

    # Salva o novo arquivo
    save_df(df_completo, 'xlsx')


def get_custm_id_by_name(name):

    request = requests.get(f'https://restcbw.bigmidia.com/gestao/api/atleta?nome_completo={name}')

    return request.json()['items']['id']


def include_customId_into_df(df):

    atletas_sge = CACHE(cache_file_name='atletas_sge_cache').load_dataframe_from_cache()

    df['search_sge_name'] = ''

    # Itera de forma segura
    for i, row in df.iterrows():
        try:
            name = find_similar_names(row['Full Name'], atletas_sge)
            print(name)

            # Busca o ID correspondente de forma segura
            match = atletas_sge.loc[atletas_sge['nome_completo'] == name, 'id']

            if not match.empty:
                custom_id = match.iloc[0]  # pega o primeiro ID se houver mais de um
                df.loc[i, 'Custom ID'] = custom_id
                df.loc[i, 'search_sge_name'] = name
            else:
                print(f'⚠️ Nenhum ID encontrado para {name}')
                df.loc[i, 'search_sge_name'] = name

        except Exception as e:
            print(f'❌ Erro ao processar linha {i}: {e}')
            pais = row.get('Code', 'Desconhecido')
            print('Pulando país', pais)

    return df


if __name__ == '__main__':

    # incluir_cabecas_de_chave(pd.read_excel(r"C:\Users\agata\CBW 2025\EVENTOS\BRASILEIROS SENIOR, INFANTIL, VETERANOS\bra_senior.xlsx"))

    merge_cnpj_cbc(pd.read_excel(r"C:\Users\agata\CBW 2026\EVENTOS\CBI U23 - U17\cbc_ranking.xlsx"))


