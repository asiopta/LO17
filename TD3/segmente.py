import string

# ------------------------------------------------------
def nettoyer_texte(texte: str) -> str:
    """
    Nettoie un texte en enlevant la ponctuation et en mettant tous les caractères en minuscules.

    :param texte: Le texte à nettoyer.
    :return: Le texte nettoyé sans ponctuation et en minuscules.
    """
    ponctuation = string.punctuation
    # Supprime chaque caractère de ponctuation
    for p in ponctuation:
        texte = texte.replace(p, "")
    return texte.lower()

# ------------------------------------------------------
def segmente(fichier, output):
    """
    Découpe le contenu d'un fichier XML en tokens (mots) 
    et les enregistre dans un fichier de sortie (un mot par ligne avec son doc_id).

    :param fichier: Chemin du fichier XML à traiter.
    :param output: Chemin du fichier de sortie pour les tokens.
    """
    # Ouvre le fichier de sortie en mode ajout
    with open(output, "a", encoding="utf-8") as f_w:
        # Écrit l'en-tête
        f_w.write("mot" + "\t" + "doc_id\n")
        
        # Ouvre le fichier XML à lire
        with open(fichier, "r", encoding="utf-8") as f:
            doc_id = 0  # Variable pour stocker le doc_id courant
            for ligne in f.readlines():
                # Récupère l'ID du fichier
                if "<fichier>" in ligne:
                    doc_id = ligne[9:14]  # Extraire l'ID du fichier (entre balises)
                
                # Si on est sur une ligne de texte, on la nettoie et on segmente
                if "<texte>" in ligne:
                    # Supprime les balises XML
                    texte = ligne.replace("<texte>", "").replace("</texte>", "")
                    # Nettoie le texte (ponctuation + minuscules)
                    texte_propre = nettoyer_texte(texte)
                    # Découpe en mots
                    mots = texte_propre.split()
                    
                    # Écrit chaque mot avec le doc_id
                    for mot in mots:
                        to_write = mot + "\t" + doc_id + "\n"
                        f_w.write(to_write)

# ------------------------------------------------------
if __name__ == "__main__":
    segmente("../TD2/corpus.XML", "tokens.csv")
