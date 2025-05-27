from TD7 import *
import time
import pandas as pd

import matplotlib.pyplot as plt

def get_precision_recall(docs_predits, docs_pertinents):
    """
    Calcule la précision et le rappel pour une requête.
    """
    docs_predits_set = set(docs_predits)
    docs_pertinents_set = set(docs_pertinents)
    docs_pertinents_recuperes = docs_predits_set & docs_pertinents_set


    if not docs_predits_set and not docs_pertinents_set:
        precision = 1.0
        recall = 1.0
    elif not docs_predits_set and docs_pertinents_set:
        precision = 1.0
        recall = 0.0
    elif docs_predits_set and not docs_pertinents_set:
        precision = 0.0
        recall = 1.0
    else:
        precision = len(docs_pertinents_recuperes) / len(docs_predits_set)
        recall = len(docs_pertinents_recuperes) / len(docs_pertinents_set)

    return precision, recall

def get_all_precisions_recalls(requetes_10, docs_pertinents_manuel):
    """
    Pour chaque requête, calcule la précision et le rappel.
    """
    precisions = []
    rappels = []
    for req, docs_pert in zip(requetes_10, docs_pertinents_manuel):
        docs_predits = traiter_et_rechercher(req)
        precision, rappel = get_precision_recall(docs_predits, docs_pert)
        precisions.append(precision)
        rappels.append(rappel)
    return precisions, rappels

def measure_average_time(requetes_10, n=100):
    """
    Mesure le temps de réponse moyen du moteur sur n exécutions.
    """
    start = time.time()
    for _ in range(n):
        for req in requetes_10:
            traiter_et_rechercher(req)
    end = time.time()
    avg_time = (end - start) / (n * len(requetes_10))
    return avg_time

def display_results_table(requetes_10, precisions, rappels):
    """
    Affiche les résultats sous forme de tableau, avec F1-score.
    """
    f1_scores = []
    for p, r in zip(precisions, rappels):
        if p + r == 0:
            f1 = 0.0
        else:
            f1 = 2 * p * r / (p + r)
        f1_scores.append(f1)
    df = pd.DataFrame({
        'Requête': requetes_10,
        'Précision': precisions,
        'Rappel': rappels,
        'F1-score': f1_scores
    })
    print(df)
    return df, f1_scores

def plot_precision_recall_f1(precisions, rappels, f1_scores):
    """
    Affiche les mesures sous forme de graphiques.
    """
    plt.figure(figsize=(8, 5))
    plt.plot(precisions, label='Précision', marker='o')
    plt.plot(rappels, label='Rappel', marker='x')
    plt.plot(f1_scores, label='F1-score', marker='s')
    plt.xlabel('Numéro de requête')
    plt.ylabel('Score')
    plt.title('Précision, rappel et F1-score par requête')
    plt.legend()
    plt.grid(True)
    plt.show()

def calculate_precision_rappel(requetes_10: list[str], docs_pertinents_manuel: list[list[str]]):
    '''
    fonction qui à partir de requetes_10, 10 requetes choisies, utilise traiter_et_rechercher pour obtenir les
    documents correspondants à la requete, puis compare ces documents à la liste des documents pertinents manuellement
    fournie.
    Cette fonction calcule donc pour chaque requete la précision, le rappel, et F-1 score.
    Elle mesure également le temps de réponse moyen du moteur sur 100 exécutions.
    Finalement, elle présente les mesures sous forme de tableaux et de graphiques.
    '''
    precisions, rappels = get_all_precisions_recalls(requetes_10, docs_pertinents_manuel)
    avg_time = measure_average_time(requetes_10, n=100)
    df, f1_scores = display_results_table(requetes_10, precisions, rappels)
    print(f"Temps de réponse moyen sur 100 exécutions : {avg_time:.4f} secondes")
    plot_precision_recall_f1(precisions, rappels, f1_scores)
    return df, precisions, rappels, f1_scores, avg_time

'''
pour récupérer 'manuellement' les documents pertinents, je regarde index inversés du td4 avec ctrl+F et je cherche le mots clés voulu
ou bien la rubrique voulue, etc...
Puis, je veille à bien effectuer manuellement les opérations entre les documents récupérés à chaque fois.
    Cela veut dire, faire correctement union lorsqu'il s'agit de "ou" et intersection sinon

Pour les dates, j'ai bien essayé à regarder tous les cas possibles (à partir de date X ou date entre X et Y)
et faire un union de tous les documents dont les dates correspondent aux contraintes.

Une approche plus correcte, que j'ai appliqué pour quelques requetes comme la 3eme où je pensais que mes résultats allaient étre faux
puisqu'on cherche un bimot 'réalité virtuelle' et non pas les deux mots séparés, je suis allé chercher directement dans le corpus avec un 
ctrl+F. Cette approche me semble plus sur et correcte pour avoir des résultats manuels fiables, mais elle consomme beaucoup de temps 
sur d'autres requetes. Donc, je l'ai malheureusement pas appliqué partout
'''

requetes_choisies = ["Je veux les articles de la rubrique Focus parlant d’innovation.",
                    "Je souhaite les rubriques des articles parlant de nutrition ou de vins.",
                    "Quels sont les articles sur la réalité virtuelle?",
                    "Je voudrais les articles qui parlent d’airbus ou du projet Taxibot.",
                    "Je cherche les recherches sur l’aéronautique.",
                    "Article traitant des Serious Game et de la réalité virtuelle.",
                    "Je voudrais tous les bulletins écrits entre 2012 et 2013 mais pas au mois de juin.",
                    "Quels sont les articles dont le titre contient le terme 'marché' et le mot 'projet'?",
                    "je voudrais les articles dont le titre contient le mot 3D.",
                    "je veux voir les articles de la rubrique Focus et publiés entre 30/08/2011 et 29/09/2011."
                     ]
resultats_manuels_requetes = [
    ['75457', '71359', '67795', '74167', '73876', '68383', '72933', '67068', '75790', '68273', '72392', '76507', '68882', '68276', '69533', '75065', '72113', '70162', '74744', '75789', '68274', '67938', '73182', '67383'], # requete 1
    ['du côté pôles', 'focus', 'au coeur régions', 'actualité innovation', 'actualités innovations', 'evénement'], #requete 2
    ['75064'], #requete 3
    ['70920', '72933', '71617', '72636'], #requete 4
    ['68888', '71840', '73687', '72636', '68392', '68280', '76207', '74167', '71358', '68393', '72113', '73884', '70914', '75792', '68383', '67068', '73879', '75066', '76510', '74745', '68642', '71615'], #requete 5
    [], #requete 6
    ['70922', '73437', '70743', '71618', '74171', '68889', '74172', '70915', '73876', '70918', '71845', '71835', '73875', '73877', '69811', '72392', '73683', '74175', '70167', '70161', '71840', '74752', '70920', '70923', '70749', '72400', '71839', '72114', '72630', '73434', '74173', '72113', '74452', '72940', '69819', '73690', '72938', '72634', '69812', '73432', '70164', '72396', '69182', '69540', '71616', '71836', '71837', '69539', '72118', '72394', '73684', '70752', '71838', '73686', '70169', '72939', '69537', '70746', '70170', '71841', '72401', '70753', '74749', '72120', '70747', '73882', '74174', '72631', '70751', '74176', '71357', '72632', '71842', '71358', '72932', '69184', '70921', '74451', '74449', '71843', '73438', '69541', '68886', '73878', '73431', '72635', '68888', '74746', '74168', '71619', '69536', '71617', '72636', '71366', '74454', '72395', '70916', '69820', '71359', '74456', '74750', '69816', '70165', '72116', '71614', '74457', '72933', '68884', '69542', '70168', '72936', '69817', '74747', '70163', '74745', '72937', '69185', '69180', '72121', '72393', '70166', '68887', '72122', '71612', '71360', '69533', '70919', '69538', '68883', '73884', '71363', '71362', '69815', '74455', '73436', '72119', '74751', '72115', '70744', '73880', '72397', '70745', '72637', '72398', '74167', '69181', '74450', '72399', '69177', '74170', '73433', '73879', '69821', '72934', '73688', '71621', '72633', '69534', '73689', '69813', '71615', '72935', '68882', '73687', '69535', '72117', '74169', '73685', '74748', '69814', '71361', '69543', '69178', '72629', '71620', '70914', '73435', '73881', '69179', '70917', '70162', '74744', '73883', '69186', '68885', '69183', '73430', '68881', '73691', '69818', '70748', '74453'], #requete 7
    ['72634', '72392'], #requete 8
    ['67554', '72635', '73431'], #requete 9
    ['67794', '67795', '67553', '67554', '67555'] #requete 10



]

calculate_precision_rappel(requetes_choisies, resultats_manuels_requetes)


"""
résultats: 
Requête  Précision    Rappel  \
0  Je veux les articles de la rubrique Focus parl...   1.000000  1.000000   
1  Je souhaite les rubriques des articles parlant...   1.000000  1.000000   
2  Quels sont les articles sur la réalité virtuelle?   1.000000  0.000000   
3  Je voudrais les articles qui parlent d’airbus ...   0.042553  1.000000   
4      Je cherche les recherches sur l’aéronautique.   1.000000  1.000000   
5  Article traitant des Serious Game et de la réa...   1.000000  1.000000   
6  Je voudrais tous les bulletins écrits entre 20...   1.000000  0.046875   
7  Quels sont les articles dont le titre contient...   1.000000  0.500000   
8  je voudrais les articles dont le titre contien...   1.000000  1.000000   
9  je veux voir les articles de la rubrique Focus...   1.000000  0.400000   

   F1-score  
0  1.000000  
1  1.000000  
2  0.000000  
3  0.081633  
4  1.000000  
5  1.000000  
6  0.089552  
7  0.666667  
8  1.000000  
9  0.571429  

Temps de réponse moyen sur 100 exécutions : 0.1773 secondes

"""
