from datetime import timedelta
import tkinter as tk
from tkinter import filedialog
from cache_manager import *


def save_df(df, file_type):

    file_object = df
    root = tk.Tk()
    root.withdraw()  # Oculta a janela principal do tkinter

    if file_type == 'xlsx':

        file_path = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel files", "*.xlsx")],
            title="Salvar arquivo como"
        )
        if not file_path:
            return

        file_object.to_excel(file_path, index=False)

        os.startfile(file_path)

    else:

        print('Filetype not supported, yet')


def calculate_new_start_list(df, based_duration):

    #df = CACHE(cache_file_name='CBI U15 E U23 - 2025_fights').load_dataframe_from_cache()

    # Convert expectedStartDate to datetime
    df["expectedStartDate"] = pd.to_datetime(df["expectedStartDate"])
    df["expectedStartTime"] = df["expectedStartDate"].dt.time

    # Sort the DataFrame by weightcategory and fightNumber
    df = df.sort_values(by=["fightNumber"]).reset_index(drop=True)

    # Calculate new expected times
    duration = timedelta(minutes=based_duration)  # Fixed duration between fights

    def calculate_new_time(row):

        fight_number = row["weight"]
        fight_mat = row['matName']

        primeiro_tempo = df.loc[df["matName"] == fight_mat, "expectedStartDate"].min()
        primeira_luta_do_tapete = df.loc[df["matName"] == fight_mat, "weight"].min()

        return primeiro_tempo + duration * (fight_number - primeira_luta_do_tapete)

    def calculate_round_i_want(row):

        if (row['round'] == "Qualif." or row['round'] == "1/4 Final" or row['round'] == "1/2 Final"
                or "Rnd" in row['round'] or "Round" in row['round']):
            return "Qualificatórias às Semifinais"

        elif row['round'] == "Repechage":
            return "Repescagens"
        else:
            return "Disputas de Medalhas"

    # Apply the function to calculate the new expected start time
    df["newExpectedStartTime"] = df.apply(calculate_new_time, axis=1)
    df["roundIWant"] = df.apply(calculate_round_i_want, axis=1)

    # Group by weightCategoryShortName, roundFriendlyName, matName
    grouped_df = (
        df.groupby(['weightCategoryShortName', 'matName', 'roundIWant'])
        .agg(
            n_lutas=('fightNumber', 'size'),  # Count of rows in each group
            duracao_estimada=('fightNumber', lambda x: len(x) * based_duration),  # Calculate expected duration
            hora_inicio=('newExpectedStartTime', 'min'),  # Get the earliest newExpectedStartTime
            hora_fim=('newExpectedStartTime', 'max')
        )
        .reset_index()
    )

    grouped_df["hora_inicio"] = grouped_df["hora_inicio"].dt.strftime("%H:%M:%S")
    grouped_df["hora_fim"] = grouped_df["hora_fim"].dt.strftime("%H:%M:%S")

    save_df(grouped_df, 'xlsx')


def calculate_new_start_list2(df, duration_dict):

    # Convert expectedStartDate to datetime
    df["expectedStartDate"] = pd.to_datetime(df["expectedStartDate"])
    df["expectedStartTime"] = df["expectedStartDate"].dt.time

    # Criar a coluna de duração específica de cada luta
    df["fight_duration"] = df["audienceName"].map(duration_dict)

    print(df['audienceName'].unique())

    # Ordenar as lutas por tapete e número da luta
    df = df.sort_values(by=["matName", "fightNumber"]).reset_index(drop=True)

    # Criar dicionário para armazenar o horário atualizado de início
    new_start_times = {}

    for mat in df["matName"].unique():
        # Filtrar apenas as lutas desse tapete
        df_mat = df[df["matName"] == mat].copy()

        # Pegamos a primeira luta no tapete para definir o início
        first_fight_start = df_mat["expectedStartDate"].min()

        # Percorrer cada luta no tapete e calcular o horário
        current_time = first_fight_start
        for idx, row in df_mat.iterrows():
            new_start_times[idx] = current_time  # Armazena o novo horário de início

            print(row['audienceName'], row['fight_duration'])

            current_time += timedelta(minutes=row["fight_duration"])  # Avança o tempo conforme a duração

    # Adicionar os novos horários ao DataFrame
    df["newExpectedStartTime"] = df.index.map(new_start_times)

    def calculate_round_i_want(row):
        if row['round'] in ["Qualif.", "1/4 Final", "1/2 Final"] or "Rnd" in row['round'] or "Round" in row['round']:
            return "Qualificatórias às Semifinais"
        elif "Repechage" in row['round']:
            return "Repescagens"
        else:
            return "Disputas de Medalhas"

    df["roundIWant"] = df.apply(calculate_round_i_want, axis=1)

    # Agrupar e calcular tempos de início e fim
    grouped_df = (
        df.groupby(['weightCategoryShortName', 'matName', 'roundIWant'])
        .agg(
            n_lutas=('fightNumber', 'size'),
            duracao_estimada=('fight_duration', 'sum'),
            hora_inicio=('newExpectedStartTime', 'min'),
            hora_fim=('newExpectedStartTime', 'max')
        )
        .reset_index()
    )

    grouped_df["hora_inicio"] = grouped_df["hora_inicio"].dt.strftime("%H:%M:%S")
    grouped_df["hora_fim"] = grouped_df["hora_fim"].dt.strftime("%H:%M:%S")

    save_df(grouped_df, 'xlsx')


def calculate_new_start_list_final(df, duration_dict):

    # Convert expectedStartDate to datetime
    df["expectedStartDate"] = pd.to_datetime(df["expectedStartDate"])
    df["expectedStartTime"] = df["expectedStartDate"].dt.time

    # Garantir sessionStartDate como datetime.date
    df["sessionStartDate"] = pd.to_datetime(df["sessionStartDate"]).dt.date

    # Criar a coluna de duração específica de cada luta
    df["fight_duration"] = df["audienceName"].map(duration_dict)

    # Ordenar por data, tapete e número da luta
    df = df.sort_values(
        by=["sessionStartDate", "matName", "fightNumber"]
    ).reset_index(drop=True)

    # Dicionário para armazenar novos horários
    new_start_times = {}

    # Loop por DIA e TAPETE
    for day, df_day in df.groupby("sessionStartDate"):
        for mat, df_mat in df_day.groupby("matName"):

            # Primeira luta do dia/tapete determina o início
            first_fight_start = df_mat["expectedStartDate"].min()
            current_time = first_fight_start

            # Para cada luta, calcular horário atualizado
            for idx, row in df_mat.iterrows():
                new_start_times[idx] = current_time
                current_time += timedelta(minutes=row["fight_duration"])

    # Adicionar novos horários ao DF principal
    df["newExpectedStartTime"] = df.index.map(new_start_times)

    # Classificação dos rounds
    def calculate_round_i_want(row):
        round_ = row['round']
        if round_ in ["Qualif.", "1/4 Final", "1/2 Final"] or \
           "Rnd" in round_ or "Round" in round_:
            return "Qualificatórias às Semifinais"
        elif "Repechage" in round_:
            return "Repescagens"
        else:
            return "Disputas de Medalhas"

    df["roundIWant"] = df.apply(calculate_round_i_want, axis=1)

    # Criar tabela final incluindo sessionStartDate
    grouped_df = (
        df.groupby(['sessionStartDate', 'weightCategoryShortName', 'matName', 'roundIWant'])
        .agg(
            n_lutas=('fightNumber', 'size'),
            duracao_estimada=('fight_duration', 'sum'),
            hora_inicio=('newExpectedStartTime', 'min'),
            hora_fim=('newExpectedStartTime', 'max'),
        )
        .reset_index()
    )

    # Converter horários para string
    grouped_df["hora_inicio"] = grouped_df["hora_inicio"].dt.strftime("%H:%M:%S")
    grouped_df["hora_fim"] = grouped_df["hora_fim"].dt.strftime("%H:%M:%S")

    save_df(grouped_df, 'xlsx')

if __name__ == '__main__':

    durations = {
        "U17": 3.4,  # 3 minutos por luta na U15
        "U20": 4.6,  # 5 minutos por luta na U23
        "U23": 4.6,  # 5 minutos por luta na U23
        "Seniors": 4.8,  # 5 minutos por luta na U23
        "U16": 3.4,  # 5 minutos por luta na U23
        "": 4.8,  # 5 minutos por luta na U23
    }

    df = CACHE(cache_file_name='CIRCUITO SUL-SUDESTE _fights').load_dataframe_from_cache()

    print(df)

    save_df(df, 'xlsx')

    breakpoint()

    lista = []

    for i in df['victoryType']:

        lista.append(i)

    print(list(set(lista)))

    df = df[df['victoryType'].isin(['VPO1', 'VIN', 'VSU', 'VCA', 'VSU1', 'VFA', 'VPO'])]

    df = df.groupby('matName').size().reset_index(name='Total')

    print(df)




