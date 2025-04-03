
import pandas as pd


def substitue(texte, replacables, output):
    df = pd.read_csv(replacables, sep="\t")
    with open(output, "a", encoding="utf-8") as f_w:
        with open(texte, "r", encoding="utf-8") as f_r:
            for ligne in f_r.readlines():
                mots = str(ligne).split()
                for mot in mots:
                    match = df[df.iloc[:, 0] == mot]  # Filter by first column
                    if not match.empty:
                        f_w.write(str(match.iloc[0, 1])+ " ")
                    else:
                        f_w.write(mot + " ")
                f_w.write("\n")



if __name__ == "__main__":
    print()
    