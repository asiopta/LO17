def compare_date_components(day_doc, month_doc, year_doc, day_req, month_req, year_req):
    """
    Compare individuellement les composantes jour, mois et année entre la date d'un document
    et les valeurs de la requête (si elles existent).

    ⚠️ La date du document est toujours complète, mais la requête peut avoir des champs vides (None).
    
    Retourne :
    -1 si date_doc < date_req (sur le premier champ significatif trouvé)
     0 si égalité
     1 si date_doc > date_req
    """
    # Comparer l'année en priorité si précisée dans la requête
    if year_req is not None:
        if int(year_doc) < int(year_req):
            return -1
        elif int(year_doc) > int(year_req):
            return 1

    # Puis comparer le mois si précisé
    if month_req is not None:
        if int(month_doc) < int(month_req):
            return -1
        elif int(month_doc) > int(month_req):
            return 1

    # Enfin, comparer le jour si précisé
    if day_req is not None:
        if int(day_doc) < int(day_req):
            return -1
        elif int(day_doc) > int(day_req):
            return 1

    # Si tous les champs connus sont égaux ou absents, retour 0 (égalité)
    return 0


def compare_dates(date_doc, date_requete):
    """
    Vérifie si une date de document (format 'j/m/a') correspond à un ensemble
    de critères de la requête (début, fin, précis, exclusion).

    Paramètres :
    - date_doc (str) : la date du document au format 'j/m/a'
    - date_requete (dict) : dictionnaire avec les éventuels champs :
        {"début", "fin", "précis", "not"}, chacun valant :
        {"j":..., "m":..., "a":...} ou None

    Retourne :
    True si la date du document est compatible avec la requête, False sinon.
    """
    # Séparer la date du document en composantes numériques
    day_doc, month_doc, year_doc = map(int, date_doc.split('/'))

    # 🚀 Cas simple : aucune contrainte, tout est valide
    if all(date_requete.get(k) is None for k in ["début", "fin", "précis", "not"]):
        return True

    # ⛔ Gestion de l'exclusion ("not") : la date NE doit PAS correspondre exactement à "not"
    not_req = date_requete.get("not")
    if not_req is not None:
        jn, mn, an = not_req.get("j"), not_req.get("m"), not_req.get("a")
        match = True  # True = potentiellement la même date
        if an is not None and int(year_doc) != int(an):
            match = False
        if mn is not None and int(month_doc) != int(mn):
            match = False
        if jn is not None and int(day_doc) != int(jn):
            match = False
        if match:
            return False  # Exactement la date "not" => rejetée

    # ✅ Gestion de la date précise : doit correspondre exactement à "précis"
    precis = date_requete.get("précis")
    if precis is not None:
        jp, mp, ap = precis.get("j"), precis.get("m"), precis.get("a")
        match = True
        if ap is not None and int(year_doc) != int(ap):
            match = False
        if mp is not None and int(month_doc) != int(mp):
            match = False
        if jp is not None and int(day_doc) != int(jp):
            match = False
        return match  # Soit True (correspond) soit False (non-correspondance)

    # 🔍 Vérification des bornes de période (début / fin)
    res = True  # Par défaut valide

    # ▪️ Vérifie la borne de début : date_doc >= date_requete["début"]
    debut = date_requete.get("début")
    if debut is not None:
        jd, md, ad = debut.get("j"), debut.get("m"), debut.get("a")
        cmp = compare_date_components(
            day_doc, month_doc, year_doc,
            int(jd) if jd is not None else None,
            int(md) if md is not None else None,
            int(ad) if ad is not None else None
        )
        if cmp < 0:
            res = False  # document trop ancien

    # ▪️ Vérifie la borne de fin : date_doc <= date_requete["fin"]
    fin = date_requete.get("fin")
    if fin is not None:
        jf, mf, af = fin.get("j"), fin.get("m"), fin.get("a")
        cmp = compare_date_components(
            day_doc, month_doc, year_doc,
            int(jf) if jf is not None else None,
            int(mf) if mf is not None else None,
            int(af) if af is not None else None
        )
        if cmp > 0:
            res = False  # document trop récent

    return res

import pandas as pd
import ast

def recherche_documents(resultats, index_inverse_texte, index_inverse_date, index_inverse_rubrique, index_inverse_titre, index_inverse_image):
    """
    Recherche les documents correspondant aux critères de la requête (résultats)
    en consultant les index inversés fournis.

    Paramètres :
    - resultats : dict contenant les critères (mots clés, dates, rubriques, etc.)
    - index_inverse_* : chemins vers les index inversés (CSV)

    Retourne :
    - Liste finale des documents trouvés (ou rubriques si spécifié)
    """

    # Liste finale des documents trouvés
    docs_cherches = []

    ##############################################################
    # Partie 1 : Traitement des mots-clés positifs ("yes")
    ##############################################################
    mots_cles = resultats["mots_cles"]
    if len(mots_cles["yes"]) != 0:
        dict_match_key = {}
        index_texte = pd.read_csv(index_inverse_texte, sep="\t")

        for mot in mots_cles["yes"]:
            # Chercher les documents associés à ce mot (après suppression des espaces superflus)
            docs_qui_matchs = index_texte.loc[index_texte["mot"] == mot.strip(), "docs"].values
            if len(docs_qui_matchs) != 0:
                dict_match_key[mot] = docs_qui_matchs[0]

        # Fusionner les résultats en fonction de l'opérateur (et/ou)
        if len(dict_match_key.keys()) == 1:
            docs_key = list(set(e.strip() for e in ast.literal_eval(list(dict_match_key.values())[0])))
        else:
            if resultats["operateurs_mots_cles"] == "ou":
                docs_key = list(set().union(*(set(e.strip() for e in ast.literal_eval(l)) for l in dict_match_key.values())))
            else:  # "et"
                docs_key = list(set.intersection(*(set(e.strip() for e in ast.literal_eval(l)) for l in dict_match_key.values())))

        # Fusion avec la liste globale des résultats
        if len(docs_cherches) == 0:
            docs_cherches = docs_key
        else:
            docs_cherches = list(set(docs_cherches) & set(docs_key))
    print("doc_cherches post mots_clés:", docs_cherches)

    ##############################################################
    # Partie 2 : Traitement des titres
    ##############################################################
    titres = resultats["titre"]
    if titres is not None:
        dict_match_titre = {}
        index_titre = pd.read_csv(index_inverse_titre, sep='\t')

        # Si un seul titre (chaîne), le mettre sous forme de liste
        if not isinstance(titres, list):
            titres = [titres]

        for titre in titres:
            # Nettoyer le titre en retirant espaces et guillemets
            for tr in [" ", '"', "'"]:
                titre = titre.replace(tr, '')
            docs_qui_matchs = index_titre.loc[index_titre["mot"] == titre, "docs"].values
            if len(docs_qui_matchs) > 0:
                dict_match_titre[titre] = docs_qui_matchs[0]
            else:
                print(f"⚠️ Titre introuvable : {titre}")

        # Fusionner les résultats (et/ou)
        if len(dict_match_titre.keys()) == 1:
            docs_titre = list(set(e.strip() for e in ast.literal_eval(list(dict_match_titre.values())[0])))
        else:
            if resultats["operateurs_titre"] == "ou":
                docs_titre = list(set().union(*(set(e.strip() for e in ast.literal_eval(l)) for l in dict_match_titre.values())))
            else:
                docs_titre = list(set.intersection(*(set(e.strip() for e in ast.literal_eval(l)) for l in dict_match_titre.values())))

        # Fusion avec la liste globale
        if len(docs_cherches) == 0:
            docs_cherches = docs_titre
        else:
            docs_cherches = list(set(docs_cherches) & set(docs_titre))
    print("doc_cherches post titre:", docs_cherches)

    ##############################################################
    # Partie 3 : Traitement des rubriques
    ##############################################################
    rubriques = resultats["rubrique"]
    if rubriques is not None:
        dict_match_rubrique = {}
        index_rubrique = pd.read_csv(index_inverse_rubrique, sep='\t')

        # Si une seule rubrique, la mettre sous forme de liste
        if not isinstance(rubriques, list):
            rubriques = [rubriques.strip()]

        for rubrique in rubriques:
            rubrique = rubrique.strip()
            docs_matchs = index_rubrique.loc[index_rubrique["mot"] == rubrique, "docs"].values
            if len(docs_matchs) > 0:
                dict_match_rubrique[rubrique] = docs_matchs[0]
            else:
                print(f"⚠️ Rubrique introuvable : {rubrique}")

        # Fusion des résultats (et/ou)
        if len(dict_match_rubrique.keys()) == 1:
            docs_rubrique = list(set(e.strip() for e in ast.literal_eval(list(dict_match_rubrique.values())[0])))
        else:
            if resultats["operateurs_rubrique"] == "ou":
                docs_rubrique = list(set().union(*(set(e.strip() for e in ast.literal_eval(l)) for l in dict_match_rubrique.values())))
            else:
                docs_rubrique = list(set.intersection(*(set(e.strip() for e in ast.literal_eval(l)) for l in dict_match_rubrique.values())))
        print("docs_rubrique:", docs_rubrique)

        # Fusion avec la liste globale
        if len(docs_cherches) == 0:
            docs_cherches = docs_rubrique
        else:
            docs_cherches = list(set(docs_cherches) & set(docs_rubrique))
    print("doc_cherches post rubrique:", docs_cherches)

    ##############################################################
    # Partie 4 : Gestion des images
    ##############################################################
    image = resultats["images"]
    if image is not None:
        index_image = pd.read_csv(index_inverse_image, sep='\t')
        docs_match_image = ast.literal_eval(index_image.loc[index_image["mot"] == "yes", "docs"].values[0])
        if len(docs_cherches) == 0:
            docs_cherches = docs_match_image
        else:
            docs_cherches = list(set(docs_cherches) & set(docs_match_image))
    print("doc_cherches post images:", docs_cherches)

    ##############################################################
    # Partie 5 : Filtrage par dates
    ##############################################################
    date = resultats["dates"]
    if any(date[k] is not None for k in ["début", "fin", "précis", "not"]):
        index_date = pd.read_csv(index_inverse_date, sep='\t')
        docs_dates = []

        for _, row in index_date.iterrows():
            date_doc_comp = row["mot"]
            if compare_dates(date_doc=date_doc_comp, date_requete=date):
                docs_qui_matchs = ast.literal_eval(row["docs"])
                # Union des résultats valides
                docs_dates = list(set(docs_dates) | set(e.strip() for e in docs_qui_matchs))

        if docs_dates:
            if len(docs_cherches) == 0:
                docs_cherches = docs_dates
            else:
                docs_cherches = list(set(docs_cherches) & set(docs_dates))
    print("doc_cherches post dates:", docs_cherches)

    ##############################################################
    # Partie 6 : Mots-clés exclus ("not")
    ##############################################################
    mot_cles_not = mots_cles["no"]
    if mot_cles_not is not None:
        index_texte = pd.read_csv(index_inverse_texte, sep="\t")
        docs_qui_matchs = ast.literal_eval(index_texte.loc[index_texte["mot"] == mot_cles_not, "docs"].values[0])
        docs_cherches = list(set(docs_cherches) - set(docs_qui_matchs))
    print("doc_cherches post not:", docs_cherches)

    ##############################################################
    # Partie 7 : Résultat final (liste des docs ou des rubriques)
    ##############################################################
    if resultats["return"] != "rubriques":
        return docs_cherches
    else:
        rubriques_cherches = []
        index_rubrique = pd.read_csv(index_inverse_rubrique, sep='\t')
        for _, rubrique in index_rubrique.iterrows():
            for doc in docs_cherches:
                if doc in ast.literal_eval(rubrique["docs"]):
                    rubriques_cherches.append(rubrique["mot"])
        return set(rubriques_cherches)

from td5 import *
from td6 import *

index_inverse_texte = "../TD4/reverse_index_texte.csv"
index_inverse_date = "../TD4/reverse_index_date.csv"
index_inverse_rubrique = "../TD4/reverse_index_rubrique.csv"
index_inverse_titre = "../TD4/reverse_index_titre.csv"
index_inverse_image = "../TD4/reverse_index_image.csv"
lemmes_path = "lemmes_lower.csv"  # Chemin du fichier de lemmes

def traiter_et_rechercher(requete):
    """
    Traite une requête en langage naturel : analyse, correction orthographique,
    puis recherche des documents pertinents.
    
    Args:
        requete (str): La requête en langage naturel saisie par l'utilisateur.
    
    Returns:
        list: Liste des documents pertinents trouvés.
    """
    print("\n########################################################")
    print("Requête initiale :", requete)
    print("########################################################\n")

    # 1. Traitement initial de la requête
    resultat = traiter_requete(requete)

    # 2. Correction orthographique des mots-clés exclus ("no")
    if resultat["mots_cles"]["no"] is not None:
        print("Mot à corriger (exclu) :", resultat["mots_cles"]["no"])
        resultat["mots_cles"]["no"] = correction_orthographique(
            resultat["mots_cles"]["no"],
            lemmes_path
        )

    # 3. Correction orthographique des mots-clés inclus ("yes")
    for i in range(len(resultat["mots_cles"]["yes"])):
        mot = resultat["mots_cles"]["yes"][i]
        print("Mot à corriger (inclus) :", mot)
        resultat["mots_cles"]["yes"][i] = correction_orthographique(
            mot,
            lemmes_path
        )

    # Affichage de la requête corrigée
    print("\nRequête corrigée :")
    print(resultat)
    print("--------------------------------------------------------\n")

    # 4. Recherche des documents pertinents à partir des index inversés
    documents = recherche_documents(
        resultat,
        index_inverse_texte,
        index_inverse_date,
        index_inverse_rubrique,
        index_inverse_titre,
        index_inverse_image
    )

    # 5. Affichage final des résultats
    print("\nDocuments trouvés :")
    print(documents)
    
    return documents

