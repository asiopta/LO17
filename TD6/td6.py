ponctuations = [
    ".", ",", "?"
    ]

articles_fr = [
    "le", "la", "les",        # Définis
    "un", "une", "des",       # Indéfinis
    "du", "de la", "de l’", "des",  # Partitifs
    "l’",                     # Élision
    "au", "aux", "à la", "à l’",  # Contractions avec "à"
    "du", "des", "de la", "de l’",  # Contractions avec "de"
    "de", "d'"
]


#---------------Traitement des images ----------------------
mot_cles_images = [
        "avec des images", "contenant une image", "et qui ont des images"
    ]

def identifie_image(requete, mot_cles_images):
    for mot in mot_cles_images:
        if mot in requete:
            requete = requete.replace(mot, "")
            return requete, True
    return requete, None


mots_cles_requete = [
        "rubriques", "articles", "article", "bulletins", "recherches"
]

#---------------Traitement des valeurs de retour ----------------------
def identifie_return(requete, mots_cles_requete):
    positions = {}
    for mot in mots_cles_requete:
        index = requete.find(mot)
        if index != -1:
            positions[mot] = index

    # Trie les mots par position d'apparition dans la requête
    mot_le_plus_tot = min(positions, key=positions.get)
    requete = requete[positions[mot_le_plus_tot] + len(mot_le_plus_tot):]
    return requete, mot_le_plus_tot

#---------------Traitement des rubriques ----------------------
mots_cles_rubrique = [
         "et", "parlant", "mentionnant", "mais", "qui" #ou fin de phrase
    ]


def identifie_rubrique(requete, mots_cles_rubrique):
    if "rubrique" not in requete:
        return requete, None, None  # "rubrique" absent

    # Position du mot "rubrique"
    start_index = requete.find("rubrique") + len("rubrique ")

    # Texte après "rubrique"
    sous_texte = requete[start_index:]

    # Trouver le mot-clé suivant
    min_index = len(sous_texte)  # valeur maximale par défaut
    for mot in mots_cles_rubrique:
        index = sous_texte.find(mot)
        if index != -1 and index < min_index:
            min_index = index

    resultat = sous_texte[:min_index]
    resultat = resultat.replace("est ", "").replace("'", "")
    if "ou" in resultat:
        resultat = resultat.split(" ou ")
        op_rubrique = "ou"
    else:
        op_rubrique = None

    requete_reste = requete[:start_index - len("rubrique ")] + sous_texte[min_index:]
    
    return requete_reste, resultat, op_rubrique

#---------------Traitement des titres ----------------------
mots_cles_titre = [
        "est", "contient", "évoque", "traite"
    ]

def identifie_titres(requete, mots_cles_titre):
    if "titre" not in requete:
        return requete, None, None  # "titre" absent

    # cas très niche: contenant mot congres dans titre
    if "contenant" in requete and "dans titre" in requete:
        start_index = requete.find("contenant") + len("contenant")
        sous_texte = requete[start_index:]
        min_index = sous_texte.find("dans titre")
        resultat = sous_texte[:min_index]
        resultat = resultat.replace("mot ", "").replace("terme ", "")
        requete_reste = requete[: requete.find("contenant")]
        return requete_reste, resultat, None
    #les autres cas
    else:
        # Position du mot "titre"
        start_index = requete.find("titre") + len("titre ")

        # Texte après "titre"
        sous_texte = requete[start_index:]

        # Ou on arrete de regarder les titres
        min_index = len(sous_texte)  # valeur maximale par défaut
        if " ou " in sous_texte:
            min_index = sous_texte.find("ou")
        resultat = sous_texte[:min_index]
    #requete_reste = requete.replace(resultat, "")

    #sous_texte = partie qui contient le titre. maintenant, il faut le nettoyer et enlever les parties inutiles
    for mot in mots_cles_titre:
        resultat = resultat.replace(mot, "")
    resultat = resultat.replace("mot ", "").replace("terme ", "")

    #vérifier si il y a un "et" dans le titre
    op_titre = None
    if "et" in resultat:
        resultat = resultat.split(" et ")
        op_titre = "et"
    if isinstance(resultat, list):
        for res in resultat:
            res.replace("\n", "").replace("\t", "").replace("  ", " ")
    elif resultat in "    \t  \n":
        resultat = None
    else:
        resultat = resultat.replace("\n", "").replace("\t", "").replace("  ", " ")
 
    requete_reste = requete[:start_index - len("titre ")] + requete[min_index + len(sous_texte):]
    requete_reste = requete_reste.replace("dont", "").replace("dont", "")
    
    return requete_reste, resultat, op_titre


#----------------Traitement des dates ----------------------
def premier_index_result(texte, mots_cles_dates):
    # Cherche l'index de chaque mot-clé dans le texte
    indices = []
    for mot in mots_cles_dates:
        idx = texte.find(mot)
        if idx != -1:
            indices.append(idx)
    # Cherche l'index du premier chiffre
    for i, c in enumerate(texte):
        if c.isdigit():
            indices.append(i)
            break
    if indices:
        ind = min(indices)
        return ind, texte[ind:]
    else:
        return None, texte
    
def last_index_result(texte, fin_dates):
    fin_dates = [
    "évoquant", "sur", "parlant", "portant", "parlent"
    ]
    indices = []
    for mot in fin_dates:
        idx = texte.find(mot)
        if idx != -1:
            indices.append(idx)
    if indices:
        ind = min(indices)
        print(ind, texte[:ind])
        return ind, texte[:ind]
    else:
        return None, texte

def contient_nombre(requete):
    return any(token.isdigit() or "/" in token for token in requete.split())

def clean_date(date_string):
    format_normalise_date = {"j": None, "m": None, "a": None}

    mois = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet",
        "août", "septembre", "octobre", "novembre", "décembre"]
    date_string = date_string.replace("\n", "").replace("\t", "").replace("  ", " ")
    if "/" in date_string:
        date = date_string.split("/")
        format_normalise_date["j"] = date[0].replace(" ", "").replace("\n", "")
        format_normalise_date["m"] = date[1].replace(" ", "").replace("\n", "")
        format_normalise_date["a"] = date[2].replace(" ", "").replace("\n", "")

    else:
        date = date_string.split(" ")
        for date_info in date:
            if date_info.isdigit():
                if len(date_info) == 4:
                    format_normalise_date["a"] = date_info.replace(" ", "").replace("\n", "")
                else:
                    format_normalise_date["j"] = date_info.replace(" ", "").replace("\n", "")
            else:
                if date_info in mois:
                    mois_value = mois.index(date_info) + 1
                    if mois_value < 10:
                        format_normalise_date["m"] = "0" + str(mois_value)
                    else:
                        format_normalise_date["m"] = str(mois_value)

    return format_normalise_date


mots_cles_dates = [
"parus", "publiés" , "datés",
"à partir", "l'année", "écrits", "date", "datent", "mois"
]

mois = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet",
        "août", "septembre", "octobre", "novembre", "décembre"]

fin_dates = [
    "évoquant", "sur", "parlant", "portant", "parlent"
    ]

def identifie_dates(requete, mots_cles_dates):
    resultat = {"début": None, "fin": None, "précis": None, "not": None}
    #vérifier si il y a une date dans la requete
    if not contient_nombre(requete):
        return requete, resultat
    
    #début et fin de partie date
    idx_debut, sous_texte = premier_index_result(requete, mots_cles_dates)
    idx_fin, sous_texte =  last_index_result(sous_texte, fin_dates)
    if idx_debut is None:
        idx_debut = 0
    if idx_fin is None:
        idx_fin = -1
    #clean up requete_reste
    #print(requete[idx_fin:])
    #print(requete[:idx_debut])
    #requete_reste = requete[:idx_debut] + requete[idx_fin:]
    requete_reste = requete.replace(sous_texte, "")

    #clean up sous_texte
    mots_trash = ["qui", "dont", "mais"]
    for mot in mots_trash:
        sous_texte = sous_texte.replace(mot, "")
    
    #3 cas possibles:
    #cas niche: on veut pas une date précise
    if "pas" in sous_texte:
        pas_indx = sous_texte.find("pas") + len("pas")
        not_date = sous_texte[pas_indx:]
        resultat["not"] = clean_date(not_date)
        sous_texte = sous_texte[:pas_indx - len("pas")]

    #cas 1: date entre deux dates
         #parus entre .... et .... / écrits entre .... et .... / publiés entre .... et ....
    if "entre" in sous_texte:
        sous_texte = sous_texte[sous_texte.find("entre") + len("entre"):]
        result_temp = sous_texte.split("et")
        #print(result_temp)
        resultat["début"] = clean_date(result_temp[0])
        resultat["fin"] = clean_date(result_temp[1])


    #cas 2: date à partir d'une date
        #datés à partir de .... / à partir ... / écrits après / date d'après ... / publiés après ...
    elif "à partir" in sous_texte or "après" in sous_texte:
        idx_à_partir = sous_texte.find("à partir")
        idx_apres = sous_texte.find("après")
        if idx_à_partir == -1:
            start_apres = idx_apres + len("après")
        else:
            start_apres = idx_à_partir + len("à partir")
            
        resultat["début"] = clean_date(sous_texte[start_apres:])

    #cas 3: date précise (utiliser else)
        #directement date / publiés mois ... /
    else:
        resultat["précis"] = clean_date(sous_texte)

    
    return requete_reste, resultat


#----------------Traitement des mots clés ----------------------*

def contains_letter(s):
    return any(c.isalpha() for c in s)

mots_cles_articles = [
    "liés à", "domaine", "impliquant", "parlent",  "sur", "traitant", 
    "évoquant", "parlant", 
    "mentionnant", "portant", "portent",   "mots", "mot", "parle",
    "à propos", "évoquent",  "mentionnent"
]

niche = "cité"

trash_words = ["est-il", "qui ", "ville", "d'", "l'", "dans", "  ", "\n",
                "  ", ",", "mais", "ont été", "ont pour", "provenant", "dont"]
stop_word = ["et", "en", "soit"]

def clean_up(mot_cle):
    mot_cle = mot_cle.replace("\n", "").replace("\t", "")
    return mot_cle

def identifie_mots_cles(requete, mots_cles_articles):
    resultat = {"yes": [], "no": None}
    op_mots_cles = None

    if not contains_letter(requete):
        return resultat, None
    #enlever les mots inutiles
    for word in trash_words:
        requete = requete.replace(word, "")
    #requete = requete.replace(" en ", " ")
    
    #identifier les mots clés non voulues
    if "pas" in requete:
        pas_indx = requete.find("pas") + len("pas")
        not_mots_cles = requete[pas_indx:]
        resultat["no"] = not_mots_cles
        requete = requete[:pas_indx - len("pas")]
    #cas niche
    if niche in requete:
        resultat["yes"] = requete.replace(niche, "").replace("est-il", "").replace("qui", "")
        return resultat, None
    #sinon
    for mot in mots_cles_articles:
        if mot in requete:
            requete = requete[requete.find(mot) + len(mot):]

    if "ou " in requete or "soit" in requete:
        op_mots_cles = "ou"
        if "soit" in requete:
            sous_text = requete.split("soit")
        else:
            sous_text = requete.split("ou ")
        for i in range(len(sous_text)):
            sous_text[i] = clean_up(sous_text[i])
            if sous_text[i] != " " and sous_text[i] != "\n" and sous_text[i] != "" and sous_text[i] != "  ":
                resultat["yes"].append(sous_text[i])
    elif "et " in requete:
        sous_text = requete.split(" et")
        for i in range(len(sous_text)):
            sous_text[i] = clean_up(sous_text[i])
            if sous_text[i] != " " and sous_text[i] != "\n" and sous_text[i] != "" and sous_text[i] != "  ":
                resultat["yes"].append(sous_text[i])
    elif " en " in requete:
        sous_text = requete.split("en")
        for i in range(len(sous_text)):
            sous_text[i] = clean_up(sous_text[i])
            if sous_text[i] != " " and sous_text[i] != "\n" and sous_text[i] != "" and sous_text[i] != "  ":
                resultat["yes"].append(sous_text[i])
    else:
        resultat["yes"].append(requete.replace(" et", "").replace("»", "").replace("«", ""))

    return resultat, op_mots_cles

#----------------Fonction qui regroupe tout----------------------

def traiter_requete(requete):   
    # suppression des articles et ponctuations inutiless
    requete = requete.lower()
    requete = requete.replace("?", "").replace(".", "").replace("’", "'")
    # Structure pour stocker les composants de la requête
    resultats = {
        "return": None,
        "mots_cles": {"yes": [], "no": None},
        "operateurs_mots_cles": None,
        "rubrique": None,
        "operateurs_rubrique"
        "dates": {"debut": None, "fin": None, "précis": None, "not": None},
        "titre": None,
        "operateurs_titre": None,
        "images": None,

    }
    # Extraction des mots-clés
    requete, resultats["return"] = identifie_return(requete, mots_cles_requete)
    requete, resultats["images"] = identifie_image(requete, mot_cles_images)
    requete, resultats["rubrique"], op_rubrique = identifie_rubrique(requete, mots_cles_rubrique)
    if op_rubrique:
        resultats["operateurs_rubrique"] = op_rubrique
    
    #enlever les articles pour faciliter le traitement des mots clés
    for article in articles_fr:
        requete = requete.replace(" " + article + " ", " ")

    #Extraction des titres
    requete, resultats["titre"], op_titre = identifie_titres(requete, mots_cles_titre)
    if op_titre:
        resultats["operateurs_titre"] = op_titre
    
    # Extraction des dates (formats simples)
    requete, resultats["dates"] = identifie_dates(requete, mots_cles_dates)
    resultats["mots_cles"], op_mot_cle = identifie_mots_cles(requete, mots_cles_articles)
    if op_mot_cle:
        resultats["operateurs_mots_cles"] = op_mot_cle

    return resultats


#------------------Main----------------------
if __name__ == "__main__":
    requete = input("Entrez votre requête en langage naturel : ")
    resultat = traiter_requete(requete)
    print("Représentation structurée de la requête :")
    print(resultat)