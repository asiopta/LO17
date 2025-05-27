import spacy
from spacy.lang.fr.stop_words import STOP_WORDS as fr_stop
import pandas as pd
from nltk.stem import SnowballStemmer

# Charger le modèle de spaCy en français
nlp = spacy.load("fr_core_news_sm")
stemmer = SnowballStemmer("french")  # Pour le stemming

# ------------------------------------------------------
def create_lemmas(corpus, output):
    """
    Extrait les lemmes (forme canonique) de chaque mot dans le corpus
    et les enregistre dans un fichier CSV (mot, lemme).
    """
    with open(output, "a", encoding="utf-8") as f_w:
        f_w.write("mot\tlemme\n")  # En-tête
        with open(corpus, "r", encoding="utf-8") as f:
            for ligne in f.readlines():
                contenu = ligne
                if "<texte>" in ligne:
                    contenu = contenu.replace("<texte>", "").replace("</texte>", "")
                elif "<titre>" in ligne:
                    contenu = contenu.replace("<titre>", "").replace("</titre>", "")
                else:
                    continue  # Ignore les autres lignes

                nlp_content = nlp(contenu)
                for token in nlp_content:
                    if (token.text in fr_stop) or (token.is_space):
                        continue
                    to_write = f"{token.text}\t{token.lemma_}\n"
                    if to_write.lower() != to_write.upper():
                        f_w.write(to_write)

create_lemmas("../TD3/corpus_nettoyé2.XML", "./lemmes.csv")

# ------------------------------------------------------
def create_stems(corpus, output):
    """
    Extrait les racines (stems) de chaque mot du corpus
    et les enregistre dans un fichier CSV (mot, racine).
    """
    with open(output, "a", encoding="utf-8") as f_w:
        f_w.write("mot\tracine\n")
        with open(corpus, "r", encoding="utf-8") as f:
            for ligne in f.readlines():
                contenu = ligne
                if "<texte>" in ligne:
                    contenu = contenu.replace("<texte>", "").replace("</texte>", "")
                elif "<titre>" in ligne:
                    contenu = contenu.replace("<titre>", "").replace("</titre>", "")
                else:
                    continue

                nlp_content = nlp(contenu)
                for token in nlp_content:
                    if (token.text in fr_stop) or (token.is_space):
                        continue
                    to_write = f"{token.text}\t{stemmer.stem(token.text)}\n"
                    if to_write.lower() != to_write.upper():
                        f_w.write(to_write)

create_stems("../TD3/corpus_nettoyé2.XML", "stems.csv")

"""
Note : Parfois, les racines (stems) modifient les noms propres qu'on souhaite conserver.
On préfère donc utiliser les lemmes, car ils conservent mieux le sens des mots,
même si cela nécessite plus de ressources.
"""

# ------------------------------------------------------
def count_unique_lemmas(file_path):
    """
    Compte le nombre de lemmes uniques dans un fichier CSV (colonne 'lemme').
    """
    df = pd.read_csv(file_path, sep="\t")
    return df["lemme"].nunique()

count_unique_lemmas("C:/Users/ntich/OneDrive/Desktop/school shit/LO17/TD4/lemmes.csv")

# Compter les racines uniques
def count_unique_stems(file_path):
    """
    Compte le nombre de racines uniques dans un fichier CSV (colonne 'racine').
    """
    df = pd.read_csv(file_path, sep="\t")
    return df["racine"].nunique()

count_unique_stems("C:/Users/ntich/OneDrive/Desktop/school shit/LO17/TD4/stems.csv")

# ------------------------------------------------------
def substitue(texte, replacables, output):
    """
    Substitue les mots du fichier texte par leurs remplaçants définis dans le fichier CSV.
    """
    df = pd.read_csv(replacables, sep="\t")
    with open(output, "a", encoding="utf-8") as f_w:
        with open(texte, "r", encoding="utf-8") as f_r:
            for ligne in f_r.readlines():
                mots = ligne.split()
                for mot in mots:
                    match = df[df.iloc[:, 0] == mot]
                    if not match.empty:
                        f_w.write(str(match.iloc[0, 1]) + " ")
                    else:
                        f_w.write(mot + " ")
                f_w.write("\n")

substitue("../TD3/corpus_final.XML", "lemmes.csv", "corpus_post_final.XML")

# ------------------------------------------------------
def clean_contenu(texte):
    """
    Nettoie le texte en enlevant la ponctuation et certains articles français.
    """
    ponctuations = [".", ",", "?", ":", "\n", '"', '!']
    for ponct in ponctuations:
        texte = texte.replace(ponct, " ")

    articles_fr = [
        "le", "la", "les", "un", "une", "des", "du", "de la", "de l’", "de", "d'", "l’", "l'",
        "au", "aux", "à la", "à l’"
    ]
    for art in articles_fr:
        texte = texte.replace(" " + art, " ")
    return texte.lower()

# ------------------------------------------------------
# Création d'index inversé pour les titres
def create_reverse_index_titres(corpus, output_titres):
    index = {}
    with open(corpus, "r", encoding="utf-8") as f:
        doc_id = 0
        for ligne in f.readlines():
            if "<fichier>" in ligne:
                doc_id = ligne[9:14]
            if "<titre>" in ligne:
                texte = clean_contenu(ligne.replace("<titre>", "").replace("</titre>", ""))
                for mot in texte.split():
                    index.setdefault(mot, []).append(doc_id)

    with open(output_titres, "w", encoding="utf-8") as f_w:
        f_w.write("mot\tdocs\n")
        for key, tab in index.items():
            f_w.write(key + "\t" + str(tab) + "\n")

create_reverse_index_titres("corpus_post_lems.XML", "reverse_index_titre.csv")

# ------------------------------------------------------
# Création d'index inversé pour le texte
def create_reverse_index_texte(corpus, output_texte):
    index = {}
    with open(corpus, "r", encoding="utf-8") as f:
        doc_id = 0
        for ligne in f.readlines():
            if "<fichier>" in ligne:
                doc_id = ligne[9:14]
            if "<texte>" in ligne:
                texte = clean_contenu(ligne.replace("<texte>", "").replace("</texte>", ""))
                for mot in texte.split():
                    index.setdefault(mot, []).append(doc_id)

    with open(output_texte, "w", encoding="utf-8") as f_w:
        f_w.write("mot\tdocs\n")
        for key, tab in index.items():
            f_w.write(key + "\t" + str(tab) + "\n")

create_reverse_index_texte("corpus_post_lems.XML", "reverse_index_texte.csv")

# ------------------------------------------------------
# Création d'index inversé pour les dates
def create_reverse_index_date(corpus, output_date):
    index = {}
    with open(corpus, "r", encoding="utf-8") as f:
        doc_id = 0
        for ligne in f.readlines():
            if "<fichier>" in ligne:
                doc_id = ligne[9:14]
            if "<date>" in ligne:
                date = ligne.replace("<date>", "").replace("</date>", "").strip()
                index.setdefault(date, []).append(doc_id)

    with open(output_date, "w", encoding="utf-8") as f_w:
        f_w.write("mot\tdocs\n")
        for key, tab in index.items():
            f_w.write(key.lower() + "\t" + str(tab) + "\n")

create_reverse_index_date("corpus_post_lems.XML", "reverse_index_date.csv")

# ------------------------------------------------------
# Création d'index inversé pour les rubriques
def create_reverse_index_rubrique(corpus, output_rubrique):
    index = {}
    with open(corpus, "r", encoding="utf-8") as f:
        doc_id = 0
        for ligne in f.readlines():
            if "<fichier>" in ligne:
                doc_id = ligne[9:14]
            if "<rubrique>" in ligne:
                rubrique = ligne.replace("<rubrique>", "").replace("</rubrique>", "").strip()
                index.setdefault(rubrique, []).append(doc_id)

    with open(output_rubrique, "w", encoding="utf-8") as f_w:
        f_w.write("mot\tdocs\n")
        for key, tab in index.items():
            f_w.write(key.lower().strip() + "\t" + str(tab) + "\n")

create_reverse_index_rubrique("corpus_post_lems.XML", "reverse_index_rubrique.csv")

# ------------------------------------------------------
# Création d'index inversé pour les images
def create_reverse_index_images(corpus, output_image):
    index = {"yes": [], "no": []}
    with open(corpus, "r", encoding="utf-8") as f:
        doc_id = 0
        res = False
        for ligne in f.readlines():
            if "<bulletin>" in ligne:
                res = False
            if "<fichier>" in ligne:
                doc_id = ligne[9:14]
            if "<images>" in ligne:
                res = True
            if "</bulletin>" in ligne:
                if res:
                    index["yes"].append(doc_id)
                else:
                    index["no"].append(doc_id)

    with open(output_image, "w", encoding="utf-8") as f_w:
        f_w.write("mot\tdocs\n")
        for key, tab in index.items():
            f_w.write(key.lower() + "\t" + str(tab) + "\n")

create_reverse_index_images("corpus_post_lems.XML", "reverse_index_image.csv")
