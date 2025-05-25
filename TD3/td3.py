"""
Faut-il utiliser comme unité documentaire un bulletin ou un article ?
Je dirais plutôt "bulletin", car chercher la fréquence d'apparition d'un mot dans un simple titre d'image, par exemple,
n'aurait que peu de sens. 
De plus, par la suite, nous nous intéresserons à rechercher des bulletins en fonction de mots spécifiques,
plutôt que de simples textes ou d'une seule image.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# ------------------------------------------------------
def calculate_coeff(input_file, output_file):
    """
    Calcule le nombre d'occurrences des mots dans chaque document
    et l'enregistre dans un fichier CSV.
    """
    df = pd.read_csv(input_file, sep="\t")
    # Nombre d'occurrences (tf) par (mot, doc_id)
    counts = df.groupby(["mot", "doc_id"]).size().reset_index(name="tf")
    counts.to_csv(output_file, sep='\t', index=False, encoding="utf-8")

# ------------------------------------------------------
def calculate_idf(input_file, output_file):
    """
    Calcule les coefficients IDF pour chaque mot
    et les enregistre dans un fichier TSV.
    """
    df = pd.read_csv(input_file, sep='\t')
    N = df["doc_id"].nunique()  # Nombre total de documents
    print(N)

    # Nombre de documents par mot
    dft = df.groupby("mot")["doc_id"].nunique().reset_index(name="dft")
    
    # Calcul de l'IDF
    dft["idft"] = np.log10(N / dft["dft"])
    dft[["mot", "idft"]].to_csv(output_file, sep='\t', index=False, encoding="utf-8")

# ------------------------------------------------------
def final_calculation(tf, idf, output):
    """
    Calcule le score TF*IDF pour chaque (mot, doc_id) et l'enregistre dans un fichier CSV.
    """
    tf_data = pd.read_csv(tf, sep="\t")
    idf_data = pd.read_csv(idf, sep="\t")

    # Fusion des deux DataFrames sur la colonne "mot"
    final_df = tf_data.merge(idf_data, on="mot", how="inner")
    final_df["tf*idf"] = final_df["tf"] * final_df["idft"]

    final_df[["doc_id", "mot", "tf*idf"]].to_csv(output, sep='\t', index=False, encoding="utf-8")

# ------------------------------------------------------
def plot_tf_idf_histogram(tf_idf_file, bins=20):
    """
    Affiche un histogramme des valeurs TF*IDF (inférieures ou égales à 10).
    """
    df = pd.read_csv(tf_idf_file, sep='\t')
    data = df[df["tf*idf"] <= 10]  # Filtre les valeurs trop grandes pour la visualisation

    plt.figure(figsize=(10, 6))
    sns.histplot(data, bins=bins, alpha=0.7)
    plt.xlabel("TF*IDF")
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.show()

# ------------------------------------------------------
def extract_first_quantile(file_path, output_path, qt1=0.1):
    """
    Extrait les mots dont le TF*IDF est inférieur au premier quantile (qt1).
    """
    df = pd.read_csv(file_path, sep="\t")
    q1 = df["tf*idf"].quantile(qt1)
    first_quartile_df = df[df["tf*idf"] <= q1]
    first_quartile_df.to_csv(output_path, sep="\t", index=False, encoding="utf-8")
    print(f"Q{qt1} Value: {q1}")

# Utilisation concrète (valeur finale choisie après visualisation)
extract_first_quantile("data/sorted_data.csv", "data/q=0.17.csv", 0.17)
# Choix final : 0.15 comme seuil max pour ne garder que des mots parasites

# ------------------------------------------------------
def extract_last_quartile(file_path, output_path, qt2=0.9):
    """
    Extrait les mots dont le TF*IDF est supérieur au dernier quantile (qt2).
    """
    df = pd.read_csv(file_path, sep="\t")
    qt = df["tf*idf"].quantile(qt2)
    last_quartile_df = df[df["tf*idf"] >= qt]
    last_quartile_df.to_csv(output_path, sep="\t", index=False, encoding="utf-8")
    print(f"Last quartile extracted and saved to {output_path}")
    print(f"Q{qt2} Value: {qt}")

extract_last_quartile("data/sorted_data.csv", "data/lq=0.95.csv", 0.95)

# ------------------------------------------------------
def create_anti_dict(file_path, output_path):
    """
    Crée un anti-dictionnaire en combinant les mots à faible et forte valeur de TF*IDF.
    """
    df = pd.read_csv(file_path, sep="\t")
    q1 = df["tf*idf"].quantile(0.17)

    # Mots à enlever (faible TF*IDF ou très élevé)
    to_remove = df[df["tf*idf"] <= q1]
    to_remove = pd.concat([to_remove, df[df["tf*idf"] >= 15]])

    # Garde seulement la colonne "mot" unique
    to_remove = to_remove["mot"].drop_duplicates().to_frame()
    to_remove.to_csv(output_path, sep="\t", index=False, encoding="utf-8", header=True)

create_anti_dict("data/sorted_data.csv", "anti_dict3.csv")

# ------------------------------------------------------
# Préparation du CSV pour la substitution (mot parasite → vide)
words_to_remove = pd.read_csv("C:/Users/ntich/OneDrive/Desktop/school shit/LO17/TD3/anti_dict3.csv")
words_to_remove[1] = " "  # Ajoute la colonne de remplacement (vide)
words_to_remove.to_csv("C:/Users/ntich/OneDrive/Desktop/school shit/LO17/TD3/anti_dict2.csv",
                        sep="\t", index=False, header=True)

# ------------------------------------------------------
# Import des fonctions pour segmentation et substitution
from segmente import *
from substitue import *

# Substitue les mots parasites du corpus nettoyé
substitue("../TD2/corpus.XML", "anti_dict3.csv", "corpus_nettoyé3.XML")

# ------------------------------------------------------
def delete_empty_lines(corpus, result):
    """
    Supprime les lignes vides dans un fichier texte.
    """
    with open(result, "a", encoding="utf-8") as f_w:
        with open(corpus, "r", encoding="utf-8") as f_r:
            for ligne in f_r.readlines():
                if ligne.strip():  # Ignore les lignes vides ou "\n"
                    f_w.write(ligne)

delete_empty_lines("corpus_nettoyé3.XML", "corpus_final.XML")

# ------------------------------------------------------
if __name__ == "__main__":
    # Étape 1 : Calcul des fréquences
    calculate_coeff("dict_complet.csv", "tf.csv")
    calculate_idf("occurences.csv", "idf_coefficients.csv")
    final_calculation("tf.csv", "idf_coefficients.csv", "output.csv")
    
    # Étape 2 : Visualisation
    plot_tf_idf_histogram("output.csv")
    
    # Étape 3 : Trie final
    final_data = pd.read_csv("C:/Users/ntich/OneDrive/Desktop/school shit/LO17/TD3/output.csv", sep='\t')
    sorted_data = final_data.sort_values("tf*idf")
    sorted_data.to_csv("C:/Users/ntich/OneDrive/Desktop/school shit/LO17/TD3/sorted_data.csv",
                       sep='\t', index=False, encoding="utf-8")
