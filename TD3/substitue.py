import pandas as pd

# ------------------------------------------------------
def substitue(texte, replacables, output):
    """
    Remplace chaque mot du fichier texte par son remplaçant défini dans un fichier CSV.
    Écrit le texte modifié dans un fichier de sortie.

    :param texte: Chemin du fichier texte à traiter.
    :param replacables: Fichier CSV contenant les remplacements (mot -> remplaçant).
    :param output: Chemin du fichier de sortie.
    """
    # Lecture du fichier CSV des remplacements
    df = pd.read_csv(replacables, sep="\t")
    
    # Ouvre le fichier de sortie en mode ajout
    with open(output, "a", encoding="utf-8") as f_w:
        # Ouvre le fichier texte à lire
        with open(texte, "r", encoding="utf-8") as f_r:
            # Parcours des lignes du fichier texte
            for ligne in f_r.readlines():
                mots = ligne.strip().split()  # Découpe en mots
                
                for mot in mots:
                    # Recherche du mot dans le fichier de remplacements
                    match = df[df.iloc[:, 0] == mot]
                    
                    if not match.empty:
                        # Mot trouvé, écriture du remplaçant
                        f_w.write(str(match.iloc[0, 1]) + " ")
                    else:
                        # Mot inchangé
                        f_w.write(mot + " ")
                
                f_w.write("\n")  # Nouvelle ligne après chaque ligne traitée

    