

import pandas as pd
import numpy as np
import xml.etree.ElementTree as ET
import string
import re
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from collections import Counter
import spacy


INPUT_XML_TD2 = Path("corpus_td2.xml")
TOKENS_FILE = Path("td3_tokens.tsv")
TF_FILE = Path("td3_tf.tsv")
IDF_FILE = Path("td3_idf.tsv")
TFIDF_FILE = Path("td3_tfidf.tsv")
SORTED_TFIDF_FILE = Path("td3_tfidf_sorted.tsv")
ANTI_DICT_FILE = Path("td3_anti_dict.txt")
SUBSTITUTION_MAP_FILE = Path("td3_substitution_map.tsv")
OUTPUT_XML_TD3_FILTERED = Path("corpus_td3_filtered.xml")


# Seuils pour l'anti-dictionnaire
IDF_MIN_THRESHOLD_FOR_STOPWORD = 0.2
AVG_TFIDF_LOW_QUANTILE = 0.02

try:
    NLP_SPACY = spacy.load("fr_core_news_sm")
    print("Modèle spaCy 'fr_core_news_sm' chargé avec succès.")
except OSError:
    NLP_SPACY = exit()

# --- Étape 1 : Segmentation  ---

def tokenize_text_spacy(text: str) -> list:
    """
    Tokenise un texte en utilisant spaCy.
    Retourne une liste de mots (en minuscules), en filtrant la ponctuation et les espaces.
    """
    if not text or not NLP_SPACY:
        return []
    
    doc = NLP_SPACY(text)
    tokens = [
        token.lower_  # Convertit le token en minuscule
        for token in doc
        if not token.is_punct and not token.is_space and token.text.strip() # Filtre la ponctuation et les espaces vides
    ]
    return tokens

def segmente_from_xml(input_xml: Path, output_tokens_file: Path):
    """
    Lit le corpus XML, extrait les mots des balises <titre> et <texte> en utilisant spaCy,
    et écrit un fichier TSV (mot <tab> doc_id).
    """
    print(f"--- Étape 1: Segmentation de {input_xml} avec spaCy ---")
    if not input_xml.is_file():
        print(f"ERREUR: Fichier XML d'entrée '{input_xml}' non trouvé.")
        return False
    if not NLP_SPACY:
        print("ERREUR: Modèle spaCy non chargé. Segmentation impossible.")
        return False

    try:
        tree = ET.parse(input_xml)
        root = tree.getroot()
    except ET.ParseError as e:
        print(f"ERREUR: Impossible de parser le fichier XML '{input_xml}': {e}")
        return False

    doc_count = 0
    token_count = 0
    with open(output_tokens_file, "w", encoding="utf-8") as f_out:
        f_out.write("mot\tdoc_id\n") # En-tête TSV

        for bulletin in root.findall(".//bulletin"):
            doc_id_tag = bulletin.find("fichier")
            titre_tag = bulletin.find("titre")
            texte_tag = bulletin.find("texte")

            if doc_id_tag is not None and doc_id_tag.text:
                doc_id = doc_id_tag.text.strip()
                doc_count += 1
                
                full_text = ""
                if titre_tag is not None and titre_tag.text:
                    full_text += titre_tag.text + " "
                if texte_tag is not None and texte_tag.text:
                    full_text += texte_tag.text

                tokens = tokenize_text_spacy(full_text)

                for token in tokens:
                    f_out.write(f"{token}\t{doc_id}\n")
                    token_count += 1
            else:
                 print(f"WARN: Bulletin sans tag <fichier> ou avec contenu vide trouvé.")

    print(f"Segmentation spaCy terminée. {doc_count} documents traités, {token_count} tokens écrits dans {output_tokens_file}")
    return True


# --- Étape 2 : Calcul TF ---

def calculate_tf(input_tokens_file: Path, output_tf_file: Path):
    """Calcule TF et enregistre dans un fichier TSV (doc_id, mot, tf)."""
    print(f"--- Étape 2: Calcul TF depuis {input_tokens_file} ---")
    try:
        df = pd.read_csv(input_tokens_file, sep="\t")
        # Compter les occurrences (TF)
        tf_counts = df.groupby(["doc_id", "mot"]).size().reset_index(name="tf")
        tf_counts.to_csv(output_tf_file, sep='\t', index=False, encoding="utf-8")
        print(f"TF calculé et enregistré dans {output_tf_file}")
        return True
    except FileNotFoundError:
        print(f"ERREUR: Fichier d'entrée '{input_tokens_file}' non trouvé.")
        return False
    except Exception as e:
        print(f"ERREUR: Erreur lors du calcul TF: {e}")
        return False

# --- Étape 3 : Calcul IDF ---

def calculate_idf(input_tf_file: Path, output_idf_file: Path):
    """Calcule IDF et enregistre dans un fichier TSV (mot, idf)."""
    print(f"--- Étape 3: Calcul IDF depuis {input_tf_file} ---")
    try:
        df_tf = pd.read_csv(input_tf_file, sep='\t')

        # Nombre total de documents (N)
        N = df_tf["doc_id"].nunique()
        if N == 0:
             print("ERREUR: Aucun document trouvé dans le fichier TF.")
             return False
        print(f"Nombre total de documents (N) = {N}")

        # Nombre de documents contenant chaque mot (DFt)
        dft = df_tf.groupby("mot")["doc_id"].nunique().reset_index(name="dft")

        # Calcul IDF: log10(N / DFt)
        # Ajout de 1 au dénominateur (N / (dft + 1)) pour éviter log10(inf) si dft=0 (ne devrait pas arriver ici)
        # Ou on peut filtrer les mots qui ont dft > 0
        dft = dft[dft['dft'] > 0].copy() # S'assurer que DFt > 0
        dft["idft"] = np.log10(N / dft["dft"])

        # Sauvegarder mot et idft
        dft[["mot", "idft"]].to_csv(output_idf_file, sep='\t', index=False, encoding="utf-8")
        print(f"IDF calculé pour {len(dft)} mots et enregistré dans {output_idf_file}")
        return True
    except FileNotFoundError:
        print(f"ERREUR: Fichier d'entrée '{input_tf_file}' non trouvé.")
        return False
    except Exception as e:
        print(f"ERREUR: Erreur lors du calcul IDF: {e}")
        return False


# --- Étape 4 : Calcul TF-IDF ---

def calculate_tfidf(tf_file: Path, idf_file: Path, output_tfidf_file: Path):
    """Calcule TF-IDF et enregistre dans un fichier TSV (doc_id, mot, tfidf)."""
    print(f"--- Étape 4: Calcul TF-IDF ---")
    try:
        tf_data = pd.read_csv(tf_file, sep="\t")
        idf_data = pd.read_csv(idf_file, sep="\t")

        # Fusionner TF et IDF sur 'mot'
        tfidf_df = pd.merge(tf_data, idf_data, on="mot", how="inner") # inner pour garder mots présents dans les deux

        # Calculer TF-IDF
        tfidf_df["tfidf"] = tfidf_df["tf"] * tfidf_df["idft"]

        # Sauvegarder doc_id, mot, tfidf
        tfidf_df[["doc_id", "mot", "tfidf"]].to_csv(output_tfidf_file, sep='\t', index=False, encoding="utf-8")
        print(f"TF-IDF calculé et enregistré dans {output_tfidf_file}")
        return True, tfidf_df # Retourner aussi le DataFrame pour analyse
    except FileNotFoundError:
        print(f"ERREUR: Fichiers TF '{tf_file}' ou IDF '{idf_file}' non trouvés.")
        return False, None
    except Exception as e:
        print(f"ERREUR: Erreur lors du calcul TF-IDF: {e}")
        return False, None

# --- Étape 5 : Analyse et création de l'Anti-dictionnaire ---

def plot_tfidf_histogram(tfidf_df: pd.DataFrame, bins=50, column_name="tfidf", title_suffix=""):
    """Affiche un histogramme des scores TF-IDF (limité pour la lisibilité)."""
    if tfidf_df is None or tfidf_df.empty:
        print(f"WARN: Impossible de générer l'histogramme {column_name} (pas de données).")
        return

    print(f"--- Étape 5a: Analyse TF-IDF (Histogramme {column_name}{title_suffix}) ---")
    plt.figure(figsize=(12, 7))
    # Si c'est le tfidf brut, on peut le limiter pour la visualisation
    data_to_plot = tfidf_df[column_name]
    if column_name == "tfidf": # Si c'est le tfidf brut, on peut le limiter
        data_to_plot = tfidf_df[column_name].clip(upper=tfidf_df[column_name].quantile(0.99))


    sns.histplot(data=data_to_plot, bins=bins, kde=True)
    plt.title(f'Distribution des Scores {column_name.upper()}{title_suffix}')
    plt.xlabel(f"Score {column_name.upper()}")
    plt.ylabel("Fréquence")
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.show()
    print(f"[+] Visualisation de l'histogramme {column_name.upper()}{title_suffix} affichée.")


def create_anti_dictionary_refined(tfidf_file: Path, idf_file: Path, output_anti_dict_file: Path, N_total_documents: int):
    """
    Crée l'anti-dictionnaire de manière affinée :
    1. Mots avec IDF très bas (très fréquents dans les documents).
    2. Mots avec TF-IDF moyen très bas (globalement peu informatifs).
    """
    print(f"--- Étape 5b: Création de l'anti-dictionnaire ---")
    try:
        df_tfidf = pd.read_csv(tfidf_file, sep='\t')
        df_idf = pd.read_csv(idf_file, sep='\t')
    except FileNotFoundError:
        print(f"ERREUR: Fichier TF-IDF '{tfidf_file}' ou IDF '{idf_file}' non trouvé.")
        return None

    stop_words_set = set()

    # Stratégie 1: Mots très communs basés sur l'IDF
    # Un IDF bas signifie que le mot apparaît dans de nombreux documents.
    print(f"Nombre total de documents pour calcul IDF anti-dict: {N_total_documents}")
    idf_threshold_value = IDF_MIN_THRESHOLD_FOR_STOPWORD 
    common_words_by_idf = set(df_idf[df_idf['idft'] < idf_threshold_value]['mot'].unique())
    print(f"Mots identifiés comme très communs (IDF < {idf_threshold_value:.2f}): {len(common_words_by_idf)}")
    stop_words_set.update(common_words_by_idf)

    # Afficher quelques exemples de mots communs trouvés
    if len(common_words_by_idf) > 0:
        print(f"  Exemples de mots communs (par IDF): {list(common_words_by_idf)[:15]}")


    # Stratégie 2: Mots avec TF-IDF moyen très bas
    # Ces mots, même s'ils ne sont pas dans tous les documents, ont globalement peu de poids.
    avg_tfidf_per_word = df_tfidf.groupby('mot')['tfidf'].mean().reset_index(name='avg_tfidf')
    
    # Visualisation de la distribution des TF-IDF moyens
    plot_tfidf_histogram(avg_tfidf_per_word, column_name="avg_tfidf", title_suffix=" Moyen par Mot")

    avg_tfidf_low_threshold = avg_tfidf_per_word['avg_tfidf'].quantile(AVG_TFIDF_LOW_QUANTILE)
    print(f"Seuil pour TF-IDF moyen bas (Quantile {AVG_TFIDF_LOW_QUANTILE}): {avg_tfidf_low_threshold:.4f}")
    
    low_avg_tfidf_words = set(avg_tfidf_per_word[avg_tfidf_per_word['avg_tfidf'] < avg_tfidf_low_threshold]['mot'].unique())
    # On s'assure de ne pas ré-ajouter des mots déjà identifiés par l'IDF bas, même si c'est peu probable
    newly_added_low_avg_tfidf = low_avg_tfidf_words - stop_words_set
    print(f"Mots identifiés par faible TF-IDF moyen (et non déjà par IDF bas): {len(newly_added_low_avg_tfidf)}")
    if len(newly_added_low_avg_tfidf) > 0:
        print(f"  Exemples de mots à faible TF-IDF moyen: {list(newly_added_low_avg_tfidf)[:15]}")
    stop_words_set.update(newly_added_low_avg_tfidf)

    with open(output_anti_dict_file, "w", encoding="utf-8") as f_out:
        for word in sorted(list(stop_words_set)):
            f_out.write(f"{word}\n")

    print(f"Anti-dictionnaire affiné créé avec {len(stop_words_set)} mots et enregistré dans {output_anti_dict_file}")
    return stop_words_set


# --- Étape 6 : Filtrage du Corpus XML (amélioré) ---

def filter_xml_corpus(input_xml: Path, stop_words: set, output_xml_file: Path):
    """
    Lit le corpus XML, supprime les mots de l'anti-dictionnaire
    des balises <titre> et <texte>, et écrit un nouveau fichier XML filtré.
    """
    print(f"--- Étape 6: Filtrage de {input_xml} ---")
    if not input_xml.is_file():
        print(f"ERREUR: Fichier XML d'entrée '{input_xml}' non trouvé.")
        return False
    if not stop_words:
        print("WARN: L'anti-dictionnaire est vide, aucun filtrage ne sera effectué.")
        return False


    try:
        tree = ET.parse(input_xml)
        root = tree.getroot()
    except ET.ParseError as e:
        print(f"ERREUR: Impossible de parser le fichier XML '{input_xml}': {e}")
        return False

    bulletins_processed = 0
    for bulletin in root.findall(".//bulletin"):
        bulletins_processed += 1
        for tag_name in ["titre", "texte"]:
            tag = bulletin.find(tag_name)
            if tag is not None and tag.text:
                original_text = tag.text
                tokens = tokenize_text_spacy(original_text)
                filtered_tokens = [token for token in tokens if token not in stop_words]
                tag.text = " ".join(filtered_tokens)

    # Sauvegarder l'arbre XML modifié
    try:
        tree.write(output_xml_file, encoding="utf-8", xml_declaration=True)
        print(f"Corpus XML filtré enregistré dans {output_xml_file}")

        return True
    except Exception as e:
        print(f"ERREUR: Impossible d'écrire le fichier XML filtré '{output_xml_file}': {e}")
        return False

# --- Point d'entrée ---
if __name__ == "__main__":
    print("=== DÉBUT TRAITEMENT TD3 ===")
    if not NLP_SPACY:
        print("Arrêt du script car le modèle spaCy n'a pas pu être chargé.")
    # Étape 1
    elif not segmente_from_xml(INPUT_XML_TD2, TOKENS_FILE):
        print("Arrêt du script à cause d'une erreur de segmentation.")
    # Étape 2
    elif not calculate_tf(TOKENS_FILE, TF_FILE):
        print("Arrêt du script à cause d'une erreur de calcul TF.")
    # Étape 3
    elif not calculate_idf(TF_FILE, IDF_FILE):
        print("Arrêt du script à cause d'une erreur de calcul IDF.")
    # Étape 4
    else:
        success_tfidf, df_tfidf_global = calculate_tfidf(TF_FILE, IDF_FILE, TFIDF_FILE)
        if not success_tfidf:
            print("Arrêt du script à cause d'une erreur de calcul TF-IDF.")
        else:
            # Étape 5
            plot_tfidf_histogram(df_tfidf_global, column_name="tfidf", title_suffix=" Global") # Histogramme des TF-IDF bruts

            # Recharger les dataframes nécessaires pour create_anti_dictionary
            try:
                # N_total_documents est déjà calculé dans calculate_idf et peut être récupéré si calculate_idf le retourne
                # ou recalculé ici à partir de TF_FILE
                df_tf_for_N = pd.read_csv(TF_FILE, sep='\t')
                N_docs = df_tf_for_N["doc_id"].nunique()
                
                df_idf_for_anti_dict = pd.read_csv(IDF_FILE, sep='\t')
                
                
                stop_words = create_anti_dictionary_refined(TFIDF_FILE, IDF_FILE, ANTI_DICT_FILE, N_docs)

            except FileNotFoundError:
                print(f"ERREUR: Fichiers TF '{TF_FILE}' ou IDF '{IDF_FILE}' non trouvés pour la création de l'anti-dict.")
                stop_words = None
            except Exception as e:
                print(f"ERREUR inattendue lors de la préparation pour l'anti-dictionnaire: {e}")
                stop_words = None
            
            # Étape 6
            if stop_words is not None:
                filter_xml_corpus(INPUT_XML_TD2, stop_words, OUTPUT_XML_TD3_FILTERED)
            else:
                print("Anti-dictionnaire non créé ou vide, filtrage du corpus XML annulé.")

    print("=== FIN TRAITEMENT TD3 ===")