import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog, ttk
from expected_start_list import save_df, calculate_new_start_list_final
import re
from autorization import *
from fuzzywuzzy import process
from cache_manager import *
import threading
import logging
import json


log_dir = 'logs/sge_rank_arena_data'
os.makedirs(log_dir, exist_ok=True)  # Cria o diretório, se não existir

log_file = os.path.join(log_dir, 'post_results.log')

logging.basicConfig(
    filename='logs/sge_post_results.log',
    level=logging.INFO,  # use logging.DEBUG se quiser mais detalhes
    format='%(asctime)s - %(levelname)s - %(message)s'
)


def map_style(var):
    if 'Greco' in var:
        return "GR"
    elif 'Freestyle' in var:
        return 'FS'
    else:
        return 'WW'


def get_headers():

    user_name = user_name_combobox.get()
    file_path = "config/credentials.json"

    with open(file_path, "r") as f:
        credentials_data = json.load(f)

    api_key = credentials_data[user_name]["api_key"]
    client_id = credentials_data[user_name]["client_id"]
    client_secret = credentials_data[user_name]["client_secret"]
    ip = credentials_data[user_name]["ip"]

    headers = {'Authorization': 'Bearer ' + get_token(api_key, client_id, client_secret, ip)}

    return headers


def get_event_id():

    user_name = user_name_combobox.get()
    file_path = "config/credentials.json"

    with open(file_path, "r") as f:
        credentials_data = json.load(f)

    event_id = credentials_data[user_name]["event_id"]

    return event_id


def get_all_ranking(api_key, client_id, client_secret, ip, event_id):

    # Get the access token
    headers = {'Authorization': 'Bearer ' + get_token(api_key, client_id, client_secret, ip)}

    # Get all weight categories in a single API call
    weight_categories = get_endpoint_response(headers, f"weight-category/{event_id}")['weightCategories']
    print(weight_categories)

    all_data = []
    for category in weight_categories:
        id_categoria = category['id']
        ranking_categoria = get_endpoint_response(headers, endpoint=f"weight-category/get/{id_categoria}/ranking?=")['ranking']
        print(ranking_categoria)
        try:
            for chave, valor in ranking_categoria.items():
                person_id = valor['fighter']['personId']
                custom_id = get_custom_id(headers, person_id)
                valor['fighter']['customId'] = custom_id
                all_data.append(valor['fighter'])

        except AttributeError:
            for key, item in range(len(ranking_categoria)):

                person_id = item['fighter']['personId']
                custom_id = get_custom_id(headers, person_id)
                item['fighter']['customId'] = custom_id
                all_data.append(item['fighter'])
        except():
            pass

    df = pd.json_normalize(all_data)
    return df


def clear_fights():
    # janela de confirmação
    confirm = messagebox.askyesno(
        "Confirmação",
        "Tem certeza que deseja deletar toda ordem de lutas?"
    )

    # cancela caso o usuário clique em "Não"
    if not confirm:
        return

    headers = get_headers()
    event_id = get_event_id()

    weight_categories = get_endpoint_response(headers, f"weight-category/{event_id}")['weightCategories']

    for category in weight_categories:

        id = category['id']

        url = f"http://localhost:8080/api/json/weight-category/get/{id}/fights/clear"
        requests.request("PATCH", url=url, headers=headers)


def clear_fights_for_age_group():

    headers = get_headers()

    weight_categories = get_weights_categories()
    categoria = simpledialog.askstring("age group","qual categoria mane")

    for id, shortName in weight_categories.items():

        if categoria in shortName:

            url = f"http://localhost:8080/api/json/weight-category/get/{id}/fights/clear"
            requests.request("PATCH", url=url, headers=headers)


def save_arena_credentials():

    api_key = entries[0].get()
    client_id = entries[1].get()
    client_secret = entries[2].get()
    ip = entries[3].get()
    event_id = entries[4].get()
    directory = entries[5].get()
    user_name = entries[6].get()
    credentials = {
        "api_key": api_key,
        "client_id": client_id,
        "client_secret": client_secret,
        "ip": ip,
        "event_id": event_id,
        "directory": directory,
        "user_name": user_name
    }

    try:
        with open("config/credentials.json", "r") as f:
            existing_credentials = json.load(f)
    except FileNotFoundError:
        existing_credentials = {}

    existing_credentials[user_name] = credentials

    with open("config/credentials.json", "w") as f:
        json.dump(existing_credentials, f)

    user_names = load_user_names()
    user_name_combobox['values'] = user_names
    user_name_combobox.set("")

    messagebox.showinfo("Credentials Saved", "Arena credentials have been saved!")


def run_main_program():

    user_name = user_name_combobox.get()
    file_path = "config/credentials.json"

    with open(file_path, "r") as f:
        credentials_data = json.load(f)

    api_key = credentials_data[user_name]["api_key"]
    client_id = credentials_data[user_name]["client_id"]
    client_secret = credentials_data[user_name]["client_secret"]
    ip = credentials_data[user_name]["ip"]
    event_id = credentials_data[user_name]["event_id"]
    directory = credentials_data[user_name]["directory"]

    if not api_key or not client_id or not client_secret or not ip or not event_id or not directory:
        messagebox.showerror("Error", f"Invalid credentials for user '{user_name}'.")
        return

    df = get_all_ranking(api_key, client_id, client_secret, ip, event_id)

    df.to_excel(f"{directory}/{user_name}.xlsx", sheet_name=f"{user_name}", index=False)

    messagebox.showinfo("Main Program Executed", "The main program has been executed!")


def run_fights_info():

    user_name = user_name_combobox.get()
    file_path = "config/credentials.json"

    with open(file_path, "r") as f:
        credentials_data = json.load(f)

    api_key = credentials_data[user_name]["api_key"]
    client_id = credentials_data[user_name]["client_id"]
    client_secret = credentials_data[user_name]["client_secret"]
    ip = credentials_data[user_name]["ip"]
    event_id = credentials_data[user_name]["event_id"]
    directory = credentials_data[user_name]["directory"]

    headers = {'Authorization': 'Bearer ' + get_token(api_key, client_id, client_secret, ip)}

    if not api_key or not client_id or not client_secret or not ip or not event_id or not directory:
        messagebox.showerror("Error", f"Invalid credentials for user '{user_name}'.")
        return

    fight_list = []

    data_list = []

    response = get_endpoint_response(headers, endpoint=f"fight/{event_id}")['fights']

    print(response)

    for i in range(len(response)):

        f_result = response[i]['result']
        tc_points = response[i]['technicalPoints']
        winner_fighter_id = response[i]['winnerFighter']
        try:
            atleta = get_endpoint_response(headers, endpoint=f"fighter/get/{winner_fighter_id}")['fighter']
            atleta_vencedor = atleta['fullName']
            f1_pid = response[i]["fighter1PersonId"]
            f1_id = get_custom_id(headers, person_id=f1_pid)
            f2_pid = response[i]["fighter2PersonId"]
            f2_id = get_custom_id(headers, person_id=f2_pid)

        except():

            f1_id = "undefined"
            f2_id = "undefined"
            atleta_vencedor = "undefined"

        f1_nome = response[i]["fighter1FullName"]
        f2_nome = response[i]["fighter2FullName"]
        tipo_de_vitoria = response[i]["victoryType"]
        f1_cp = response[i]["fighter1RankingPoint"]
        f2_cp = response[i]["fighter2RankingPoint"]
        nome_evento = response[i]["sportEventName"]
        categoria = response[i]["weightCategoryFullName"]
        team1 = response[i]['team1AlternateName']
        team2 = response[i]['team2AlternateName']
        check_rank = response[i]['rankingCheck']
        tech_check = response[i]['technicalCheck']
        rk_nice_name = response[i]['rankingPointNiceName']
        fight_number = response[i]['fightNumber']
        fight_id = response[i]['id']
        weight_category_id = response[i]["sportEventWeightCategoryId"]
        is_round_robin = response[i]['isRobinGroupFight']
        fight_time = response[i]['endTime']

        print(tc_points)

        try:
            for item in tc_points.keys():

                atleta = tc_points[item]['fullName']

                total_de_pontos_tecnicos = tc_points[item]['total']

                if item == winner_fighter_id:

                    is_fight_winner = 1
                else:
                    is_fight_winner = 0

                print(f"{atleta} marcou o total de: {total_de_pontos_tecnicos}")

                rounds = tc_points[item]['rounds']

                for z in rounds.keys():

                    round_numer = rounds[z]['number']
                    total_de_pontos_do_round = rounds[z]['total']
                    points = rounds[z]['points']

                    print(f"Total de: {total_de_pontos_do_round} maracados no {round_numer} round")

                    for pontos in points.keys():

                        ponto_marcado = points[pontos]['points']
                        segundo = points[pontos]['second']
                        print(ponto_marcado, segundo)

                        linhas_minimas = [atleta,
                                          is_fight_winner,
                                          total_de_pontos_tecnicos,
                                          total_de_pontos_do_round,
                                          round_numer,
                                          ponto_marcado,
                                          segundo,
                                          fight_number,
                                          fight_id,
                                          event_id,
                                          fight_time]

                        fight_list.append(linhas_minimas)
        except():

            linhas_minimas = [0,
                              0,
                              0,
                              0,
                              0,
                              0,
                              0,
                              fight_number,
                              fight_id,
                              event_id]

            fight_list.append(linhas_minimas)

        all_data = [f_result,
                    winner_fighter_id,
                    atleta_vencedor,
                    f1_nome,
                    f1_id,
                    f2_nome,
                    f2_id,
                    tipo_de_vitoria,
                    f1_cp,
                    f2_cp,
                    event_id,
                    nome_evento,
                    categoria,
                    team1,
                    team2,
                    check_rank,
                    tech_check,
                    rk_nice_name,
                    fight_number,
                    fight_id,
                    weight_category_id]

        print(all_data)

        data_list.append(all_data)

        df1 = pd.DataFrame(data_list, columns=[
                    'f_result',
                    'winner_fighter_id',
                    'atleta_vencedor',
                    'f1_nome',
                    'f1_id',
                    'f2_nome',
                    'f2_id',
                    'tipo_de_vitoria',
                    'f1_cp',
                    'f2_cp',
                    'id do evento',
                    'nome do evento',
                    'categoria',
                    'team1',
                    'team2',
                    'check_rank',
                    'tech_check',
                    'rk_nice_name',
                    'fight_number',
                    'fight_id',
                    'weight_category_id'])

        df2 = pd.DataFrame(fight_list, columns=["atleta",
                                                "is_fight_winner",
                                                "total_de_pontos_tecnicos",
                                                "total_de_pontos_do_round",
                                                "round_numer",
                                                "ponto_marcado",
                                                "segundo",
                                                "fight_number",
                                                "fight_id",
                                                "id do evento"])

        df2.to_excel(f"xlsx/{user_name}_rounds_results.xlsx", index=False)

        df1.to_excel(f"xlsx/{user_name}_fight_results.xlsx", index=False)

    messagebox.showinfo("fights loaded", "The fights results has been loaded to the files!")


def get_teams_ranking():

    user_name = user_name_combobox.get()
    file_path = "config/credentials.json"

    with open(file_path, "r") as f:
        credentials_data = json.load(f)

    api_key = credentials_data[user_name]["api_key"]
    client_id = credentials_data[user_name]["client_id"]
    client_secret = credentials_data[user_name]["client_secret"]
    ip = credentials_data[user_name]["ip"]
    event_id = credentials_data[user_name]["event_id"]
    directory = credentials_data[user_name]["directory"]

    if not api_key or not client_id or not client_secret or not ip or not event_id or not directory:
        messagebox.showerror("Error", f"Invalid credentials for user '{user_name}'.")
        return

    df = get_all_ranking(api_key, client_id, client_secret, ip, event_id)
    print(df.columns)

    df = df[df['isNotRanked'] == False]

    def assign_points(rank):

        if rank == 1:
            return 50
        elif rank == 2:
            return 44
        elif rank == 3:
            return 40
        elif rank == 4:
            return 36
        elif rank == 5:
            return 32
        elif rank == 6:
            return 28
        elif rank == 7:
            return 26
        elif rank == 8:
            return 24
        elif rank == 9:
            return 22
        elif rank == 10:
            return 20
        elif rank == 11:
            return 16
        elif rank == 12:
            return 12
        else:
            return 8

    def assign_tie_breaker_uww(rank):

        if rank == 1:
            return 50 * (10**8)

        elif rank == 2:
            return 44 * (10**7)

        elif rank == 3:
            return 40 * (10**6)

        elif rank == 4:
            return 36 * (10**5)

        elif rank == 5:
            return 32 * (10**4)

        elif rank == 6:
            return 28 * (10**3)

        elif rank == 7:
            return 26 * (10**2)

        elif rank == 8:
            return 24 * 10

        elif rank == 9:
            return 22 * 1

        elif rank == 10:
            return 20 * 0.1

        else:
            return 1

    def assing_genero(weight_category_string):

        if weight_category_string.split(' - ')[0] == "Freestyle":
            return "M"
        elif weight_category_string.split(' - ')[0] == "Greco-Roman":
            return "M"
        else:
            return "F"

    def assign_points_jubs(rank):

        if rank == 1:
            return 5
        elif rank == 2:
            return 3
        elif rank == 3:
            return 2
        elif rank == 4:
            return 1.5
        elif rank == 5:
            return 1
        elif rank == 6:
            return 0.5
        elif rank >= 7:
            return 0.5

    def assing_age_group(var):

        partes = var.split(' ')
        valor_entre_hifens = partes[0].strip()

        return valor_entre_hifens

    df['jubs_pontos'] = df['rank'].apply(assign_points_jubs)

    df['tie_braker'] = df['rank'].apply(assign_tie_breaker_uww)

    df['Gênero'] = df['weightCategoryFullName'].apply(assing_genero)

    df['AgeGroup'] = df['weightCategoryShortName'].apply(assing_age_group)

    #df = df.groupby(['teamAlternateName', 'AgeGroup']).agg({'jebs_brasilia_pontos': 'sum', 'tie_braker': 'sum'}).reset_index()

    df = df.groupby(['teamAlternateName']).agg(
        {'jubs_pontos': 'sum', 'tie_braker': 'sum'}).reset_index()
    # clubes_info = CACHE(cache_file_name='df_estabelecimentos_data').load_dataframe_from_cache()

    # clubes_info['id'] = clubes_info['id'].astype(str)

    # df = df_grouped.merge(clubes_info, how='left', left_on='teamAlternateName', right_on='id')

    # df['Colocação'] = df.groupby('teamAlternateName')['jebs_brasilia_pontos'].rank(method='dense', na_option='bottom')

    # Adiciona coluna de sorteio aleatório
    # df['sorteio'] = np.random.rand(len(df))

    # Ordena por pontos, tie_braker e sorteio

    #LEMBRAR DOS CASOS COM AGE GROUP

    df = df.sort_values(
        [ 'jubs_pontos', 'tie_braker'],
        ascending=[False, False]
    )

    # Rankeia por grupo
    # df['Colocação'] = df.groupby('AgeGroup').cumcount() + 1

    # Rankeia por grupo
    df['Colocação'] = df.count() + 1

    # caso queira numeros com mesmo empate siga a proxima lógica

    # df['Colocação'] = df.groupby('AgeGroup') \
        # .apply(lambda x: x[['jebs_brasilia_pontos', 'tie_braker']].rank(
        # method='dense', ascending=False)).reset_index(level=0, drop=True)['jebs_brasilia_pontos']

    headers_nEeded = ['teamAlternateName', 'Colocação', 'Gênero', 'jubs_pontos', 'tie_braker', 'AgeGroup']

    df = df.filter(items=headers_nEeded)

    save_df(df, 'xlsx')


def browse_directory():

    directory = filedialog.askdirectory()
    entries[5].delete(0, tk.END)
    entries[5].insert(0, directory)


def save_credentials_stored():

    file_saving_path = filedialog.asksaveasfilename(confirmoverwrite=True)

    if file_saving_path:
        with open("config/credentials.json", 'r') as creds:

            data = json.load(creds)

            df = pd.json_normalize(data)

            df.to_excel(excel_writer=f"{file_saving_path}.xlsx")

            messagebox.showinfo("Sucesso", "arquivo salvo com sucesso")

    else:
        messagebox.showerror("Erro", "uepa, ratinho!")


def load_user_names():
    try:
        with open("config/credentials.json", "r") as f:
            credentials_data = json.load(f)
            # user_names = []
        # for n in range(len(credentials_data)):

            # user_names.append(n)
        user_names = [machines["user_name"] for cred_data, machines in credentials_data.items()]
        # user_names = [credentials[next(iter(credentials))]["user_name"] for credentials in credentials_data]

        # Inverter a ordem — registros mais novos no topo
        user_names.reverse()

        return user_names
    except FileNotFoundError:
        return []


def get_sport_events_info():

    get_endpoint_response(get_headers(), endpoint="/sport-event")                                           


def get_eight_quarter_losers():

    headers = get_headers()
    id_evento = get_event_id()

    response = get_endpoint_response(headers=headers, endpoint=f"fight/{id_evento}/completed")['fights']
    eighters_list = []
    quarters_list = []
    print(response)

    lista_de_perdedores = {}

    for i in range(len(response)):

        round_name = response[i]['roundFriendlyName']

        print(round_name)

        if round_name == "1/4 Final" or round_name == "1/8 Final" or round_name == "Qualif.":

            winner_fighter_id = response[i]['winnerFighter']
            # try:
                # atleta = get_endpoint_response(headers, endpoint=f"fighter/get/{winner_fighter_id}")['fighter']
                # atleta_vencedor = atleta['fullName']
                # f1_pid = response[i]["fighter1PersonId"]
                # f1_id = get_custom_id(headers, person_id=f1_pid)
                # f2_pid = response[i]["fighter2PersonId"]
                # f2_id = get_custom_id(headers, person_id=f2_pid)
            # except():
                # f1_id = "undefined"
                # f2_id = "undefined"
                # atleta_vencedor = "undefined"

            f1_nome = response[i]["fighter1FullName"]
            f1_draw_number = response[i]['fighter1DrawRank']
            f2_nome = response[i]["fighter2FullName"]
            f2_draw_number = response[i]['fighter2DrawRank']
            f1_cp = response[i]["fighter1RankingPoint"]
            f2_cp = response[i]["fighter2RankingPoint"]
            team_1 = response[i]['team1Name']
            team_2 = response[i]['team2Name']
            team1 = response[i]['team1AlternateName']
            team2 = response[i]['team2AlternateName']
            check_rank = response[i]['rankingCheck']
            tech_check = response[i]['technicalCheck']
            weight_category_id = response[i]["sportEventWeightCategoryId"]
            is_round_robin = response[i]['isRobinGroupFight']
            round_name = response[i]['roundFriendlyName']
            estilo = response[i]['sportName']
            audience = response[i]['audienceName']
            peso = response[i]['weightCategoryName']
            print(round_name, "pontos atleta 2:", f2_cp, "pontos atleta 1:", f1_cp)

            if round_name == "1/8 Final":

                if f1_cp == 1 or f1_cp == 0:
                    eighters_list.append(
                        [team_1, team1, "", "", f1_nome, "", "", audience, estilo, peso, "", "", "", f1_draw_number])
                    print("atleta 1 perdeu, linha adicionada")

                elif f2_cp == 1 or f2_cp == 0:
                    eighters_list.append(
                        [team_2, team2, "", "", f2_nome, "", "", audience, estilo, peso, "", "", "", f2_draw_number])
                    print("atleta 2 perdeu, linha adicionada")

            elif round_name == 'Qualif.':

                if f1_cp == 1 or f1_cp == 0:
                    eighters_list.append(
                        [team_1, team1, "", "", f1_nome, "", "", audience, estilo, peso, "", "", "", f1_draw_number])
                    print("atleta 1 perdeu, linha adicionada")

                    lista_de_perdedores[f1_nome] = weight_category_id

                elif f2_cp == 1 or f2_cp == 0:
                    eighters_list.append(
                        [team_2, team2, "", "", f2_nome, "", "", audience, estilo, peso, "", "", "", f2_draw_number])
                    print("atleta 2 perdeu, linha adicionada")

                    lista_de_perdedores[f2_nome] = weight_category_id

            elif round_name == "1/4 Final":

                if f1_cp == 1 or f1_cp == 0:

                    quarters_list.append(
                        [team_1, team1, "", "", f1_nome, "", "", audience, estilo, peso, "", "",
                         "", f1_draw_number * 3])
                    quarters_list.append(
                        ["null", "null", "", "", f"null", "", "", audience, estilo, peso, "", "",
                         "", int(f1_draw_number * 3) + 1])

                    print("atleta 1 perdeu, linha adicionada")

                elif f2_cp == 1 or f2_cp == 0:

                    quarters_list.append(
                        [team_2, team2, "", "", f2_nome, "", "", audience, estilo, peso, "", "",
                         "", f2_draw_number*3])
                    quarters_list.append(
                        ["null", "null", "", "", f"null", "", "", audience, estilo, peso, "", "",
                         "", f2_draw_number*3+1])

                    print("atleta 2 perdeu, linha adicionada")

    catgoridict = get_weights_categories()

    for id in catgoridict.keys():

        response = get_endpoint_response(headers, f"weight-category/get/{id}")

        number_of_fighters = response['weightCategory']['fightersIsReady'][0][
            'weightCategoryCountReadyFighters']

        if number_of_fighters < 16:

            contagem_de_perdedores = list(lista_de_perdedores.values()).count(id)

            atletas_fantasmas = 8 - contagem_de_perdedores

            for i in range(atletas_fantasmas):

                eighters_list.append(
                    ["", "", "", "", f"null", "", "", response['weightCategory']['audienceName'], response['weightCategory']['sportId'], re.findall(r'\d+', str(response['weightCategory']['alternateName'])), "", "",
                     "", ""])

            # contador_de_categoria = 16 - number_of_fighters

    df = pd.DataFrame(eighters_list, columns=[

        "Code",
        "Code Alt(max 10 chars)",
        "Last Name",
        "First Name",
        "Full Name",
        "Short Name",
        "Athena Print ID",
        "Age Group",
        "Discipline",
        "Weight category",
        "Previous Federation",
        "Seed Number",
        "Custom ID",
        "DrawNumber"])
    print(df)
    # df.to_excel(r"C:\Users\agata\CBW 2025\JEBS_25_UBERLANDIA\arena_model_bronze.xlsx", sheet_name="Oitavas", index=False)

    df2 = pd.DataFrame(quarters_list, columns=[

        "Code",
        "Code Alt(max 10 chars)",
        "Last Name",
        "First Name",
        "Full Name",
        "Short Name",
        "Athena Print ID",
        "Age Group",
        "Discipline",
        "Weight category",
        "Previous Federation",
        "Seed Number",
        "Custom ID",
        "DrawNumber"])
    print(df2)
    df2.to_excel(r"C:\Users\agata\CBW 2025\JEBS_25_UBERLANDIA\arena_model_prata.xlsx", sheet_name="Quartas", index=False)


def show_credentials_infos(user_name):

    user_name = user_name_combobox.get()
    file_path = "config/credentials.json"

    with open(file_path, "r") as f:
        credentials_data = json.load(f)

    api_key = credentials_data[user_name]["api_key"]
    client_id = credentials_data[user_name]["client_id"]
    client_secret = credentials_data[user_name]["client_secret"]
    ip = credentials_data[user_name]["ip"]
    event_id = credentials_data[user_name]["event_id"]
    directory = credentials_data[user_name]["directory"]

    if user_name in credentials_data:
        entries[0].delete(0, tk.END)
        entries[0].insert(0, api_key)
        entries[1].delete(0, tk.END)
        entries[1].insert(0, client_id)
        entries[2].delete(0, tk.END)
        entries[2].insert(0, client_secret)
        entries[3].delete(0, tk.END)
        entries[3].insert(0, ip)
        entries[4].delete(0, tk.END)
        entries[4].insert(0, event_id)
        entries[5].delete(0, tk.END)
        entries[5].insert(0, directory)
        entries[6].delete(0, tk.END)
        entries[6].insert(0, user_name)


def clear_single_fight(fight_id, headers):

    url = f"http://localhost:8080/api/json/fight/get/{fight_id}/clear-result"
    tryi = requests.request("POST", url=url, headers=headers)
    print(tryi.status_code)


def get_completed_fights_ids(id_evento, headers):

    response = get_endpoint_response(headers=headers, endpoint=f"fight/{id_evento}/completed")['fights']

    fights_id_list = []
    fights_dict = {}

    for i in range(len(response)):

        fight_id = response[i]['id']
        estilo = response[i]['sportName']
        audience = response[i]['audienceName']
        peso = response[i]['weightCategoryName']
        fight_number = response[i]['fightNumber']

        fights_id_list.append([fight_id, estilo, audience, peso, fight_number])
        fights_dict[fight_id] = [estilo, audience, peso, fight_number]

    return fights_dict


def json_rounds_request():

    headers = get_headers()
    sport_event_id = get_event_id()

    response = get_endpoint_response(headers, endpoint=f'fight/{sport_event_id}')['fights']

    list = []

    for fight in response:

        technical_points_ids = fight.get("technicalPointIds", [])

        df = pd.json_normalize(fight)
        list.append(df)

        for ids in technical_points_ids:

            data = fight['technicalPointsDetail'][ids]


def run_selecionar_categorias():

    headers = get_headers()
    id_evento = get_event_id()

    selection_window = tk.Toplevel(root, bg="#2f2f2f")
    selection_window.title("Selecione as Categorias/Pesos")
    selection_window.iconbitmap('icon 1.ico')

    items = get_completed_fights_ids(id_evento, headers)

    # Create a list to store the Checkbutton variables
    check_vars = []

    for valor in items.values():
        var = tk.StringVar()
        check_vars.append(var)
        checkbutton = tk.Checkbutton(selection_window, text=f"Luta: {valor[3]}", variable=var)
        checkbutton.pack()

    def limpar_lutas_selecionadas():

        selected_items = [chave
                          for var, chave in zip(check_vars, items.keys())
                          if var.get() == "1"]
        for chave in selected_items:
            print("Selected:", chave)
            clear_single_fight(chave, headers)
            print(f"Luta: {chave} apagada")

    select_button = tk.Button(selection_window, text="Show Selected Items", command=limpar_lutas_selecionadas)
    select_button.pack()


def try_cleaning():

    headers = get_headers()
    var = input("digite o id da luta")
    clear_single_fight(var, headers)

    print("cleaned")


def get_sge_event():

    selection_window = tk.Toplevel(root, bg="#2f2f2f")
    selection_window.title("Selecione o Evento ")
    selection_window.iconbitmap('icon 1.ico')
    selection_window.configure(background="#2f2f2f", bg="#2f2f2f", highlightbackground="black", highlightcolor="black")

    with open("static/json/eventos_sge_2024.json", "rb") as campeonatos_sge:
        campeonatos_data = json.load(campeonatos_sge)

    selected_event_var = tk.StringVar()
    button_style = {"bg": "#2f2f2f", "fg": "white", "font": ("Roboto", 9)}
    event_combobox = ttk.Combobox(selection_window, values=list(campeonatos_data.keys()), width=50)
    event_combobox.set("Selecione o evento do SGE")
    event_combobox.grid(row=0, column=0, padx=10, pady=10)

    # Function to set the selected event and close the window
    def set_selected_event():

        global evento_sge
        evento_sge = event_combobox.get()
        selection_window.destroy()

        return evento_sge

    # Button to confirm the selection
    confirm_button = tk.Button(selection_window, text="Confirm", command=set_selected_event, **button_style, width=10, relief='groove', borderwidth=2)
    confirm_button.grid(row=1, column=0, padx=10, pady=10)

    selection_window.wait_window(event_combobox)

    return evento_sge, campeonatos_data


def get_teams_custom_ranking(aggregate_by_age_group=False):

    import json
    from tkinter import messagebox

    user_name = user_name_combobox.get()
    file_path = "config/credentials.json"

    # --- Carregar credenciais ---
    with open(file_path, "r") as f:
        credentials_data = json.load(f)

    creds = credentials_data.get(user_name, {})
    required_keys = ["api_key", "client_id", "client_secret", "ip", "event_id", "directory"]

    if not all(creds.get(k) for k in required_keys):
        messagebox.showerror("Erro", f"Credenciais inválidas para o usuário '{user_name}'.")
        return

    # --- Buscar dados ---
    df = get_all_ranking(
        creds["api_key"], creds["client_id"], creds["client_secret"], creds["ip"], creds["event_id"]
    )

    # --- Filtrar apenas ranqueados ---
    df = df[df['isNotRanked'] == False].copy()

    # --- Pontuações configuráveis ---
    uww_points_ = {
        1: 50, 2: 44, 3: 40, 4: 36, 5: 32,
        6: 28, 7: 26, 8: 24, 9: 22, 10: 20,
        11: 16, 12: 12
    }

    uww_points = {
        1: 25, 2: 20, 3: 15, 4: 12, 5: 10,
        6: 12, 7: 8, 8: 6, 9: 4, 10: 2
    }

    jubs_points = {
        1: 5, 2: 3, 3: 2, 4: 2, 5: 1, 6: 0.5
    }

    jebs_points = {
        1: 13, 2: 9, 3: 7, 4: 5, 5: 4, 6: 3, 7: 2, 8: 1
     }



    def assign_points(rank, system="jebs"):
        if system == "uww":
            return uww_points.get(rank, 0)
        elif system == "jubs":
            return jubs_points.get(rank, 0.5)
        elif system == "jebs":
            return jebs_points.get(rank, 0)
        return 0

    def assign_tie_breaker(rank):
        """Usa fator exponencial para desempate proporcional à pontuação."""
        base = jebs_points.get(rank, 8)
        return base * (10 ** (max(0, 12 - rank)))

    def get_gender(weight_category):
        style = weight_category.split(" - ")[0]
        return "F" if style not in ["Freestyle", "Greco-Roman"] else "M"

    def get_age_group(short_name):
        return short_name.split(" ")[0].strip()

    # --- Aplicar transformações ---
    df['Pontos'] = df['rank'].apply(lambda r: assign_points(r, "uww"))
    df['TieBreaker'] = df['rank'].apply(assign_tie_breaker)
    df['Gênero'] = df['weightCategoryFullName'].apply(get_gender)
    df['AgeGroup'] = df['weightCategoryShortName'].apply(get_age_group)

    df = df[df['AgeGroup'].isin(['U20', 'U15'])].copy()

    # --- Agrupar por time, gênero e (opcionalmente) faixa etária ---
    group_cols = ['teamName', 'Gênero']
    if aggregate_by_age_group:
        group_cols.append('AgeGroup')

    df_grouped = (
        df.groupby(group_cols, as_index=False)
        .agg({'Pontos': 'sum', 'TieBreaker': 'sum'})
    )

    # --- Ordenar e ranquear dentro de cada gênero (e age_group, se usado) ---
    sort_cols = ['Gênero', 'Pontos', 'TieBreaker']
    ascending_order = [True, False, False]

    if aggregate_by_age_group:
        sort_cols.insert(1, 'AgeGroup')
        ascending_order.insert(1, True)

    df_grouped = df_grouped.sort_values(sort_cols, ascending=ascending_order)

    # Adicionar coluna de colocação separada por gênero (e faixa etária se ativo)
    rank_groups = ['Gênero']
    if aggregate_by_age_group:
        rank_groups.append('AgeGroup')

    df_grouped['Colocação'] = (
            df_grouped.groupby(rank_groups)
            .cumcount() + 1
    )

    # --- Selecionar colunas finais ---
    columns_final = ['teamName', 'Gênero', 'Colocação', 'Pontos', 'TieBreaker']
    if aggregate_by_age_group:
        columns_final.append('AgeGroup')

    df_final = df_grouped[columns_final]

    # --- Exportar ---
    save_df(df_final, 'xlsx')

    return df_final


def get_cbc_teams_custom_ranking(aggregate_by_age_group=False):

    import json
    from tkinter import messagebox

    user_name = user_name_combobox.get()
    file_path = "config/credentials.json"

    # --- Carregar credenciais ---
    with open(file_path, "r") as f:
        credentials_data = json.load(f)

    creds = credentials_data.get(user_name, {})
    required_keys = ["api_key", "client_id", "client_secret", "ip", "event_id", "directory"]

    if not all(creds.get(k) for k in required_keys):
        messagebox.showerror("Erro", f"Credenciais inválidas para o usuário '{user_name}'.")
        return

    # --- Buscar dados ---
    df = get_all_ranking(
        creds["api_key"], creds["client_id"], creds["client_secret"], creds["ip"], creds["event_id"]
    )

    # --- Filtrar apenas ranqueados ---
    df = df[df['isNotRanked'] == False].copy()

    # --- Pontuações configuráveis ---
    uww_points = {
        1: 50, 2: 44, 3: 40, 4: 36, 5: 32,
        6: 28, 7: 26, 8: 24, 9: 22, 10: 20,
        11: 16, 12: 12
    }

    jubs_points = {
        1: 5, 2: 3, 3: 2, 4: 2, 5: 1, 6: 0.5
    }

    jebs_points = {
        1: 13, 2: 9, 3: 7, 4: 5, 5: 4, 6: 3, 7: 2, 8: 1
    }

    def assign_points(rank, system="jebs"):
        if system == "uww":
            return uww_points.get(rank, 8)
        elif system == "jubs":
            return jubs_points.get(rank, 0.5)
        elif system == "jebs":
            return jebs_points.get(rank, 0)
        return 0

    def assign_tie_breaker(rank):
        """Usa fator exponencial para desempate proporcional à pontuação."""
        base = jebs_points.get(rank, 8)
        return base * (10 ** (max(0, 12 - rank)))

    def get_gender(weight_category):
        style = weight_category.split(" - ")[0]
        return "F" if style not in ["Freestyle", "Greco-Roman"] else "M"

    def get_age_group(short_name):
        return short_name.split(" ")[0].strip()

    # --- Aplicar transformações ---
    df['TieBreaker'] = df['rank'].apply(assign_tie_breaker)
    df['Gênero'] = df['weightCategoryFullName'].apply(get_gender)
    df['AgeGroup'] = df['weightCategoryShortName'].apply(get_age_group)
    df['customPoints'] = df['rank'].apply(assign_points)

    # Filter agegroups
    df = df[df['AgeGroup'].isin(['U20', 'U15'])].copy()


    # --- Agrupar por time, gênero e (opcionalmente) faixa etária ---
    group_cols = ['teamAlternateName', 'Gênero']
    if aggregate_by_age_group:
        group_cols.append('AgeGroup')

    df_grouped = (
        df.groupby(group_cols, as_index=False)
        .agg({'teamRankingPoint': 'sum', 'TieBreaker': 'sum'})
    )

    # --- Ordenar e ranquear dentro de cada gênero (e age_group, se usado) ---
    sort_cols = ['Gênero', 'teamRankingPoint', 'TieBreaker']
    ascending_order = [True, False, False]

    if aggregate_by_age_group:
        sort_cols.insert(1, 'AgeGroup')
        ascending_order.insert(1, True)

    df_grouped = df_grouped.sort_values(sort_cols, ascending=ascending_order)

    # Adicionar coluna de colocação separada por gênero (e faixa etária se ativo)
    rank_groups = ['Gênero']
    if aggregate_by_age_group:
        rank_groups.append('AgeGroup')

    df_grouped['Colocação'] = (
            df_grouped.groupby(rank_groups)
            .cumcount() + 1
    )

    sge_df = CACHE(cache_file_name='df_estabelecimentos_data').load_dataframe_from_cache()

    # --- Selecionar colunas finais ---
    columns_final = ['teamAlternateName', 'Gênero', 'Colocação', 'descricao', 'uf', 'cnpj', 'teamRankingPoint', 'TieBreaker',]

    if aggregate_by_age_group:
        columns_final.append('AgeGroup')

    df_grouped['teamAlternateName'] = df_grouped['teamAlternateName'].astype(str)
    sge_df['id'] = sge_df['id'].astype(str)

    df_merge = df_grouped.merge(sge_df, how='left', left_on='teamAlternateName', right_on='id')

    df_final = df_merge[columns_final]

    # --- Exportar ---
    save_df(df_final, 'xlsx')

    return df_final


def post_results_sge():

    headers = get_headers()
    event_id = get_event_id()
    athletes = CACHE(cache_file_name='atletas_sge_cache').load_dataframe_from_cache()
    var_dict = {}

    try:
        event_selected = evento_sge_combobox.get()
        id_evento = event_selected.split('} ')[1]

    except Exception as e:
        logging.error(f"Erro ao obter evento selecionado: {e}")
        print(f"Erro ao obter evento selecionado: {e}")
        return

    categoria_sge = simpledialog.askstring('Pergunta:', 'Qual a classe?')

    try:
        weight_categories = get_endpoint_response(headers, f"weight-category/{event_id}")['weightCategories']

    except Exception as e:
        logging.error(f"Erro ao buscar categorias de peso: {e}")
        print(f"Erro ao buscar categorias de peso: {e}")
        return

    for category in weight_categories:
        try:
            id_categoria = category['id']
            id_evento_sge = id_evento

            ranking_categoria = get_endpoint_response(headers, f"weight-category/get/{id_categoria}/ranking?=")['ranking']
            logging.info(f"Categoria {id_categoria} - Ranking obtido com sucesso")

            for chave, valor in ranking_categoria.items():
                weight_category_string = str(valor['fighter']['weightCategoryFullName'])
                categoria_arena = weight_category_string.split(' - ')[1]

                if (categoria_sge == categoria_arena or categoria_sge == "") and not valor['fighter']['isNotRanked']: # and valor['fighter']['weightCategoryFullName'] == "Women's wrestling - Seniors - 76 kg"
                    person_id = valor['fighter']['personId']
                    try:
                        custom_id = get_custom_id(headers, person_id)
                    except Exception as e:
                        logging.warning(f"Erro ao obter custom_id para {person_id}: {e}")
                        custom_id = ""
                        print(f"Erro ao obter custom_id para {person_id}: {e}")

                    # Preenche o dicionário
                    var_dict.update({
                        'id_evento': id_evento_sge,
                        'id': "",
                        'id_evento_arena': str(valor['fighter']['sportEventId']),
                        'countFighters': str(valor['fighter']['weightCategoryCountReadyFighters']),
                        'countFights': str(valor['fighter']['weightCategoryCountFights']),
                        'weightCategoryFullName': weight_category_string,
                        'customId': str(custom_id),
                        'fullName': str(valor['fighter']['fullName']),
                        'rank': str(valor['fighter']['rank']),
                        'sportAlternateName': "FS" if "Freestyle" in weight_category_string else "GR" if "Greco-Roman" in weight_category_string else "WW",
                        'sportName': weight_category_string.split(' - ')[0],
                        'name': weight_category_string.split(' - ')[2],
                        'audienceName': 'veterans-a' if categoria_arena == "Veterans A" else categoria_arena
                    })

                    try:
                        response = requests.post(
                            "https://restcbw.bigmidia.com/cbw/api/resultado-rank-arena",
                            data=json.dumps(var_dict),
                            headers={"Content-Type": "application/json"}
                        )
                        logging.info(f"Post para {var_dict['fullName']} retornou status {response.status_code}")
                        print(f"Post para {var_dict['fullName']} retornou status {response.status_code}")

                    except Exception as e:
                        logging.error(f"Erro no POST para {var_dict['fullName']}: {e}")
                        print(f"Erro no POST para {var_dict['fullName']}: {e}")

        except Exception as e:
            logging.error(f"Erro ao processar categoria {category.get('id')}: {e}")
            print(f"Erro ao processar categoria {category.get('id')}: {e}")

    messagebox.showinfo("Finished", "finish baby agatinha!")


def delete_ids_sge_range():

    x = simpledialog.askinteger("range inicial", "id")
    y = simpledialog.askinteger("range final", "id")
    a = x


    for items in range(x, y):

        url_api = f"https://restcbw.bigmidia.com/cbw/api/resultado-rank-arena/{a}"

        payload = {}
        headers2 = {}

        response = requests.delete(url_api, data=payload, headers=headers2)

        a += 1

        print(response.status_code)
    messagebox.showinfo("Finished", f"Cleanded Id Range {x}:{y}")


def delete_ids_sge():

    a = simpledialog.askstring("id a ser excluido", "informe o id")

    url_api = f"https://restcbw.bigmidia.com/cbw/api/resultado-rank-arena/{a}"

    payload = {}
    headers2 = {}

    response = requests.delete(url_api, data=payload, headers=headers2)

    print(response.status_code)

    messagebox.showinfo("Finished", f"Cleanded Id {a}")


def delete_evento_results_sge():

    a = simpledialog.askstring("id eventos pra limpar", "informe o id do evento agora:")

    df_resultados_a_excluir = rank_arena_atleta(a)

    for _, resultado in df_resultados_a_excluir.iterrows():

        id_resultado = resultado['id']

        url_api = f"https://restcbw.bigmidia.com/cbw/api/resultado-rank-arena/{id_resultado}"

        payload = {}
        headers2 = {}

        response = requests.delete(url_api, data=payload, headers=headers2)

        print(response.status_code)

    messagebox.showinfo("Finished", f"Cleanded Evento Id {a}")


def update_sge():

    resultados_window = tk.Toplevel(root, bg="#2f2f2f")
    resultados_window.title("Manipulação de Resultados ")
    resultados_window.iconbitmap('icon 1.ico')
    resultados_window.configure(background="#2f2f2f", bg="#2f2f2f", highlightbackground="black", highlightcolor="black")

    estilos = ["Freestyle", "Greco-Roman", "Female wrestling"]

    estilo_combobox = ttk.Combobox(resultados_window, values=estilos, width=50)
    estilo_combobox.set("Estilo")
    estilo_combobox.grid(row=0, column=0, padx=10, pady=10)

    rotulos = ["Id SGE:", "Novo Custom Id:"]
    entradas = [tk.Entry(resultados_window, relief='groove', borderwidth=2),
               tk.Entry(resultados_window, relief='groove', borderwidth=2)]

    for i, label_text in enumerate(rotulos):
        tk.Label(resultados_window, text=label_text, anchor='w', **label_style).grid(row=i + 2, column=0, padx=10, pady=5,
                                                                        sticky='w')
        entradas[i].grid(row=i + 2, column=1, pady=5)
        entradas[i].config(**entry_style)

    # a = simpledialog.askstring("ID", "Qual ID?")
    # r = simpledialog.askstring("Rank", "Qual o novo rank?")
    # estilo = simpledialog.askstring("Estilo", "Qual o novo estilo?")

    def send_new_results():

        id_resultado = entradas[0].get()
        novo_resultado = entradas[1].get()

        print("id_do_resultado enviado", id_resultado)

        estilo = estilo_combobox.get()

        print("estilo novo", estilo)

        url_api = f"https://restcbw.bigmidia.com/cbw/api/resultado-rank-arena/{id_resultado}"

        headers = {"Content-Type": "application/json"}

        resultado_payload = requests.get(url_api).json()

        #resultado_payload['rank'] = f'{novo_resultado}'

        if estilo == 'Freestyle':

            resultado_payload['sportAlternateName'] = 'FS'

        elif estilo == 'Greco-Roman':

            resultado_payload['sportAlternateName'] = 'GR'

        else:
            resultado_payload['sportAlternateName'] = 'WW'

        resultado_payload['weightCategoryFullName'] = (resultado_payload['weightCategoryFullName']

                                                       .replace(str(resultado_payload['sportName']), estilo))

        resultado_payload['sportName'] = str(estilo)

        resultado_payload['customId'] = str(novo_resultado)

        final_json_payload = json.dumps(resultado_payload)

        print(final_json_payload)

        requests.delete(url_api)

        url_post = 'https://restcbw.bigmidia.com/cbw/api/resultado-rank-arena'

        post = requests.post(url_post, data=final_json_payload, headers=headers)

        print(final_json_payload, post.status_code)

    button = tk.Button(resultados_window, text="Enviar", command=send_new_results, **button_style)
    button.grid(row=3, column=2, padx=5)


def send_alternative_result():

    payload = {"id_evento": '122',
               "sportAlternateName": "FS",
               "sportName": "Freestyle",
               "name": "65 kg",
               "audienceName": "U23",
               "weightCategoryFullName": "Freestyle - U23 - 65 kg",
               "customId": "121",
               "fullName": "GUILHERMY DE JESUS OLIVEIRA SILVA",
               "rank": '7'}

    url_post = 'https://restcbw.bigmidia.com/cbw/api/resultado-rank-arena'

    final_json_payload = json.dumps(payload)

    headers = {"Content-Type": "application/json"}

    post = requests.post(url_post, data=final_json_payload, headers=headers)

    breakpoint()

    resultado_payload = {}

    resultado_payload['sportAlternateName'] = r'FS'

    resultado_payload['sportName'] = r'Freestyle'

    resultado_payload['customId'] = r'536'

    resultado_payload['fullName'] = r'VINICIUS ALVES LESSA PAULA'

    resultado_payload['name'] = r'97 kg'

    resultado_payload['rank'] = r'3'

    resultado_payload['audienceName'] = r'Seniors'

    resultado_payload['id_evento'] = r'123'

    final_json_payload = json.dumps(resultado_payload)

    print(final_json_payload)

    url_post = 'https://restcbw.bigmidia.com/cbw/api/resultado-rank-arena'

    post = requests.post(url_post, data=final_json_payload, headers=headers)

    print(final_json_payload, post.status_code)


def post_bra_senior():

    file_path = "config/credentials.json"

    with open(file_path, "r") as f:
        credentials_data = json.load(f)

    file = f"C://Users//agata//CBW disco C//RESULTADOS ARENA 2023-AGOSTO//resultados individuais/BRA SR.xlsx"
    df = pd.read_excel(file)

    evento_sge, campeonatos_data = get_sge_event()

    id_evento_sge = campeonatos_data[evento_sge]['id_sge']
    categoria_sge = campeonatos_data[evento_sge]['age']

    var_dict = {}

    print('It is OK untill now')
    for index, linha in df.iterrows():

        weight_category_string = linha['weightCategoryFullName']
        categoria_arena = weight_category_string.split(' - ')[1]

        if (categoria_sge == categoria_arena or categoria_sge == "") and linha['isNotRanked'] is False:

            var_dict['id_evento'] = id_evento_sge
            var_dict['id'] = ""
            var_dict['id_evento_arena'] = str(linha['sportEventId'])
            var_dict['countFighters'] = str(linha['weightCategoryCountReadyFighters'])
            var_dict['countFights'] = str(linha['weightCategoryCountFights'])
            var_dict['weightCategoryFullName'] = str(linha['weightCategoryFullName'])
            var_dict["customId"] = str(linha['customId'])
            var_dict['fullName'] = str(linha['fullName'])
            var_dict["rank"] = str(linha['rank'])
            if weight_category_string.split(' - ')[0] == "Freestyle":
                var_dict['sportAlternateName'] = "FS"
            elif weight_category_string.split(' - ')[0] == "Greco-Roman":
                var_dict['sportAlternateName'] = "GR"
            else:
                var_dict['sportAlternateName'] = "WW"
            var_dict['sportName'] = weight_category_string.split(' - ')[0]
            var_dict['name'] = weight_category_string.split(' - ')[2]
            var_dict['audienceName'] = categoria_arena

            url_api = "https://restcbw.bigmidia.com/cbw/api/resultado-rank-arena"

            json_payload = json.dumps(var_dict)

            headers2 = {"Content-Type": "application/json"}

            response = requests.post(url_api, data=json_payload, headers=headers2)

            print(json_payload)
            print(response.status_code)


def get_fighters():

    categorias = get_weights_categories()

    data = get_endpoint_response(get_headers(), f"fighter/list")['fighters']
    data_final = pd.json_normalize(data)
    print(data_final)

    list = []

    for id, value in categorias.items():

        list.append(id)

    data_final1 = data_final[data_final['sportEventWeightCategoryId'].isin(list)]
    data_final1.to_excel(r"C:\Users\agata\CBW 2024\eventos 2024\CAMPEONATO SUL-AMERICANO 2024\fighter_from_arena.xlsx")


def get_weights_categories():

    weight_categories = get_endpoint_response(get_headers(), f"weight-category/{get_event_id()}")['weightCategories']
    categorias = {}

    for category in weight_categories:
        id_categoria = category['id']
        nome = category['shortName']
        categorias[id_categoria] = nome

    return categorias


def post_generate_automatic_draw():

    categorias = get_weights_categories()

    data = {"drawType": "block"}

    for id in categorias.keys():

        post_endpoint(get_headers(), f"weight-category/get/{id}/draw/auto?drawType=block&drawType=block", data)

    print("done")


def reset_all_draw():
    # janela de confirmação
    confirm = messagebox.askyesno(
        "Confirmação",
        "Tem certeza que deseja resetar todo chaveamento?"
    )

    # cancela caso o usuário clique em "Não"
    if not confirm:
        return

    categorias = get_weights_categories()

    data = {}

    for id in categorias.keys():

        patch_endpoint(get_headers(), f"weight-category/get/{id}/draw/clear", data)

    print("done")


def delete_all_categorias():
    # janela de confirmação
    confirm = messagebox.askyesno(
        "Confirmação",
        "Tem certeza que deseja deletar todas as categorias?"
    )

    # cancela caso o usuário clique em "Não"
    if not confirm:
        return

    categorias = get_weights_categories()

    data = {}

    for id in categorias.keys():
        delete_endpoint(get_headers(), f"weight-category/get/{id}", data)

    print("done")


def get_brackets_pdf():

    h = get_headers()
    h['Content-Type'] = 'application/pdf'

    print(h)

    data = {}

    categorias = get_weights_categories()

    for id, value in categorias.items():
        params = {
            'print': 1,
            'showNumber': 1
        }

        pdf = requests.get(f"http://localhost:8080/api/json/weight-category/bracket/print?sportEventWeightCategoryId={id}", data=data, headers=h, params=params)

        # print(f"Content-Type: {pdf.headers.get('Content-Type')}")

        # pdf = requests.get(f"http://localhost:8080/bracket/weight-category/show/{id}/bracket/print?live=1")

        # print(pdf.text)

        with open(f'output_folder/{value}.pdf', 'wb') as file:

            file.write(pdf.content)

    print("done")


def enviar_resultados_whatsmat_database():

    # Load cached DataFrames
    whatsmat_results_df = CACHE(cache_file_name='whatsmart_table_normalized_names_2026').load_dataframe_from_cache()

    print(whatsmat_results_df)
    eventos_df = CACHE(cache_file_name='dataframe_cache_eventos_2026').load_dataframe_from_cache()
    eventos_df = eventos_df[eventos_df['escopo'] == 'Internacional']
    atletas_df = CACHE(cache_file_name='atletas_sge_cache').load_dataframe_from_cache()

    def find_similar_names(name, threshold=90):
        matches = process.extract(name, atletas_df['nome_completo'].dropna(), limit=3)
        return [(m[0], get_id_by_name(m[0])) for m in matches if m[1] >= threshold]

    def get_id_by_name(name):
        result = atletas_df.loc[atletas_df['nome_completo'] == name, 'id']
        return result.values[0] if not result.empty else None

    def get_sge_event_id(name):
        result = eventos_df.loc[eventos_df['descricao'] == name, 'id']
        return result.values[0] if not result.empty else None

    def post_payload(payload):
        url = "https://restcbw.bigmidia.com/cbw/api/resultado-rank-arena"
        headers = {"Content-Type": "application/json"}
        print("Sending payload:", payload)
        response = requests.post(url, data=json.dumps(payload), headers=headers)
        print("Response:", response)

    def extrair_inteiro(valor):
        if pd.isna(valor):
            return None

        valor = str(valor)  # 👈 garante string

        match = re.search(r"[+]?\d+(?:\.\d+)?", valor)

        if match:
            return int(float(match.group()))

        return None

    def compare_and_prepare_payloads(df, event_id):
        # Clear frame
        for widget in result_frame.winfo_children():
            widget.destroy()

        payload_dict = {}

        for idx, row in df.iterrows():

            name = row['Name']

            peso = extrair_inteiro(row['Weight'])

            weight = f"{peso} kg"
            style = row['Style']
            key = f"{name}_{weight}_{style}_{idx}"

            # Find matches
            matches = find_similar_names(name)
            names_only = [m[0] for m in matches]

            # UI Row
            tk.Label(result_frame, text=key, anchor='w', width=50, **label_style).grid(row=idx, column=0, padx=5, pady=2)
            cb = ttk.Combobox(result_frame, values=names_only, width=30)
            cb.grid(row=idx, column=1, padx=5, pady=2)

            def update_payload(event, k=key, cb_ref=cb):
                selected = cb_ref.get()
                payload_dict[k]['fullName'] = selected
                payload_dict[k]['customId'] = str(get_id_by_name(selected))

            cb.bind("<<ComboboxSelected>>", update_payload)

            btn = tk.Button(result_frame, text="Enviar", command=lambda k=key: post_payload(payload_dict[k]))
            btn.grid(row=idx, column=2, padx=5, pady=2)

            payload_dict[key] = {
                'fullName': "",
                'customId': "",
                'sportAlternateName': map_style(style),
                'sportName': style,
                'audienceName': row['Age Group'],
                'name': weight,
                'rank': str(row['Rank']),
                'id_evento': str(event_id)
            }

        result_frame.update_idletasks()
        canvas.config(scrollregion=canvas.bbox("all"))

    def update_results(*_):
        selected = intl_event_cb.get()
        return whatsmat_results_df[
            (whatsmat_results_df['Age Group'] + ' - ' +
             whatsmat_results_df['Competition'] + ' - ' +
             whatsmat_results_df['Place']) == selected
        ]

    def on_confirm():
        event_name = sge_event_cb.get()
        event_id = get_sge_event_id(event_name)
        if not event_id:
            print("Evento SGE inválido.")
            return
        filtered = update_results()
        compare_and_prepare_payloads(filtered, event_id)

    # ---------------- UI ----------------
    root.withdraw()
    win = tk.Toplevel(root)
    win.title("Envio de Resultados")
    win.configure(bg="#2f2f2f")
    # win.iconbitmap('static/images/icon 1.ico')

    sge_event_cb = ttk.Combobox(win, values=list(eventos_df['descricao']), width=50)
    sge_event_cb.set("Selecione o evento do SGE")
    sge_event_cb.grid(row=0, column=0, padx=10, pady=5)

    intl_event_cb = ttk.Combobox(win, values=list(
        (whatsmat_results_df['Age Group'] + ' - ' +
         whatsmat_results_df['Competition'] + ' - ' +
         whatsmat_results_df['Place']).unique()), width=50)
    intl_event_cb.set("Selecione Evento Internacional")
    intl_event_cb.grid(row=1, column=0, padx=10, pady=5)

    confirm_btn = tk.Button(win, text="Confirmar", command=on_confirm)
    confirm_btn.grid(row=2, column=0, padx=10, pady=5)

    canvas = tk.Canvas(win, height=500, width=600, bg="#2f2f2f")
    canvas.grid(row=3, column=0, columnspan=2)

    scrollbar = ttk.Scrollbar(win, orient="vertical", command=canvas.yview)
    scrollbar.grid(row=3, column=2, sticky="ns")

    canvas.configure(yscrollcommand=scrollbar.set)

    result_frame = tk.Frame(canvas, bg="#2f2f2f")
    canvas.create_window((0, 0), window=result_frame, anchor="nw")


def situacao():

    data = {'sessionType': '1day'}

    patch_endpoint(get_headers(), "sport-event/get/1ef06f5f-83af-6bb6-9093-7b50a7a7b5dc", data)


def print_events():

    print(get_endpoint_response(get_headers(), "sport-event/get/1ef06f5f-83af-6bb6-9093-7b50a7a7b5dc"))


def load_sge_events_tuple():

    df = CACHE(cache_file_name='dataframe_cache_eventos_2026').load_dataframe_from_cache()

    global lista

    lista = list(df[['descricao', 'id']].itertuples(index=False, name=None))

    evento_sge_combobox['values'] = lista

    return lista


def get_json_ranking_results():

    headers = get_headers()
    event_id = get_event_id()

    weight_categories = get_endpoint_response(headers, f"weight-category/{event_id}")['weightCategories']

    all_data = []

    for category in weight_categories:
        id_categoria = category['id']
        ranking_categoria = get_endpoint_response(headers, endpoint=f"weight-category/get/{id_categoria}/ranking?=")[
            'ranking']
        all_data.append(ranking_categoria)

    with open("data_final_jejs_wrestling.json", "w") as file:
        json.dump(all_data, file)

    print("done")


def start_loading():
    thread = threading.Thread(target=load_sge_events_tuple)
    thread.start()


def return_new_expected_start_list():

    machine_name = user_name_combobox.get()

    def cache_data():

        headers = get_headers()
        sport_event_id = get_event_id()
        json_response = get_endpoint_response(headers, f"fight/{sport_event_id}")

        fights = json_response['fights']

        print(fights)

        df = pd.json_normalize(fights)

        print(df)

        CACHE(df, f'{machine_name}_fights').save_dataframe_to_cache()

    if os.path.exists(os.path.join(CACHE_DIR, f"{machine_name}_fights.pkl")):

        load_frame = CACHE(cache_file_name=f'{machine_name}_fights').load_dataframe_from_cache()

    else:

        cache_data()
        load_frame = CACHE(cache_file_name=f'{machine_name}_fights').load_dataframe_from_cache()

    durations = {
        "U17": 3.4,
        "U16": 3.0,# 3 minutos por luta na U15
        "U20": 4.2,
        "U23": 4.2, # 5 minutos por luta na U23"U17": 3.0,  # 3 minutos por luta na U15
        "U15": 3.0,  # 5 minutos por luta na U23"U17": 3.0,  # 3 minutos por luta na U15
        "Seniors": 4.8,  # 5 minutos por luta na U23"U17": 3.0,  # 3 minutos por luta na U15
        "inf-11-12": 1.5,
        "inf-9-10": 1.5,
        "inf-7-8": 1.5,
        "equipes senior": 15,
        "equipes base": 20,# 5 minutos por luta na U23
    }

    calculate_new_start_list_final(load_frame, durations)


def print_brackets():

    dict_categorias_id = get_weights_categories()

    headers = get_headers()

    def check_fulaninhos(headers, id_categoria):

        data = get_endpoint_response(
            headers,
            f"weight-category/get/{id_categoria}"
        )

        if data["weightCategory"]["countFighters"] == 1:
            return "/print/rankings"

        return "/bracket/print"

    # reutiliza conexão HTTP corretamente
    with requests.Session() as session:

        session.headers.update(headers)

        for id_categoria, name in dict_categorias_id.items():

            try:

                endpoint = check_fulaninhos(headers, id_categoria)

                api_url = (
                    f"http://localhost:8080/onvenue/"
                    f"weight-category/show/{id_categoria}"
                    f"{endpoint}"
                )

                response = session.get(
                    api_url,
                    allow_redirects=True,
                    timeout=30
                )

                print(response)

                if response.status_code == 200:

                    output_file = f"{name}.pdf"

                    with open(output_file, "wb") as file:
                        file.write(response.content)

                    print(
                        f"PDF downloaded successfully "
                        f"as '{output_file}'"
                    )

                else:

                    print(
                        f"Erro {response.status_code}: "
                        f"{response.text[:500]}"
                    )

            except Exception as e:

                print(
                    f"Erro ao processar categoria "
                    f"{name} ({id_categoria}): {e}"
                )


def send_team_tournament_results():

    sportEventId = get_event_id()

    headers = get_headers()

    fights_response = get_endpoint_response(headers, f'fight/{sportEventId}')['fights']

    dicionario_vencedores_por_winner_id = {}

    for luta in fights_response:

        victory_type = luta['rankingPoint']['victoryTypeId']
        winner_id = luta['winnerFighter']
        winner_team = luta['winnerTeamAlternateName']
        round_name = luta['roundFriendlyName']
        estilo = luta['sportName']
        audience = luta['audienceName']
        peso = luta['weightCategoryName']


        if victory_type != "VFO" and victory_type != '2DSQ' and victory_type != '2VFO' and victory_type != 'VIN' and victory_type != '2VIN':

            if winner_id not in dicionario_vencedores_por_winner_id and winner_id:
                dicionario_vencedores_por_winner_id[winner_id] = []

            dicionario_vencedores_por_winner_id[winner_id].append({'id_estabelecimento': winner_team,
                                                      'sportName': estilo,
                                                      'name': peso,
                                                      'audienceName': audience,
                                                      'victory_type': victory_type})

    for winners in dicionario_vencedores_por_winner_id:

        fighter_info = get_fighter_info_by_id(winners)

        dump = {}

        dump['id_evento'] = evento_sge_combobox.get().split('} ')[1]
        dump['id_evento_arena'] = fighter_info['sportEventId']
        dump['countFighters'] = ''
        dump['countFights'] = ''
        dump['weightCategoryFullName'] = fighter_info['weightCategoryFullName']
        dump["customId"] = str(get_custom_id(headers, fighter_info['personId']))
        dump['fullName'] = fighter_info['fullName']
        dump["rank"] = str(len(dicionario_vencedores_por_winner_id[winners]))
        dump['sportAlternateName'] = fighter_info['weightCategoryShortName'].split(' ')[1]
        dump['name'] = fighter_info['weightCategoryShortName'].split(' ')[2]
        dump['audienceName'] = fighter_info['weightCategoryShortName'].split(' ')[0]
        dump['id_estabelecimento'] = str(fighter_info['teamAlternateName'])

        url_api = "https://restcbw.bigmidia.com/cbw/api/resultado-rank-arena"

        json_payload = json.dumps(dump)

        headers2 = {"Content-Type": "application/json"}

        response = requests.post(url_api, data=json_payload, headers=headers2)

        print(response.status_code, dump)

    print("finished little bitch")


def clear_all_people():

    headers = get_headers()
    event_id = get_event_id()

    all_people = get_endpoint_response(headers, f"person?limit=5000")['people']['items']

    print(all_people)

    for i in all_people:
        person_id = i['id']
        delete_endpoint(headers, f"person/get/{person_id}", {})
        print(f"Deleted person with ID: {person_id}")


def get_fighter_info_by_id(fighter_id):

    headers = get_headers()
    response = get_endpoint_response(headers, f"fighter/get/{fighter_id}")['fighter']

    return response


root = tk.Tk()
root.title("Arena Integrated Aplication GUI")

# Configure the window background and dimensions
root.configure(background="#2f2f2f", bg="#2f2f2f", highlightbackground="black", highlightcolor="black", width= 100)


# root.iconbitmap(r'static/images/icon 1.ico')

# Create labels and entry widgets for each credential
label_style = {"bg": "#2f2f2f", "fg": "white", "font": ("Roboto", 9)}
entry_style = {"bg": "#585858", "fg": "white", "font": ("Roboto", 9), "width": 35}


labels = ["API Key:", "Client ID:", "Client Secret:", "IP:", "Event ID:", "Directory:", "Nome Evento Arena:"]
entries = [tk.Entry(root, relief='groove', borderwidth=2),
           tk.Entry(root, relief='groove', borderwidth=2),
           tk.Entry(root, show="*", relief='groove', borderwidth=2),
           tk.Entry(root, relief='groove', borderwidth=2),
           tk.Entry(root, relief='groove', borderwidth=2),
           tk.Entry(root, relief='groove', borderwidth=2),
           tk.Entry(root, relief='groove', borderwidth=2)]

for i, label_text in enumerate(labels):
    tk.Label(root, text=label_text, anchor='w', **label_style).grid(row=i+2, column=0, padx=10, pady=5, sticky='w')
    entries[i].grid(row=i+2, column=1, pady=5)
    entries[i].config(**entry_style)

# Set additional configurations for Combobox and Buttons
user_name_combobox_label = (tk.Label(root, text="Maquina/Evento", **label_style))
user_name_combobox_label.grid(row=0, column=0, sticky='w')

user_name_combobox = ttk.Combobox(root, values=load_user_names(), width=38)
user_name_combobox.grid(row=0, column=1, pady=5)
user_name_combobox.bind('<<ComboboxSelected>>', show_credentials_infos)

button_style = {"bg": "#2f2f2f", "fg": "white", "font": ("Roboto", 9)}

browse_button = tk.Button(root, text="Selecionar", command=browse_directory, **button_style,
                          width=10, relief='groove', borderwidth=2)
browse_button.grid(row=7, column=2, padx=5)
save_button = tk.Button(root, text="Salvar", command=save_arena_credentials, **button_style,
                        width=10, relief='groove', borderwidth=2)
save_button.grid(row=8, column=2)


buttons = [

    ("Save Credentials", save_arena_credentials),
    ("Dados de Lutas", run_main_program),
    ("Resultado Geral de Times", get_teams_ranking),
    ("Resultados por Luta", run_fights_info),
    ("Limpar Sessão", clear_fights),
    ("Gerar Planilha com Perdedores das Oitava/Quartas", get_eight_quarter_losers)
]

# for i, (text, command) in enumerate(buttons):

# tk.Button(root, text=text, command=command, **button_style).grid(row=9 + i, column=0, padx=10)

menu_bar = tk.Menu(root, cursor='cross', borderwidth="10px")


relatorios_menu = tk.Menu(menu_bar, tearoff=0, cursor='hand1')

menu_bar.add_cascade(label="Relatórios e Resultados", menu=relatorios_menu)

relatorios_menu.add_command(label="Rodar resultados individuais", command=run_main_program)
relatorios_menu.add_command(label="resultados de luta a luta", command=run_fights_info)
relatorios_menu.add_command(label="Rodar Oitavas/Quartas", command=get_eight_quarter_losers)
relatorios_menu.add_command(label="Gerar Pontuações de Equipes Custom", command=get_teams_custom_ranking)
relatorios_menu.add_command(label="Api [fighters]", command=get_fighters)
relatorios_menu.add_command(label='Json Ranking Dump', command=get_json_ranking_results)
relatorios_menu.add_command(label='Ordem de Lutas Customizada', command=return_new_expected_start_list)
relatorios_menu.add_command(label='json fights points detail', command=json_rounds_request)
relatorios_menu.add_command(label='CBC Custom Ranking', command=get_cbc_teams_custom_ranking)

implementacoes_menu = tk.Menu(menu_bar, tearoff=0, cursor='hand1')
menu_bar.add_cascade(label="Implementações no Arena", menu=implementacoes_menu)
implementacoes_menu.add_command(label="Ver Categorias", command=run_selecionar_categorias)
implementacoes_menu.add_command(label="Clear Fights", command=clear_fights)
implementacoes_menu.add_command(label="Limpar Luta X", command=try_cleaning)
implementacoes_menu.add_command(label="Generate Auto Draw", command=post_generate_automatic_draw)
implementacoes_menu.add_command(label="Clear All Draw", command=reset_all_draw)
implementacoes_menu.add_command(label="Print Brackets", command=print_brackets)
implementacoes_menu.add_command(label="Delete All WCategories", command=delete_all_categorias)
implementacoes_menu.add_command(label="Get test info", command=situacao)
implementacoes_menu.add_command(label="clear age group", command=clear_fights_for_age_group)
implementacoes_menu.add_command(label="limpar geral", command=clear_all_people)


help_menu = tk.Menu(menu_bar, tearoff=0)
menu_bar.add_cascade(label="Downloads", menu=help_menu)
help_menu.add_command(label="Biaxar Credenciais", command=save_credentials_stored)


api_menu = tk.Menu(menu_bar, tearoff=0)
menu_bar.add_cascade(label="Integração SGE API", menu=api_menu)
api_menu.add_command(label="Post SGE Events Results", command=post_results_sge)
api_menu.add_command(label="Excluir Resultados por ID", command=delete_ids_sge)
api_menu.add_command(label="Uppar Bra senior", command=post_bra_senior)
api_menu.add_command(label="Atualizar Resultados por ID (add custom id)", command=update_sge)
api_menu.add_command(label="Excluir Resultados por Evento", command=delete_evento_results_sge)
api_menu.add_command(label="Whatsmat Resultados Internacionais", command=enviar_resultados_whatsmat_database)
api_menu.add_command(label="Enviar Resultados por Equipes", command=send_team_tournament_results)
api_menu.add_command(label="Enviar Resultado Pontual (guilhermy)", command=send_alternative_result)

evento_sge_combobox_label = (tk.Label(root, text="Evento SGE", **label_style))
evento_sge_combobox_label.grid(row=30, column=0, sticky='w')

evento_sge_combobox = ttk.Combobox(root, values=[], width=50)
evento_sge_combobox.grid(row=30, column=1, pady=5)
# evento_sge_combobox.bind('<Button-1>', load_sge_events_tuple)


root.config(menu=menu_bar)

root.after(1, start_loading)

root.mainloop()

