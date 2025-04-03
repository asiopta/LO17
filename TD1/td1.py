import pandas as pd

c_r = "Un corbeau tient un fromage dans son bec. Un renard rusé le flatte pour le tromper et lui faire lâcher son repas."
r_b = "Un renard et un bouc tombent dans un puits. Le renard parvient à tromper le bouc pour s’en sortir, puis l’abandonne au fond."
l_a = "Un loup cherche un prétexte pour faire de l’agneau innocent son repas."
r_c = "Un renard invite une cigogne à dîner mais lui sert un repas inadapté; la cigogne se venge de la même manière."
ldb = "Un loup se déguise en berger pour tromper les moutons, mais il est vite démasqué et puni."

stories = [c_r, r_b, l_a, r_c, ldb]
incidence_matrix_2= [
        [1, 1, 0, 0, 0, 0, 1, 1, 1],
        [0, 1, 0, 1, 0, 0, 0, 0, 1],
        [0, 0, 0, 0, 1, 0, 0, 1, 0],
        [0, 1, 1, 0, 0, 0, 0, 1, 0],
        [0, 0, 0, 0, 1, 1, 0, 0, 1]
    ]

incidence_matrix = [
    [1, 0, 0, 0, 0],
    [1, 1, 0, 1, 0],
    [0, 0, 0, 1, 0],
    [0, 1, 0, 0, 0],
    [0, 0, 1, 0, 1],
    [0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0],
    [1, 0, 1, 1, 0],
    [1, 1, 0, 0, 1]
]

inversed_index = {}

def liste_termes(stories: list[str]) -> pd.DataFrame:
    inverted_index = pd.DataFrame({"terme": [], "DocId": []})
    for i in range(len(stories)):
        story = stories[i]
        story = "".join([char 
                         for char in story 
                         if char not in [".", ",", ";", ":"]])
        
        story = story.lower()
        words = story.split(" ")
        for word in words:
            inverted_index.loc[len(inversed_index)] = [word, i]
    
    return inverted_index.sort_values(by="terme", ascending=True)

def create_inverted_index(liste_termes):
    resultat = liste_termes.groupby("termes")["DocId"].apply(lambda x: list(set(x)) if len(set(x)) > 1 else x.iloc[0]).reset_index()
    return resultat


if __name__ == "__main__":
    termes = liste_termes(stories)
    print(termes)
    res = create_inverted_index(termes)
    print(res)
