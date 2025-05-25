# Importations
from bs4 import BeautifulSoup
from pathlib import Path
import pandas as pd

# ------------------------------------------------------
# Fonction pour extraire l'ID du fichier
def extract_fichier(fichier_html, fichier_xml):
    '''Extrait l'ID du fichier (nom sans extension)'''
    with open(fichier_xml, 'a', encoding="utf-8") as f2:
        f2.write("<fichier>")
        fichier = fichier_html.split("\\")[-1].split(".")[0]  # Récupère le nom du fichier sans extension
        f2.write(fichier)
        f2.write("</fichier>\n")

# ------------------------------------------------------
# Fonction pour extraire le titre, la date et le numéro de bulletin
def extract_title(fichier_html, fichier_xml):
    '''Extrait le titre, le numéro du bulletin et la date'''
    with open(fichier_html, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f, "html.parser")
    
    balise_title = soup.title.string.split(">")  # Découpe la balise <title>

    # Réorganise la date (inverse le format)
    date = balise_title[0].split("/")
    fixed_date = date[2][:-1] + "/" + date[1] + "/" + date[0]

    titre = balise_title[2]
    num_bulletin = balise_title[1].split("\xa0")[1]

    with open(fichier_xml, 'a', encoding="utf-8") as f2:
        f2.write("<numero>")
        f2.write(num_bulletin)
        f2.write("</numero>\n")

        f2.write("<date>")
        f2.write(fixed_date)
        f2.write("</date>\n")

        f2.write("<titre>")
        f2.write(titre)
        f2.write("</titre>\n")

# ------------------------------------------------------
# Fonction pour extraire l'auteur
def extract_author(fichier_html, fichier_xml):
    '''Extrait le nom de l'auteur'''
    with open(fichier_html, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f, "html.parser")
    
    meta_tag = soup.find("meta", attrs={"name": "author"})
    span_tags = soup.find_all("span", class_="style95")

    if meta_tag:
        with open(fichier_xml, 'a', encoding="utf-8") as f2:
            for span in span_tags:
                content = span.get_text(separator=" ", strip=True)
                if content and "email" in content and "-" in content:
                    f2.write("<auteur>")
                    nom = content.split("-")[1] + "-" + content.split("-")[2]
                    f2.write(nom)
                    f2.write("</auteur>\n")

# ------------------------------------------------------
# Fonction pour extraire le texte principal
def extract_text(fichier_html, fichier_xml):
    '''Extrait le texte principal du fichier'''
    with open(fichier_html, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f, "html.parser")
    
    span_tags = soup.find_all("span", class_="style95")
    texte = ""

    with open(fichier_xml, 'a', encoding="utf-8") as f2:
        for i, span in enumerate(span_tags):
            for content in span.stripped_strings:
                if content and content[-1] == ".":
                    texte += " " + content
        f2.write("<texte>")
        f2.write(texte)
        f2.write("</texte>\n")

# ------------------------------------------------------
# Fonction pour extraire la rubrique
def extract_rubrique(fichier_html, fichier_xml):
    '''Extrait la rubrique du fichier'''
    with open(fichier_html, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f, "html.parser")
    
    span_tags = soup.find_all("span", class_="style42")

    with open(fichier_xml, 'a', encoding="utf-8") as f2:
        for i, span in enumerate(span_tags):
            for content in span.stripped_strings:
                if "/" not in content:
                    f2.write("<rubrique>")
                    f2.write(content)
                    f2.write("</rubrique>\n")

# ------------------------------------------------------
# Fonction pour extraire les URL et légendes des images
def extract_images_legends(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f, "html.parser")

    images_info = []
    for div in soup.find_all("div", style="text-align: center"):
        img_tag = div.find("img")
        span_tag = div.find("span", class_="style21")
        if img_tag and span_tag:
            img_url = img_tag["src"]
            legende = span_tag.get_text(strip=True)
            images_info.append((img_url, legende))
    return images_info

# ------------------------------------------------------
# Fonction pour écrire les images et légendes dans le XML
def write_image_infos(fichier_html, fichier_xml):
    img_infos = extract_images_legends(fichier_html)
    with open(fichier_xml, 'a', encoding="utf-8") as f2:
        if img_infos:
            f2.write("<images>\n")
            for (img_src, img_legende) in img_infos:
                f2.write("<image>\n")
                f2.write("<urlImage>")
                f2.write(img_src)
                f2.write("</urlImage>\n")
                f2.write("<legendeImage>")
                f2.write(img_legende)
                f2.write("</legendeImage>\n")
                f2.write("</image>\n")
            f2.write("</images>\n")

# ------------------------------------------------------
# Fonction pour extraire les contacts
def extract_contacts(fichier_html, fichier_xml):
    '''Extrait les contacts dans les balises <span> (sans lien "67391.htm")'''
    with open(fichier_html, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f, "html.parser")

    span_tags = soup.find_all("span", class_="style85")
    with open(fichier_xml, 'a', encoding="utf-8") as f2:
        for span in span_tags:
            content = span.get_text(separator=" ", strip=True)
            if "-" in content:
                f2.write("<contact>")
                f2.write(content)
                f2.write("</contact>\n")

# ------------------------------------------------------
# Fonction principale pour un seul bulletin
def extract_file(fichier_html, fichier_xml):
    with open(fichier_xml, "a", encoding="utf-8") as f:
        f.write("<bulletin>\n")
    
    extract_fichier(fichier_html, fichier_xml)
    extract_title(fichier_html, fichier_xml)
    extract_rubrique(fichier_html, fichier_xml)
    extract_author(fichier_html, fichier_xml)
    extract_text(fichier_html, fichier_xml)
    write_image_infos(fichier_html, fichier_xml)
    extract_contacts(fichier_html, fichier_xml)
    
    with open(fichier_xml, "a", encoding="utf-8") as f:
        f.write("</bulletin>\n")

# ------------------------------------------------------
# Fonction pour tous les bulletins dans un répertoire
def extract_all_files(directory, fichier_xml):
    with open(fichier_xml, "w", encoding="utf-8") as f:
        f.write("<corpus>\n")
    
    dir_path = Path(directory)
    if not dir_path.is_dir():
        print("Invalid directory path")
        return
    
    for file in dir_path.iterdir():
        if file.is_file():
            file_name = str(file.resolve())
            extract_file(fichier_html=file_name, fichier_xml=fichier_xml)
    
    with open(fichier_xml, "a", encoding="utf-8") as f:
        f.write("</corpus>\n")

# ------------------------------------------------------
# Point d'entrée du script
if __name__ == "__main__":
    extract_all_files("BULLETINS", "corpus.XML")
