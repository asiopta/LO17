import numpy as np
import pandas as pd

# -----------------------------------------------------
# Mesure de similarité de surface entre deux mots
# -----------------------------------------------------
def recherche_proximite(m1, m2, seuilMin=3, seuilMax=4):
    """
    Évalue la proximité entre deux mots m1 et m2 en utilisant une mesure simple de préfixe commun.
    Retourne un score proportionnel à la longueur du préfixe commun.
    """
    l1 = len(m1)
    l2 = len(m2)
    if (l1 < seuilMin) or (l2 < seuilMin):
        return 0
    elif abs(l1 - l2) > seuilMax:
        return 0
    else:
        i = 0
        while (i < min(l1, l2)) and (m1[i] == m2[i]):
            i += 1
        return 100 * i / max(l1, l2)

# -----------------------------------------------------
# Calcule la distance de Levenshtein (édition) entre un mot et une liste de candidats
# -----------------------------------------------------
def levenshtein(word, mots_candidats):
    """
    Trouve le mot le plus proche de 'word' dans la liste 'mots_candidats'
    en utilisant la distance de Levenshtein (édition).
    """
    best_dist = float('inf')
    best_mot = ""
    lw = len(word)

    for candidate in mots_candidats:
        lc = len(candidate)
        dist = np.zeros((lw + 1, lc + 1), dtype=int)

        # Initialisation
        for i in range(lw + 1):
            dist[i][0] = i
        for j in range(lc + 1):
            dist[0][j] = j

        # Calcul de la distance
        for i in range(1, lw + 1):
            for j in range(1, lc + 1):
                cost = 0 if word[i - 1] == candidate[j - 1] else 1
                dist[i][j] = min(
                    dist[i - 1][j] + 1,        # Suppression
                    dist[i][j - 1] + 1,        # Insertion
                    dist[i - 1][j - 1] + cost  # Substitution
                )

        # Choix du mot avec la plus petite distance
        if dist[lw][lc] < best_dist:
            best_dist = dist[lw][lc]
            best_mot = candidate

    return best_mot

# -----------------------------------------------------
# Lemmatise une phrase entrée par l'utilisateur
# -----------------------------------------------------
def lemmatize(lemmes_path):
    lemmes = pd.read_csv(lemmes_path, sep="\t")
    phrase = input("Écrivez une phrase: ").lower()
    words = phrase.split()
    print(words)

    for word in words:
        if word in lemmes["mot"].values:
            lemme = lemmes.loc[lemmes["mot"] == word, "lemme"].values[0]
            phrase = phrase.replace(word, lemme)
        else:
            mots_candidats = [mot for mot in lemmes["mot"] if recherche_proximite(word, mot) != 0]
            if not mots_candidats:
                print("no lemma found for:", word)
            else:
                mot_result = levenshtein(word, mots_candidats)
                lemme = lemmes.loc[lemmes["mot"] == mot_result, "lemme"].values[0]
                phrase = phrase.replace(word, str(lemme))
    return phrase

# -----------------------------------------------------
# Même fonction que lemmatize (doublon possible à fusionner)
# -----------------------------------------------------
def lemmatize_corpus(lemmes_path):
    lemmes = pd.read_csv(lemmes_path, sep="\t")
    phrase = input("Écrivez une phrase: ").lower()
    words = phrase.split()
    print(words)

    for word in words:
        if word in lemmes["mot"].values:
            lemme = lemmes.loc[lemmes["mot"] == word, "lemme"].values[0]
            phrase = phrase.replace(word, lemme)
        else:
            mots_candidats = [mot for mot in lemmes["mot"] if recherche_proximite(word, mot) != 0]
            if not mots_candidats:
                print("no lemma found for:", word)
            else:
                mot_result = levenshtein(word, mots_candidats)
                lemme = lemmes.loc[lemmes["mot"] == mot_result, "lemme"].values[0]
                phrase = phrase.replace(word, str(lemme))
    return phrase

# -----------------------------------------------------
# Correction orthographique pour un seul mot
# -----------------------------------------------------
def correction_orthographique(mot, lemmes_path):
    lemmes = pd.read_csv(lemmes_path, sep="\t")
    mot = mot.lower()
    if mot in lemmes["mot"].values:
        lemme = lemmes.loc[lemmes["mot"] == mot, "lemme"].values[0]
    else:
        mots_candidats = [lemme for lemme in lemmes["mot"] if recherche_proximite(mot, lemme) != 0]
        if not mots_candidats:
            print("no lemma found for:", mot)
            lemme = mot  # Par défaut, on garde le mot si aucun candidat n'est trouvé
        else:
            mot_result = levenshtein(mot, mots_candidats)
            lemme = lemmes.loc[lemmes["mot"] == mot_result, "lemme"].values[0]
    return str(lemme)
