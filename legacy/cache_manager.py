from connections.bigmidia_restapi import return_all_ranking, return_all_ranking_fast, get_ids_ano_eventos, main_estabelecimento, main_atletas
from connections.whatsmat_request import load_whatsmart_table, whatsmart_table_normalized_names
import joblib
import os
import pandas as pd

CACHE_DIR = r'C:\Users\agata\PycharmProjects\ArenaProject\cache'


class CACHE:
    def __init__(self, cache_instance=None, cache_file_name=None):

        self.object = cache_instance
        self.file_name = os.path.join(
            CACHE_DIR, f"{cache_file_name}.pkl"
        ) if cache_file_name else None

    def to_df(self, cache_instance):

        if isinstance(cache_instance, dict):  # Verifica se é um JSON (representado como dict em Python)
            print("Recebi um JSON!")
            df = pd.json_normalize(cache_instance)
            return df

        elif isinstance(cache_instance, list):  # Verifica se é um JSON (representado como dict em Python)
            print("Recebi uma Lista!")
            df = pd.DataFrame(cache_instance)
            return df

        elif isinstance(cache_instance, str) and cache_instance.endswith('.txt'):  # Verifica se é um arquivo de texto
            print("Recebi um arquivo TXT!")
            # Lógica para processar arquivo TXT

        elif isinstance(cache_instance, str) and cache_instance.endswith('.csv'):  # Verifica se é um arquivo CSV
            print("Recebi um arquivo CSV!")

        elif isinstance(cache_instance, pd.DataFrame):
            return cache_instance

        else:
            print("Tipo de dado não suportado.")

            raise ValueError("Formato de arquivo não reconhecido.")

    def save_dataframe_to_cache(self):
        """
        Save a DataFrame to the cache.
        """
        cache_instance = self.object

        if cache_instance is None:
            raise ValueError("No object provided to save to cache.")

        # Convert the instance to a DataFrame
        df = self.to_df(cache_instance)

        if df is None or (isinstance(df, pd.DataFrame) and df.empty):
            raise ValueError("Cannot save: DataFrame is empty or invalid.")

        if not self.file_name:
            raise ValueError("Cache file name is not set.")

        if not os.path.exists(CACHE_DIR):
            os.makedirs(CACHE_DIR)

        joblib.dump(df, self.file_name)

    def load_dataframe_from_cache(self):
        """
        Load a DataFrame from the cache if it exists.

        :return: The cached DataFrame or None if no cache exists.
        """
        if not self.file_name:
            raise ValueError("Cache file name is not set.")
        if os.path.exists(self.file_name):
            return joblib.load(self.file_name)
        return None

    def clear_cache(self):
        """
        Clear the cache by deleting the cache file if it exists.
        """
        if not self.file_name:
            raise ValueError("Cache file name is not set.")

        if os.path.exists(self.file_name):
            os.remove(self.file_name)
            print(f"Cache cleared: {self.file_name}")
        else:
            print("No cache file to clear.")

    def atualizar_todo_cache(self):

        if not os.path.exists(CACHE_DIR):
            print("No cache directory found.")
            return

        for file in os.listdir(CACHE_DIR):
            if file.endswith(".pkl"):
                file_path = os.path.join(CACHE_DIR, file)
                print(f"Updating cache: {file}")
                try:
                    # Load the cache file
                    df = joblib.load(file_path)

                    # Save the updated DataFrame back to the file
                    joblib.dump(df, file_path)
                    print(f"Cache updated: {file}")
                except Exception as e:
                    print(f"Failed to update {file}: {e}")


def start_cache():

    # CACHE(return_all_ranking_fast('GERAL', 2026), 'RANKING_GERAL_2025_2026').save_dataframe_to_cache()
    CACHE(return_all_ranking('NACIONAL', 2026), 'RANKING_NACIONAL_2026').save_dataframe_to_cache()
    CACHE(return_all_ranking('GERAL', 2026), 'RANKING_GERAL_2026').save_dataframe_to_cache()

    # CACHE(main_estabelecimento(), 'df_estabelecimentos_data').save_dataframe_to_cache()
    print("ok")
    # CACHE(get_ids_ano_eventos([2024]), 'dataframe_cache_eventos_2024').save_dataframe_to_cache()
    print("ok")
    # CACHE(get_ids_ano_eventos([2026]), 'dataframe_cache_eventos_2026').save_dataframe_to_cache()
    print("ok")
    # CACHE(main_atletas(), 'atletas_sge_cache').save_dataframe_to_cache()
    print("ok")
    # CACHE(whatsmart_table_normalized_names(2026), 'whatsmart_table_normalized_names_2026').save_dataframe_to_cache()

    # CACHE(rank_arena_all_data(), 'rank_arena_all_data').save_dataframe_to_cache()


if __name__ == "__main__":

    start_cache()
