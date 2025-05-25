import numpy as np

def recherche_proximite(m1, m2, seuilMin = 3, seuilMax = 4):
    l1 = len(m1)
    l2 = len(m2)
    if (l1< seuilMin) or (l2<seuilMin):
        return 0
    elif abs(l1- l2) > seuilMax :
        return 0
    else :
        i = 0
        while (i < min(l1, l2)) and (m1[i] == m2[i]):
            i += 1
        return 100*i/max(l1, l2)
    
def levenshtein(word, mots_candidats):
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

        # Remplissage
        for i in range(1, lw + 1):
            for j in range(1, lc + 1):
                if word[i - 1] == candidate[j - 1]:
                    cost = 0
                else:
                    cost = 1
                dist[i][j] = min(dist[i - 1][j] + 1,     # suppression
                                 dist[i][j - 1] + 1,     # insertion
                                 dist[i - 1][j - 1] + cost)  # substitution

        if dist[lw][lc] < best_dist:
            best_dist = dist[lw][lc]
            best_mot = candidate

    return best_mot


import pandas as pd
def lemmatize(lemmes_path):
    lemmes = pd.read_csv(lemmes_path, sep="\t")

    phrase: str = input("Ecrivez une phrase: ")
    phrase = phrase.lower()
    words = phrase.split()
    print(words)
    for word in words:
        if word in lemmes["mot"].values:
            lemme = lemmes.loc[lemmes["mot"] == word, "lemme"].values[0]
            phrase = phrase.replace(word, lemme)
        else: 
            mots_candidats = []
            for mot in lemmes["mot"]:
                dist = recherche_proximite(word, mot, 3, 4)
                if dist != 0:
                    mots_candidats.append(mot)
            if len(mots_candidats) == 0:
                print("no lemma found for: ", word)
            else:
                mot_result = levenshtein(word ,mots_candidats)
                lemme = lemmes.loc[lemmes["mot"] == mot_result, "lemme"].values[0]
                phrase = phrase.replace(word, str(lemme))
    return phrase

import pandas as pd
def lemmatize_corpus(lemmes_path):
    lemmes = pd.read_csv(lemmes_path, sep="\t")

    phrase: str = input("Ecrivez une phrase: ")
    phrase = phrase.lower()
    words = phrase.split()
    print(words)
    for word in words:
        if word in lemmes["mot"].values:
            lemme = lemmes.loc[lemmes["mot"] == word, "lemme"].values[0]
            phrase = phrase.replace(word, lemme)
        else: 
            mots_candidats = []
            for mot in lemmes["mot"]:
                dist = recherche_proximite(word, mot, 3, 4)
                if dist != 0:
                    mots_candidats.append(mot)
            if len(mots_candidats) == 0:
                print("no lemma found for: ", word)
            else:
                mot_result = levenshtein(word ,mots_candidats)
                lemme = lemmes.loc[lemmes["mot"] == mot_result, "lemme"].values[0]
                phrase = phrase.replace(word, str(lemme))
    return phrase

def correction_orthographique(mot, lemmes_path):
    lemmes = pd.read_csv(lemmes_path, sep="\t")
    mot = mot.lower()
    if mot in lemmes["mot"].values:
            lemme = lemmes.loc[lemmes["mot"] == mot, "lemme"].values[0]
    else: 
            mots_candidats = []
            for lemme in lemmes["mot"]:
                dist = recherche_proximite(mot, lemme, 3, 4)
                if dist != 0:
                    mots_candidats.append(lemme)
            if len(mots_candidats) == 0:
                print("no lemma found for: ", mot)
            else:
                mot_result = levenshtein(mot ,mots_candidats)
                lemme = lemmes.loc[lemmes["mot"] == mot_result, "lemme"].values[0]
    return str(lemme)