import numpy as np
import pandas as pd
import ast

# ---------------------------------------------------------------
# Compare les composants d'une date (jour, mois, année)
# ---------------------------------------------------------------
def compare_date_components(day_doc, month_doc, year_doc, day_req, month_req, year_req):
    """
    Compare deux ensembles de composantes de date.
    Renvoie :
        -1 si la date du document < date de la requête
         0 si égalité
         1 si la date du document > date de la requête
    """
    # Année
    if year_req is not None:
        if int(year_doc) < int(year_req):
            return -1
        elif int(year_doc) > int(year_req):
            return 1
    # Mois
    if month_req is not None:
        if int(month_doc) < int(month_req):
            return -1
        elif int(month_doc) > int(month_req):
            return 1
    # Jour
    if day_req is not None:
        if int(day_doc) < int(day_req):
            return -1
        elif int(day_doc) > int(day_req):
            return 1
    return 0

# ---------------------------------------------------------------
# Compare la date d'un document à une contrainte de date de requête
# ---------------------------------------------------------------
def compare_dates(date_doc, date_requete):
    """
    Vérifie si la date du document (format 'j/m/a') satisfait la requête de date (dictionnaire avec "début", "fin", "précis", "not").
    """
    # Conversion des composants
    day_doc, month_doc, year_doc = [int(e) for e in date_doc.split('/')]

    # Cas où aucune contrainte n'est spécifiée
    if all(date_requete.get(k) is None for k in ["début", "fin", "précis", "not"]):
        return True

    # Cas "not"
    not_req = date_requete.get("not")
    if not_req is not None:
        match = True
        if not_req["a"] and int(year_doc) != int(not_req["a"]):
            match = False
        if not_req["m"] and int(month_doc) != int(not_req["m"]):
            match = False
        if not_req["j"] and int(day_doc) != int(not_req["j"]):
            match = False
        if match:
            return False

    # Cas "précis"
    precis = date_requete.get("précis")
    if precis is not None:
        match = True
        if precis["a"] and int(year_doc) != int(precis["a"]):
            match = False
        if precis["m"] and int(month_doc) != int(precis["m"]):
            match = False
        if precis["j"] and int(day_doc) != int(precis["j"]):
            match = False
        return match

    # Cas "début"
    res = True
    debut = date_requete.get("début")
    if debut is not None:
        cmp = compare_date_components(
            day_doc, month_doc, year_doc,
            debut.get("j"), debut.get("m"), debut.get("a")
        )
        if cmp < 0:
            res = False

    # Cas "fin"
    fin = date_requete.get("fin")
    if fin is not None:
        cmp = compare_date_components(
            day_doc, month_doc, year_doc,
            fin.get("j"), fin.get("m"), fin.get("a")
        )
        if cmp > 0:
            res = False

    return res

'''
    resultats = {
        "return": None,
        "mots_cles": {"yes": [], "no": None},
        "operateurs_mots_cles": None,
        "rubrique": None,
        "operateurs_rubrique": None,
        "dates": {"debut": None, "fin": None, "précis": None, "not": None},
        "titre": None,
        "operateurs_titre": None,
        "images": None
    }

'''

# ---------------------------------------------------------------
# Recherche les documents pertinents pour une requête donnée
# ---------------------------------------------------------------
def recherche_documents(resultats, index_inverse_texte, index_inverse_date, index_inverse_rubrique, index_inverse_titre, index_inverse_image):
    """
    Fonction principale de recherche. Combine les critères de la requête pour trouver les documents pertinents.
    """
    docs_cherches = []

    # 1️⃣ Partie mots-clés
    mots_cles = resultats["mots_cles"]
    if len(mots_cles["yes"]) != 0:
        dict_match_key = {}
        index_texte = pd.read_csv(index_inverse_texte, sep="\t")
        for mot in mots_cles["yes"]:
            docs = index_texte.loc[index_texte["mot"] == mot, "docs"].values[0]
            dict_match_key[mot] = docs
        if resultats["operateurs_mots_cles"] == "ou":
            docs_key = list(set.union(*(set(ast.literal_eval(l)) for l in dict_match_key.values())))
        else:
            docs_key = list(set.intersection(*(set(ast.literal_eval(l)) for l in dict_match_key.values())))
        docs_cherches = docs_key

    # 2️⃣ Partie titre
    titres = resultats["titre"]
    if titres is not None:
        dict_match_titre = {}
        index_titre = pd.read_csv(index_inverse_titre, sep='\t')
        if not isinstance(titres, list):
            titres = [titres]
        for titre in titres:
            docs = index_titre.loc[index_titre["mot"] == titre, "docs"].values[0]
            dict_match_titre[titre] = docs
        if resultats["operateurs_titre"] == "ou":
            docs_titre = list(set.union(*(set(ast.literal_eval(l)) for l in dict_match_titre.values())))
        else:
            docs_titre = list(set.intersection(*(set(ast.literal_eval(l)) for l in dict_match_titre.values())))
        docs_cherches = docs_cherches if docs_cherches else docs_titre
        docs_cherches = list(set(docs_cherches) & set(docs_titre))

    # 3️⃣ Partie rubrique
    rubriques = resultats["rubrique"]
    if rubriques is not None:
        dict_match_rubrique = {}
        index_rubrique = pd.read_csv(index_inverse_rubrique, sep='\t')
        if not isinstance(rubriques, list):
            rubriques = [rubriques]
        for rubrique in rubriques:
            docs_matchs = index_rubrique.loc[index_rubrique["mot"] == rubrique, "docs"].values
            if len(docs_matchs) > 0:
                dict_match_rubrique[rubrique] = docs_matchs[0]
            else:
                print(f"⚠️ Rubrique introuvable : {rubrique}")
        if resultats["operateurs_rubrique"] == "ou":
            docs_rub = list(set.union(*(set(ast.literal_eval(l)) for l in dict_match_rubrique.values())))
        else:
            docs_rub = list(set.intersection(*(set(ast.literal_eval(l)) for l in dict_match_rubrique.values())))
        docs_cherches = docs_cherches if docs_cherches else docs_rub
        docs_cherches = list(set(docs_cherches) & set(docs_rub))

    # 4️⃣ Partie images
    image = resultats["images"]
    if image is not None:
        index_image = pd.read_csv(index_inverse_image, sep='\t')
        docs_match_image = index_image.loc[index_image["mot"] == "yes", "docs"].values[0]
        docs_cherches = docs_cherches if docs_cherches else ast.literal_eval(docs_match_image)
        docs_cherches = list(set(docs_cherches) & set(ast.literal_eval(docs_match_image)))

    # 5️⃣ Partie date
    date = resultats["dates"]
    if any(date[k] is not None for k in ["début", "fin", "précis", "not"]):
        index_date = pd.read_csv(index_inverse_date, sep='\t')
        docs_date = []
        for _, row in index_date.iterrows():
            date_doc = row["mot"]
            if compare_dates(date_doc, date):
                docs = ast.literal_eval(row["docs"])
                docs_date.extend(docs)
        docs_cherches = docs_cherches if docs_cherches else docs_date
        docs_cherches = list(set(docs_cherches) & set(docs_date))

    # 6️⃣ Partie "not"
    mot_cles_not = mots_cles["no"]
    if mot_cles_not is not None:
        index_texte = pd.read_csv(index_inverse_texte, sep="\t")
        docs_exclus = ast.literal_eval(index_texte.loc[index_texte["mot"] == mot_cles_not, "docs"].values[0])
        docs_cherches = list(set(docs_cherches) - set(docs_exclus))

    return docs_cherches

# ---------------------------------------------------------------
# Programme principal
# ---------------------------------------------------------------
from td5 import *
from td6 import *

if __name__ == "__main__":
    requete = input("Entrez votre requête en langage naturel : ")
    resultat = traiter_requete(requete)

    # Correction orthographique
    lemmes_path = "lemmes.csv"
    if resultat["mots_cles"]["no"] is not None:
        resultat["mots_cles"]["no"] = correction_orthographique(resultat["mots_cles"]["no"], lemmes_path)
    for i in range(len(resultat["mots_cles"]["yes"])):
        resultat["mots_cles"]["yes"][i] = correction_orthographique(resultat["mots_cles"]["yes"][i], lemmes_path)

    print("Requête corrigée :")
    print(resultat)
    print("-------------------------------------------")

    # Recherche des documents pertinents
    index_inverse_texte = "../TD4/reverse_index_texte.csv"
    index_inverse_date = "../TD4/reverse_index_date.csv"
    index_inverse_rubrique = "../TD4/reverse_index_rubrique.csv"
    index_inverse_titre = "../TD4/reverse_index_titre.csv"
    index_inverse_image = "../TD4/reverse_index_image.csv"
    documents = recherche_documents(resultat, index_inverse_texte, index_inverse_date, index_inverse_rubrique, index_inverse_titre, index_inverse_image)
    print(documents)
