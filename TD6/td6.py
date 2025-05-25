# -------------------- PONCTUATIONS ET ARTICLES --------------------
ponctuations = [".", ",", "?"]

articles_fr = [
    "le", "la", "les", "un", "une", "des",  # Définis et indéfinis
    "du", "de la", "de l’", "l’",
    "au", "aux", "à la", "à l’",
    "de", "d'"
]

# -------------------- MOTS CLÉS SPÉCIFIQUES --------------------
mot_cles_images = [
    "avec des images", "contenant une image", "et qui ont des images"
]

mots_cles_requete = [
    "rubriques", "articles", "article", "bulletins", "recherches"
]

mots_cles_rubrique = [
    "et", "parlant", "mentionnant", "mais", "qui"
]

mots_cles_titre = [
    "est", "contient", "évoque", "traite"
]

mots_cles_dates = [
    "parus", "publiés", "datés", "à partir", "l'année",
    "écrits", "date", "datent", "mois"
]

mois = [
    "janvier", "février", "mars", "avril", "mai", "juin", "juillet",
    "août", "septembre", "octobre", "novembre", "décembre"
]

fin_dates = [
    "évoquant", "sur", "parlant", "portant", "parlent"
]

mots_cles_articles = [
    "liés à", "domaine", "impliquant", "parlent", "sur", "traitant",
    "évoquant", "mentionnant", "portant", "mots", "mot", "parle",
    "à propos", "évoquent", "mentionnent"
]

niche = "cité"
trash_words = ["est-il", "qui ", "ville", "d'", "l'", "dans", "  ", "\n",
                ",", "mais", "ont été", "ont pour", "provenant", "dont"]
stop_word = ["et", "en", "soit"]

# -------------------- TRAITEMENT DES IMAGES --------------------
def identifie_image(requete, mot_cles_images):
    for mot in mot_cles_images:
        if mot in requete:
            return requete.replace(mot, ""), True
    return requete, None

# -------------------- TRAITEMENT DE LA VALEUR DE RETOUR --------------------
def identifie_return(requete, mots_cles_requete):
    positions = {mot: requete.find(mot) for mot in mots_cles_requete if requete.find(mot) != -1}
    mot_le_plus_tot = min(positions, key=positions.get)
    requete = requete[positions[mot_le_plus_tot] + len(mot_le_plus_tot):]
    return requete, mot_le_plus_tot

# -------------------- TRAITEMENT DES RUBRIQUES --------------------
def identifie_rubrique(requete, mots_cles_rubrique):
    if "rubrique" not in requete:
        return requete, None, None

    start_index = requete.find("rubrique") + len("rubrique ")
    sous_texte = requete[start_index:]

    min_index = len(sous_texte)
    for mot in mots_cles_rubrique:
        index = sous_texte.find(mot)
        if index != -1 and index < min_index:
            min_index = index

    resultat = sous_texte[:min_index].replace("est ", "").replace("'", "")
    op_rubrique = "ou" if "ou" in resultat else None
    resultat = resultat.split(" ou ") if op_rubrique else resultat

    requete_reste = requete[:start_index - len("rubrique ")] + sous_texte[min_index:]
    return requete_reste, resultat, op_rubrique

# -------------------- TRAITEMENT DES TITRES --------------------
def identifie_titres(requete, mots_cles_titre):
    if "titre" not in requete:
        return requete, None, None

    if "contenant" in requete and "dans titre" in requete:
        start_index = requete.find("contenant") + len("contenant")
        sous_texte = requete[start_index:]
        min_index = sous_texte.find("dans titre")
        resultat = sous_texte[:min_index].replace("mot ", "").replace("terme ", "")
        return requete[:requete.find("contenant")], resultat, None

    start_index = requete.find("titre") + len("titre ")
    sous_texte = requete[start_index:]

    min_index = sous_texte.find("ou") if " ou " in sous_texte else len(sous_texte)
    resultat = sous_texte[:min_index]
    for mot in mots_cles_titre:
        resultat = resultat.replace(mot, "")
    resultat = resultat.replace("mot ", "").replace("terme ", "").strip()

    op_titre = "et" if "et" in resultat else None
    resultat = resultat.split(" et ") if op_titre else resultat

    requete_reste = requete[:start_index - len("titre ")] + requete[min_index + len(sous_texte):]
    return requete_reste.replace("dont", ""), resultat, op_titre

# -------------------- TRAITEMENT DES DATES --------------------
def premier_index_result(texte, mots_cles_dates):
    indices = [texte.find(mot) for mot in mots_cles_dates if texte.find(mot) != -1]
    indices += [i for i, c in enumerate(texte) if c.isdigit()]
    if indices:
        ind = min(indices)
        return ind, texte[ind:]
    return None, texte

def last_index_result(texte, fin_dates):
    indices = [texte.find(mot) for mot in fin_dates if texte.find(mot) != -1]
    if indices:
        ind = min(indices)
        return ind, texte[:ind]
    return None, texte

def contient_nombre(requete):
    return any(token.isdigit() or "/" in token for token in requete.split())

def clean_date(date_string):
    format_normalise_date = {"j": None, "m": None, "a": None}
    date_string = date_string.replace("\n", "").replace("\t", "").strip()
    if "/" in date_string:
        date = date_string.split("/")
        format_normalise_date["j"], format_normalise_date["m"], format_normalise_date["a"] = date
    else:
        for date_info in date_string.split(" "):
            if date_info.isdigit():
                format_normalise_date["a"] = date_info if len(date_info) == 4 else format_normalise_date["j"]
            elif date_info in mois:
                mois_value = mois.index(date_info) + 1
                format_normalise_date["m"] = f"{mois_value:02d}"
    return format_normalise_date

def identifie_dates(requete, mots_cles_dates):
    resultat = {"début": None, "fin": None, "précis": None, "not": None}
    if not contient_nombre(requete):
        return requete, resultat

    idx_debut, sous_texte = premier_index_result(requete, mots_cles_dates)
    idx_fin, sous_texte = last_index_result(sous_texte, fin_dates)

    requete_reste = requete.replace(sous_texte, "")
    for mot in ["qui", "dont", "mais"]:
        sous_texte = sous_texte.replace(mot, "")

    if "pas" in sous_texte:
        pas_indx = sous_texte.find("pas") + len("pas")
        not_date = sous_texte[pas_indx:]
        resultat["not"] = clean_date(not_date)
        sous_texte = sous_texte[:pas_indx - len("pas")]
    if "entre" in sous_texte:
        sous_texte = sous_texte.split("entre")[1]
        debut, fin = sous_texte.split("et")
        resultat["début"] = clean_date(debut)
        resultat["fin"] = clean_date(fin)
    elif "à partir" in sous_texte or "après" in sous_texte:
        start_apres = sous_texte.find("après") + len("après") if "après" in sous_texte else sous_texte.find("à partir") + len("à partir")
        resultat["début"] = clean_date(sous_texte[start_apres:])
    else:
        resultat["précis"] = clean_date(sous_texte)

    return requete_reste, resultat

# -------------------- TRAITEMENT DES MOTS CLÉS --------------------
def contains_letter(s):
    return any(c.isalpha() for c in s)

def clean_up(mot_cle):
    return mot_cle.replace("\n", "").replace("\t", "").strip()

def identifie_mots_cles(requete, mots_cles_articles):
    resultat = {"yes": [], "no": None}
    op_mots_cles = None

    if not contains_letter(requete):
        return resultat, None

    for word in trash_words:
        requete = requete.replace(word, "")

    if "pas" in requete:
        pas_indx = requete.find("pas") + len("pas")
        resultat["no"] = requete[pas_indx:]
        requete = requete[:pas_indx - len("pas")]

    if niche in requete:
        resultat["yes"] = requete.replace(niche, "").split()
        return resultat, None

    for mot in mots_cles_articles:
        if mot in requete:
            requete = requete[requete.find(mot) + len(mot):]

    if "ou " in requete or "soit" in requete:
        op_mots_cles = "ou"
        sous_text = requete.split("soit" if "soit" in requete else "ou ")
        resultat["yes"] = [clean_up(st) for st in sous_text if clean_up(st)]
    elif "et " in requete:
        sous_text = requete.split(" et")
        resultat["yes"] = [clean_up(st) for st in sous_text if clean_up(st)]
    elif " en " in requete:
        sous_text = requete.split("en")
        resultat["yes"] = [clean_up(st) for st in sous_text if clean_up(st)]
    else:
        resultat["yes"].append(requete.strip())

    return resultat, op_mots_cles

# -------------------- FONCTION GLOBALE --------------------
def traiter_requete(requete):
    requete = requete.lower().replace("?", "").replace(".", "").replace("’", "'")
    resultats = {
        "return": None,
        "mots_cles": {"yes": [], "no": None},
        "operateurs_mots_cles": None,
        "rubrique": None,
        "operateurs_rubrique": None,
        "dates": {"début": None, "fin": None, "précis": None, "not": None},
        "titre": None,
        "operateurs_titre": None,
        "images": None
    }

    requete, resultats["return"] = identifie_return(requete, mots_cles_requete)
    requete, resultats["images"] = identifie_image(requete, mot_cles_images)
    requete, resultats["rubrique"], op_rubrique = identifie_rubrique(requete, mots_cles_rubrique)
    if op_rubrique:
        resultats["operateurs_rubrique"] = op_rubrique

    for article in articles_fr:
        requete = requete.replace(" " + article + " ", " ")

    requete, resultats["titre"], op_titre = identifie_titres(requete, mots_cles_titre)
    if op_titre:
        resultats["operateurs_titre"] = op_titre

    requete, resultats["dates"] = identifie_dates(requete, mots_cles_dates)
    resultats["mots_cles"], op_mot_cle = identifie_mots_cles(requete, mots_cles_articles)
    if op_mot_cle:
        resultats["operateurs_mots_cles"] = op_mot_cle

    return resultats

# -------------------- MAIN --------------------
if __name__ == "__main__":
    requete = input("Entrez votre requête en langage naturel : ")
    resultat = traiter_requete(requete)
    print("requete: ", requete)
    print("-----------------------------------")
    print("Représentation structurée de la requête :")
    print(resultat)
    print("------------------------------------")
