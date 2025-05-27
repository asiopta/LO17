import os
from pathlib import Path
from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET
from xml.dom import minidom
import re

INVALID_XML_CHARS_RE = re.compile(r'[\x00-\x08\x0b\x0c\x0e-\x1f]')

# Fonctions d'extraction pour UN SEUL bulletin (fichier HTML)

def extract_single_bulletin_data(html_file_path: Path) -> dict:
    """
    Extrait toutes les informations pertinentes d'un fichier HTML de bulletin.
    Retourne un dictionnaire contenant les données extraites.
    """
    data = {
        "fichier": None,
        "numero": None,
        "date": None,
        "titre": None,
        "rubrique": None,
        "auteur": None,
        "texte": "", 
        "images": [],
        "contact": None
    }

    try:
        # Extraire le nom de fichier de base comme identifiant
        data["fichier"] = html_file_path.stem

        with open(html_file_path, "r", encoding="utf-8") as f:
            soup = BeautifulSoup(f, "html.parser")

        # --- Extraction Titre, Numéro, Date (depuis <title>) ---
        if soup.title and soup.title.string:
            title_parts = soup.title.string.split(">")
            try:
                # Date
                date_str = title_parts[0].strip()
                date_parts = date_str.split("/")
                # Vérifier qu'on a bien 3 parties et qu'elles sont numériques
                if len(date_parts) == 3 and all(p.isdigit() for p in date_parts):
                    # Format attendu JJ/MM/AAAA à partir de AAAA/MM/JJ
                    data["date"] = f"{date_parts[2].zfill(2)}/{date_parts[1].zfill(2)}/{date_parts[0]}"
                else:
                    print(f"Format de date non reconnu ou incomplet dans <title> pour {html_file_path.name}: {title_parts[0]}")

                # Numéro
                num_part = title_parts[1].replace("\xa0", " ").strip()
                if "BE France" in num_part:
                    data["numero"] = num_part.split(" ")[-1] # Prend le dernier élément après split par espace

                # Titre de l'article
                data["titre"] = title_parts[2].replace("\xa0", " ").strip()
            except IndexError:
                print(f"Structure <title> non supporté dans {html_file_path.name}: {soup.title.string}")
        else:
             print(f"Balise <title> manquante ou vide dans {html_file_path.name}")

        # Extraction Rubrique (span.style42)
        # Prend la première rubrique trouvée qui ne contient pas '/'
        rubrique_tag = soup.find("span", class_="style42")
        if rubrique_tag:
            rubrique_text = rubrique_tag.get_text(strip=True)
            if "/" not in rubrique_text:
                data["rubrique"] = rubrique_text
            else:
                 # Essayer de trouver une autre balise si la première ne convient pas
                 all_rubriques = soup.find_all("span", class_="style42")
                 for tag in all_rubriques:
                     text = tag.get_text(strip=True)
                     if "/" not in text and text: # Vérifie non vide aussi
                         data["rubrique"] = text
                         break # Prend la première trouvée


        # Extraction Texte (span.style95)
        main_content_td = None
        title_tag = soup.find("span", class_="style17") # Titre de l'article
        if title_tag:
            main_content_td = title_tag.find_parent("td")

        if main_content_td:
            text_spans = main_content_td.find_all("span", class_="style95")
            collected_text = []
            for span in text_spans:
                span_text = " ".join(span.stripped_strings)
                # Appliquer les filtres existants si nécessaire,
                # ou s'assurer que ces spans sont bien ceux du corps de l'article
                # (par ex. en vérifiant qu'ils ne sont pas dans une sous-structure contact/auteur à l'intérieur de ce td)
                if "Rédacteurs" not in span_text and "Pour en savoir plus" not in span_text: # Maintenir les filtres actuels
                    collected_text.append(span_text)
            data["texte"] = " ".join(collected_text).strip()
        else: # Fallback si le td principal n'est pas trouvé via le titre
            # Utiliser l'ancienne méthode, mais attention à sa portée globale
            span_tags_text = soup.find_all("span", class_="style95")
            collected_text = []
            for span in span_tags_text:
                span_text = " ".join(span.stripped_strings)
                if "Rédacteurs" not in span_text and "Pour en savoir plus" not in span_text:
                    collected_text.append(span_text)
            data["texte"] = " ".join(collected_text).strip()
        # Extraction Images (div align center > img + span.style21)
        centered_divs = soup.find_all("div", style=lambda s: s and "text-align: center" in s)
        counter = 0
        for div in centered_divs:
            counter += 1
            img_tag = div.find("img")
            if img_tag and img_tag.get("src"):
                img_url = f"../BULLETINS/IMAGESWEB/{data['fichier']}_0{counter}.jpg"
                final_legend_text = ""

                # Prioriser span.style21 pour la légende
                legend_span_style21 = div.find("span", class_="style21")
                if legend_span_style21:
                    text = legend_span_style21.get_text(strip=True)
                    if text and not text.lower().startswith("crédits"):
                        final_legend_text = text

                data["images"].append({"urlImage": img_url, "legendeImage": final_legend_text})

        # --- Extraction Contact (et auteur dérivé du contact) ---
        data["contact"] = None
        data["auteur"] = None

        contact_details_list = []
        contact_label_tags = soup.find_all(lambda tag: "Pour en savoir plus, contacts :" in tag.get_text(strip=True) and tag.name == "span" and "style28" in tag.get("class", []))
        if not contact_label_tags: 
             contact_label_tags = soup.find_all(lambda tag: "Pour en savoir plus, contacts :" in tag.get_text(strip=True))

        contact_info_td = None
        for label_tag in contact_label_tags:
            parent_td = label_tag.find_parent("td")
            if parent_td:
                details_td_candidate = parent_td.find_next_sibling("td")
                if details_td_candidate:
                    contact_info_td = details_td_candidate # Garder la référence au td pour l'auteur
                    potential_contact_spans = details_td_candidate.find_all("span", class_="style85")
                    for contact_span in potential_contact_spans:
                        contact_line = contact_span.get_text(separator=" ", strip=True)
                        is_redacteur_section = False
                        # Vérifier si ce span est sous une section "Rédacteur" précédente dans le même bloc
                        previous_strong_labels = contact_span.find_all_previous("span", class_="style28")
                        for prev_label in previous_strong_labels:
                            if "Rédacteur" in prev_label.get_text(strip=True):
                                is_redacteur_section = True
                                break
                        if not is_redacteur_section and contact_line:
                            contact_details_list.append(contact_line)
                    
                    if contact_details_list:
                        data["contact"] = " ".join(contact_details_list).strip()
                        # Maintenant, essayons d'extraire l'auteur de la première ligne de contact pertinente
                        # On suppose que la première ligne de contact contient souvent le nom de la personne
                        first_contact_line_for_author = None
                        if contact_info_td: # Utiliser le td identifié pour les contacts
                            first_relevant_span = contact_info_td.find("span", class_="style85")
                            if first_relevant_span:
                                first_contact_line_for_author = first_relevant_span.get_text(separator=" ", strip=True)
                        
                        if first_contact_line_for_author:
                            # Exemple: "Inria/Sophia Antipolis-Méditerranée - Olivier Bernard : tél. : ..."
                            # Ou: "CNES - Julien Watelet : tél. : ..."
                            # Ou: "Ingérop - Silvia Nimo : tél. : ..."
                            # On cherche à isoler "Olivier Bernard", "Julien Watelet", "Silvia Nimo"
                            
                            # Séparer la partie avant " : tél." ou " - email" ou juste ":"
                            name_part_match = re.search(r"(.*?)\s*(: tél\.|\s-\s*email\s*:)", first_contact_line_for_author, re.IGNORECASE)
                            if name_part_match:
                                name_section = name_part_match.group(1).strip()
                                # Souvent, la structure est "Organisation - Nom Personne" ou juste "Nom Personne"
                                if " - " in name_section:
                                    potential_name = name_section.split(" - ")[-1].strip()
                                    # Vérifier que ce n'est pas juste une partie de l'organisation
                                    # ou une fonction si possible (difficile sans plus de règles)
                                    # Simple vérification : contient au moins un espace (prénom nom) ou est capitalisé
                                    if (" " in potential_name or potential_name.istitle()) and len(potential_name) > 3 : # Éviter les acronymes courts
                                        data["auteur"] = potential_name
                                else: # Si pas de " - ", on suppose que c'est le nom directement
                                    if (" " in name_section or name_section.istitle()) and len(name_section) > 3 :
                                        data["auteur"] = name_section
                            
                            if data["auteur"]:
                                print(f"  Auteur extrait du contact pour {html_file_path.name}: {data['auteur']}")
                            else:
                                print(f"  N'a pas pu extraire un nom d'auteur distinct de la ligne de contact: {first_contact_line_for_author}")
                        else:
                            print(f"  Pas de première ligne de contact trouvée pour l'extraction de l'auteur pour {html_file_path.name}")
                        break # Contacts (et auteur potentiel) trouvés
            if data["contact"]:
                break
        
        if not data["contact"]:
            print(f"  Informations de contact non trouvées pour {html_file_path.name}")
        if not data["auteur"]:
            # Fallback : si aucun auteur n'est extrait du contact,
            # vous pouvez remettre ici l'ancienne logique de recherche de "Rédacteur: Jean-François Desessard"
            # ou décider de laisser l'auteur vide si la source principale (contact) ne donne rien.
            # Pour l'instant, on le laisse potentiellement vide si non trouvé dans le contact.
            print(f"  Auteur final non défini pour {html_file_path.name} (sera vide si non trouvé dans contact).")

    except FileNotFoundError:
        print(f"ERREUR: Fichier non trouvé {html_file_path}")
        return None
    except Exception as e:
        print(f"ERREUR: Erreur lors du parsing de {html_file_path.name}: {e}")
        return None

    return data

def clean_xml_text(text: str) -> str:
    """
    Supprime les caractères invalides pour XML 1.0 d'une chaîne.
    Retourne None si l'entrée est None.
    """
    if text is None:
        return None
    # S'assurer que c'est une chaîne avant de nettoyer
    text_str = str(text)
    return INVALID_XML_CHARS_RE.sub('', text_str)

# Fonctions de génération XML

def create_bulletin_element(bulletin_data: dict) -> ET.Element:
    
    # Crée un élément XML <bulletin> à partir du dictionnaire de données.
    
    bulletin_el = ET.Element("bulletin")

    # Fonction interne pour ajouter un sous-élément en nettoyant le texte
    def add_sub_element(parent, tag_name, text_content):
        cleaned_text = clean_xml_text(text_content)
        # Ajouter l'élément seulement si le contenu nettoyé n'est pas None/vide
        if cleaned_text is not None and cleaned_text.strip() != "":
            ET.SubElement(parent, tag_name).text = cleaned_text
        # Optionnel: ajouter même si vide ? Dépend du besoin.
        # elif text_content is not None: # Si on veut des balises vides <tag></tag>
        #     ET.SubElement(parent, tag_name).text = ""


    # Ajouter chaque champ en utilisant la fonction interne de nettoyage
    add_sub_element(bulletin_el, "fichier", bulletin_data.get("fichier"))
    add_sub_element(bulletin_el, "numero", bulletin_data.get("numero"))
    add_sub_element(bulletin_el, "date", bulletin_data.get("date"))
    add_sub_element(bulletin_el, "rubrique", bulletin_data.get("rubrique"))
    add_sub_element(bulletin_el, "titre", bulletin_data.get("titre"))
    add_sub_element(bulletin_el, "auteur", bulletin_data.get("auteur"))
    add_sub_element(bulletin_el, "texte", bulletin_data.get("texte"))

    # Gestion des images
    images_data = bulletin_data.get("images")
    if images_data: # Vérifie si la liste existe et n'est pas vide
        images_el = ET.SubElement(bulletin_el, "images")
        for img_info in images_data:
            image_el = ET.SubElement(images_el, "image")
            add_sub_element(image_el, "urlImage", img_info.get("urlImage"))
            add_sub_element(image_el, "legendeImage", img_info.get("legendeImage"))

    add_sub_element(bulletin_el, "contact", bulletin_data.get("contact"))

    return bulletin_el

def prettify_xml(element: ET.Element) -> str:
    """
    Retourne une chaîne XML formatée (indentée) pour la lisibilité.
    """
    rough_string = ET.tostring(element, 'utf-8')
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="  ", encoding="utf-8").decode("utf-8")

# Fonction principale pour traiter tous les fichiers

def process_all_bulletins(input_dir: str, output_xml_file: str):
    """
    Parcourt tous les fichiers .htm dans le répertoire d'entrée,
    extrait les données et écrit le fichier XML de sortie.
    """
    input_path = Path(input_dir)
    output_path = Path(output_xml_file)


    # Créer l'élément racine du XML
    root = ET.Element("corpus")

    print(f"Traitement des fichiers dans : {input_path}")
    file_count = 0
    processed_count = 0
    error_count = 0

    # Itérer sur les fichiers .htm ou .html dans le répertoire
    for html_file in list(input_path.glob('*.htm')) + list(input_path.glob('*.html')):
        file_count += 1
        print(f"  -> Traitement de {html_file.name}...")
        bulletin_data = extract_single_bulletin_data(html_file)

        if bulletin_data:
            bulletin_element = create_bulletin_element(bulletin_data)
            root.append(bulletin_element)
            processed_count += 1
        else:
            error_count += 1

    print(f"\nTraitement terminé.")
    print(f"  Fichiers trouvés : {file_count}")
    print(f"  Bulletins traités avec succès : {processed_count}")
    print(f"  Erreurs rencontrées : {error_count}")

    # Écrire l'arbre XML complet dans le fichier de sortie
    try:
        # Créer une version indentée pour la lisibilité
        pretty_xml_str = prettify_xml(root)
        with open(output_path, "w", encoding="utf-8") as f_out:
             f_out.write(pretty_xml_str)
        print(f"Fichier XML généré : {output_path}")
    except Exception as e:
        print(f"ERREUR: Impossible d'écrire le fichier XML de sortie {output_path}: {e}")

# -----------------------------------------------------
# Point d'entrée du script
# -----------------------------------------------------
if __name__ == "__main__":
    INPUT_DIRECTORY = r"C:\Users\loicr\Downloads\LO17\LO17-2\TD2\BULLETINS"
    OUTPUT_XML = r"C:\Users\loicr\Downloads\LO17\LO17-2\TD2\corpus_td2.xml"
    process_all_bulletins(INPUT_DIRECTORY, OUTPUT_XML)