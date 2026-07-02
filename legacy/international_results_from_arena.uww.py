from pandas import DataFrame
from fuzzywuzzy import process
import tkinter as tk
from tkinter import ttk
from cache_manager import *
import requests
from bs4 import BeautifulSoup
import json

def process_event(event_url):


    url = event_url.replace('sport-event/show', 'weight-category')

    weights_url_list = get_weight_categories_urls(url)

    df_list = []

    for url in weights_url_list:

        rank_df = get_results_from_weight_category(url)

        df_list.append(rank_df)

    df: DataFrame = pd.concat(df_list)

    filter_brazilian_results = df[df['Team'] == 'BRA']

    return filter_brazilian_results, df


def get_weight_categories_urls(event_results_url):

    response = requests.get(event_results_url)
    soup = BeautifulSoup(response.content, 'html.parser')

    tables = soup.find_all('table', class_='table table-hover records_properties')

    data = []

    for table in tables:

        rows = table.find_all('tr')

        for row in rows:
            columns = row.find_all('td')
            a_tag = columns[0].find('a')
            href_value = a_tag['href']
            data.append(f'http://arena.uww.org{href_value}')

    return data


def get_results_from_weight_category(weight_category_url):

    response = requests.get(weight_category_url)
    soup = BeautifulSoup(response.content, 'html.parser')

    h2_text = soup.find('div', class_='col-lg-12').h2.text.strip()
    style, age_category, weight = h2_text.split(' - ')

    table = soup.find('table', class_='table table-hover records_properties')
    rows = table.tbody.find_all('tr')

    data = []
    for row in rows:
        columns = row.find_all('td')
        draw_rank = columns[0].text.strip()
        name = columns[1].text.strip()
        team = columns[3].text.strip()
        draw_number = columns[4].text.strip()


        data.append([draw_rank, name, team, draw_number, style, age_category, weight])

    df = pd.DataFrame(data, columns=['Draw Rank', 'Name', 'Team', 'Draw Number', 'Style', 'Age Group', 'Weight'])

    return df


def compare_athletes_uww_sge():

    selected_sge_event = event_combobox.get()
    url_arena_event_get = evento_internacional_var.get()

    id_sge_event_selected = eventos_2024['id'][eventos_2024['descricao'] == selected_sge_event].iloc[0]

    df_atletas_sge = CACHE(cache_file_name='atletas_sge_cache').load_dataframe_from_cache()

    df_atletas_internacionais = process_event(url_arena_event_get)[0]

    # df_atletas_internacionais = df_atletas_internacionais[df_atletas_internacionais['Style'] == 'Greco-Roman']

    selection_window = tk.Toplevel(root, bg="#2f2f2f")
    selection_window.title("Match Athletes")
#    selection_window.iconbitmap(r'static/images/icon 1.ico')
    selection_window.configure(background="#2f2f2f", bg="#2f2f2f", highlightbackground="black", highlightcolor="black")

    def get_id_by_name(df, name):

        filtered_df = df[df['nome_completo'] == name]

        if not filtered_df.empty:
            return filtered_df.iloc[0]['id']
        else:
            return None

    def find_similar_names(row, df_atetas_sge, threshold=80):
        similar_names = process.extract(row['Name'], df_atetas_sge['nome_completo'], limit=None)

        result = []
        for name_score_tuple in similar_names:
            if name_score_tuple[1] >= threshold:
                name_id_tuple = (name_score_tuple[0], get_id_by_name(df_atetas_sge, name_score_tuple[0]))
                result.append(name_id_tuple)
        return result

    similar_names_dict = {row['Name']: find_similar_names(row, df_atletas_sge) for _, row in df_atletas_internacionais.iterrows()}

    def on_select_change(event, row, labels):

        selection = event.widget.get()
        row_name = labels[row]['text']
        if selection != "":
            selected_name, selected_id = selection.split(':')
            similar_names_dict[row_name] = [(selected_name.strip(), int(selected_id.strip()))]
        else:
            similar_names_dict[row_name] = []

        return

    def on_entry_get(event):

        entrada_rank = event.widget.get()

        return entrada_rank

    labels = []
    entries_l = []

    for idx, (_, row) in enumerate(df_atletas_internacionais.iterrows()):
        label = tk.Label(selection_window, text=row['Name'].upper() + " " + row['Style'] + " " + row['Weight'], **label_style)
        label.grid(row=idx, column=0, padx=5, pady=5, sticky=tk.W)
        labels.append(label)

        entry_var = tk.StringVar()
        entries = tk.Entry(selection_window, textvariable=entry_var, relief='groove',width=10, borderwidth=2, **entry_style)
        entries.grid(row=idx, column=1, padx=5, pady=5, sticky=tk.W)
        entries_l.append(entry_var)

        values = [f"{name}: {id_}" for name, id_ in similar_names_dict[row['Name']]]
        values.insert(0, "")
        selection = ttk.Combobox(selection_window, values=values, width=25)
        selection.grid(row=idx, column=2, padx=5, pady=5)
        selection.bind("<<ComboboxSelected>>",
                       lambda event, row=idx, labels = labels: on_select_change(event, row, labels))
        selection.current(0)

        send_button = tk.Button(
            selection_window,
            text="Enviar",
            command=lambda s=selection, r=row, rank_var=entry_var: send_results(s, r, id_sge_event_selected, rank_var)
        )
        send_button.grid(row=idx, column=3, padx=5, pady=5)

    def send_results(selection, row, evento_selecionado_id, rank_var):
        selection_value = selection.get()
        rank = rank_var.get()
        if selection_value:
            name_id = selection_value.split(':')
            if len(name_id) >= 2:
                name = name_id[0].strip()
                id_ = int(name_id[1].strip())
                international_results_send(name, id_, evento_selecionado_id, rank, row)
            else:
                print("Selection value is not in the expected format")
        else:
            print("Selection value is empty")


def international_results_send(nome_sge, id_atleta, id_evento, rank, row):
    data_load = {
        'id_evento': str(id_evento),
        'id': "",
        'id_evento_arena': "",
        'countFighters': "",
        'countFights': "",
        "customId": str(id_atleta),
        'fullName': nome_sge,
        "rank": str(rank),
        'sportName': row['Style'],
        'name': row['Weight'],
        'audienceName': row['Age Group'],
        'weightCategoryFullName': f"{row['Style']} - {row['Age Group']} - {row['Weight']}",
    }

    if row['Style'] == "Freestyle":
        data_load['sportAlternateName'] = "FS"
    elif row['Style'] == "Greco-Roman":
        data_load['sportAlternateName'] = "GR"
    else:
        data_load['sportAlternateName'] = "WW"

    url_api = "https://restcbw.bigmidia.com/cbw/api/resultado-rank-arena"
    json_payload = json.dumps(data_load)
    headers2 = {"Content-Type": "application/json"}

    response = requests.post(url_api, data=json_payload, headers=headers2)

    print(data_load)



root = tk.Tk()

root.title("Resultados Internacionais")

root.configure(background="#2f2f2f", bg="#2f2f2f", highlightbackground="black", highlightcolor="black", width=100)

#root.iconbitmap(r'static/images/icon 1.ico')

label_style = {"bg": "#2f2f2f", "fg": "white", "font": ("Roboto", 9)}
entry_style = {"bg": "#585858", "fg": "white", "font": ("Roboto", 9)}
button_style = {"bg": "#2f2f2f", "fg": "white", "font": ("Roboto", 9)}


root.title("Selecione o Evento ")

#root.iconbitmap(r'static/images/icon 1.ico')
root.configure(background="#2f2f2f", bg="#2f2f2f", highlightbackground="black", highlightcolor="black")

eventos_2024 = CACHE(cache_file_name='dataframe_cache_eventos_2026').load_dataframe_from_cache()

event_combobox = ttk.Combobox(root, values=list(eventos_2024['descricao']), width=50)
event_combobox.set("Selecione o evento do SGE")
event_combobox.grid(row=5, column=0, padx=10, pady=10)

evento_internacional_label = tk.Label(root, text='Url do evento internacional', **label_style)
evento_internacional_label.grid(row=2, column=0, padx=10, pady=10)
evento_internacional_var = tk.StringVar()
evento_internacional_entry = tk.Entry(root, textvariable=evento_internacional_var, relief='groove', width=45, borderwidth=2, **entry_style)
evento_internacional_entry.grid(row=3, column=0, padx=10, pady=10, sticky='w')

confirm_button = tk.Button(root, text="Confirm", command=compare_athletes_uww_sge,
                           width=10, relief='groove', borderwidth=2, **button_style)
confirm_button.grid(row=7, column=0, padx=10, pady=10, sticky='w')

root.mainloop()