import string

def nettoyer_texte(texte: str) -> str:
    """
    Nettoie un texte en enlevant la ponctuation et en mettant tous les caractères en minuscules.

    :param texte: Le texte à nettoyer.
    :return: Le texte nettoyé sans ponctuation et en minuscules.
    """
    ponctuation = string.punctuation
    for p in ponctuation:
        texte = texte.replace(p, "")
    return texte.lower()



def segmente(fichier, output):
    with open(output, "a", encoding="utf-8") as f_w:
        f_w.write("mot" + "\t" + "doc_id\n")
        with open(fichier, "r", encoding="utf-8") as f:
            doc_id = 0
            for ligne in f.readlines():
                if "<fichier>" in ligne:
                    doc_id = ligne[9:14]
                if "<texte>" in ligne:
                    texte = str(ligne)
                    texte = texte.replace("<texte>", "")
                    texte = texte.replace("</texte>", "")
                    texte_propre = nettoyer_texte(texte)
                    mots = texte_propre.split()
                    #print(mots)
                    for mot in mots:
                        to_write = mot + "\t" + doc_id + "\n"
                        f_w.write(to_write)




if __name__ == "__main__":
    segmente("C:/Users/ntich/OneDrive/Desktop/school shit/LO17/TD2/corpus.XML", "C:/Users/ntich/OneDrive/Desktop/school shit/LO17/TD3/tokens.csv")