import xml.etree.ElementTree as ET
from pathlib import Path
import pandas as pd
import spacy
import nltk
from nltk.stem.snowball import FrenchStemmer
from collections import defaultdict
import string
import re
import spacy


try:
    NLP_SPACY = spacy.load("fr_core_news_sm")
    print("Modèle spaCy 'fr_core_news_sm' chargé pour TD4.")
except OSError:
    print("ERREUR TD4: Modèle spaCy 'fr_core_news_sm' non trouvé.")
    NLP_SPACY = exit()


# --- Configuration ---
INPUT_XML_TD3_FILTERED = Path("corpus_td3_filtered.xml")
TOKENS_FOR_LEMMATIZATION_FILE = Path("td4_tokens_for_lemmatization.tsv")
LEMMAS_SPACY_FILE = Path("td4_mots_lemmes_spacy.tsv")
LEMMAS_SNOWBALL_FILE = Path("td4_mots_racines_snowball.tsv")

CHOSEN_LEMMA_METHOD = "spacy"
OUTPUT_XML_TD4_LEMMATIZED = Path(f"corpus_td4_lemmatized_{CHOSEN_LEMMA_METHOD}.xml")

INV_INDEX_TEXTE_LEMMES_FILE = Path("td4_inv_index_texte_lemmes.tsv")
INV_INDEX_TITRE_LEMMES_FILE = Path("td4_inv_index_titre_lemmes.tsv")
INV_INDEX_RUBRIQUE_FILE = Path("td4_inv_index_rubrique.tsv")
INV_INDEX_DATE_FILE = Path("td4_inv_index_date.tsv")


INVALID_XML_CHARS_RE = re.compile(r'[\x00-\x08\x0b\x0c\x0e-\x1f]')

def clean_xml_text(text: str) -> str:
    if text is None:
        return None
    text_str = str(text)
    return INVALID_XML_CHARS_RE.sub('', text_str)

def tokenize_text_for_index(text: str) -> list:
    if not text or not NLP_SPACY:
        return []

    doc = NLP_SPACY(text)
    tokens = [
        token.lower_
        for token in doc
        if not token.is_punct and not token.is_space and token.text.strip()
    ]
    return tokens


def extract_tokens_for_lemmatization(input_xml: Path, output_tokens_file: Path):
    if not input_xml.is_file():
        print(f"ERREUR: Fichier XML '{input_xml}' non trouvé.")
        return False
    try:
        tree = ET.parse(input_xml)
        root = tree.getroot()
    except ET.ParseError as e:
        print(f"ERREUR: Parsing XML '{input_xml}' échoué: {e}")
        return False

    with open(output_tokens_file, "w", encoding="utf-8") as f_out:
        f_out.write("doc_id\tmot_original\n")
        for bulletin in root.findall(".//bulletin"):
            doc_id_tag = bulletin.find("fichier")
            if doc_id_tag is None or not doc_id_tag.text:
                continue
            doc_id = doc_id_tag.text.strip()

            for tag_name in ["titre", "texte"]:
                tag = bulletin.find(tag_name)
                if tag is not None and tag.text:
                    tokens = tokenize_text_for_index(tag.text)
                    for token in tokens:
                        f_out.write(f"{doc_id}\t{token}\n")
    print(f"Tokens extraits pour lemmatisation dans {output_tokens_file}")
    return True

def lemmatize_with_spacy(input_tokens_file: Path, output_lemmas_file: Path):
    try:
        df = pd.read_csv(input_tokens_file, sep='\t', usecols=['mot_original'])
    except FileNotFoundError:
        print(f"ERREUR: Fichier tokens '{input_tokens_file}' non trouvé pour spaCy.")
        return False
    
    mots_uniques = df['mot_original'].dropna().unique()
    
    try:
        nlp = spacy.load("fr_core_news_sm")
    except OSError:
        print("Modèle spaCy 'fr_core_news_sm' non trouvé.")
        return False

    results = []
    for mot in mots_uniques:
        doc = nlp(str(mot)) 
        if doc and len(doc) > 0:
             results.append({'mot': mot, 'lemme_spacy': doc[0].lemma_})
        else:
            results.append({'mot': mot, 'lemme_spacy': mot}) 

    pd.DataFrame(results).to_csv(output_lemmas_file, sep='\t', index=False, encoding='utf-8')
    print(f"Lemmes spaCy générés dans {output_lemmas_file}")
    return True

def stem_with_snowball(input_tokens_file: Path, output_stems_file: Path):
    try:
        df = pd.read_csv(input_tokens_file, sep='\t', usecols=['mot_original'])
    except FileNotFoundError:
        print(f"ERREUR: Fichier tokens '{input_tokens_file}' non trouvé pour Snowball.")
        return False
        
    mots_uniques = df['mot_original'].dropna().unique()
    stemmer = FrenchStemmer()
    results = [{'mot': mot, 'racine_snowball': stemmer.stem(str(mot))} for mot in mots_uniques]
    pd.DataFrame(results).to_csv(output_stems_file, sep='\t', index=False, encoding='utf-8')
    print(f"Racines Snowball générées dans {output_stems_file}")
    return True

def substitute_words_in_xml(input_xml: Path, substitution_map_file: Path, output_xml: Path):
    if not input_xml.is_file():
        print(f"ERREUR: Fichier XML '{input_xml}' non trouvé pour substitution.")
        return False
    if not substitution_map_file.is_file():
        print(f"ERREUR: Fichier de mapping '{substitution_map_file}' non trouvé.")
        return False

    try:
        sub_map_df = pd.read_csv(substitution_map_file, sep='\t', header=0)
        
        if sub_map_df.shape[1] < 2:
            print(f"ERREUR: Fichier de mapping '{substitution_map_file}' doit avoir au moins 2 colonnes.")
            return False
        
        original_col_name = sub_map_df.columns[0]
        substitution_col_name = sub_map_df.columns[1]

        substitution_dict = pd.Series(sub_map_df[substitution_col_name].values, index=sub_map_df[original_col_name]).to_dict()
        
    except Exception as e:
        print(f"ERREUR: Lecture du fichier de mapping '{substitution_map_file}' échouée: {e}")
        return False

    try:
        tree = ET.parse(input_xml)
        root = tree.getroot()
    except ET.ParseError as e:
        print(f"ERREUR: Parsing XML '{input_xml}' échoué: {e}")
        return False

    for bulletin in root.findall(".//bulletin"):
        for tag_name in ["titre", "texte"]:
            tag = bulletin.find(tag_name)
            if tag is not None and tag.text:
                original_text = tag.text
                tokens = tokenize_text_for_index(original_text)
                substituted_tokens = [substitution_dict.get(token, token) for token in tokens]
                tag.text = clean_xml_text(" ".join(substituted_tokens))
    try:
        tree.write(output_xml, encoding="utf-8", xml_declaration=True)
        print(f"Corpus XML substitué (lemmatisé/racinisé) enregistré dans {output_xml}")
        return True
    except Exception as e:
        print(f"ERREUR: Impossible d'écrire le XML substitué '{output_xml}': {e}")
        return False

def create_inverted_index_from_xml_field(input_xml_lemmatized: Path, field_name: str, output_inv_index_file: Path, is_text_field=True):
    if not input_xml_lemmatized.is_file():
        print(f"ERREUR: Fichier XML lemmatisé '{input_xml_lemmatized}' non trouvé.")
        return False
        
    inverted_index = defaultdict(lambda: defaultdict(int)) # terme -> {doc_id: freq}
    doc_ids = set()

    try:
        tree = ET.parse(input_xml_lemmatized)
        root = tree.getroot()
    except ET.ParseError as e:
        print(f"ERREUR: Parsing XML '{input_xml_lemmatized}' échoué: {e}")
        return False

    for bulletin in root.findall(".//bulletin"):
        doc_id_tag = bulletin.find("fichier")
        if doc_id_tag is None or not doc_id_tag.text:
            continue
        doc_id = doc_id_tag.text.strip()
        doc_ids.add(doc_id)

        field_tag = bulletin.find(field_name)
        if field_tag is not None and field_tag.text:
            content = field_tag.text.strip()
            if is_text_field:
                tokens = tokenize_text_for_index(content) # Utilise la même tokenisation
                for token in tokens:
                    inverted_index[token][doc_id] += 1
            else: # Pour les champs non textuels comme 'rubrique' ou 'date', le contenu est le terme lui-même
                term = content.lower() # ou une normalisation spécifique si besoin
                if term:
                    inverted_index[term][doc_id] += 1
    
    with open(output_inv_index_file, "w", encoding="utf-8") as f_out:
        f_out.write("terme\tdoc_id\tfrequence\n")
        for term, postings in sorted(inverted_index.items()):
            for doc_id, freq in sorted(postings.items()):
                f_out.write(f"{term}\t{doc_id}\t{freq}\n")
    
    print(f"Index inversé pour le champ '{field_name}' créé dans {output_inv_index_file} ({len(doc_ids)} documents)")
    return True

if __name__ == "__main__":
    print("=== DÉBUT TRAITEMENT TD4 ===")

    # Étape 1: Création des lemmes (extraire tokens d'abord)
    print("\n--- TD4 Étape 1.1: Extraction des tokens pour lemmatisation ---")
    if not extract_tokens_for_lemmatization(INPUT_XML_TD3_FILTERED, TOKENS_FOR_LEMMATIZATION_FILE):
        print("Arrêt: Échec de l'extraction des tokens.")
    else:
        print("\n--- TD4 Étape 1.2: Lemmatisation avec spaCy ---")
        lemmatize_with_spacy(TOKENS_FOR_LEMMATIZATION_FILE, LEMMAS_SPACY_FILE)


        chosen_lemma_file = LEMMAS_SPACY_FILE if CHOSEN_LEMMA_METHOD == "spacy" else LEMMAS_SNOWBALL_FILE
        if not chosen_lemma_file.is_file():
             print(f"ERREUR: Le fichier de lemmes choisi '{chosen_lemma_file}' n'existe pas. Vérifiez le choix et l'exécution des étapes précédentes.")
        else:
            print("\n--- TD4 Étape 1.5: Substitution des mots par les lemmes/racines dans le XML ---")
            if substitute_words_in_xml(INPUT_XML_TD3_FILTERED, chosen_lemma_file, OUTPUT_XML_TD4_LEMMATIZED):
                
                print("\n--- TD4 Étape 2: Création des fichiers inverses ---")
                create_inverted_index_from_xml_field(OUTPUT_XML_TD4_LEMMATIZED, "texte", INV_INDEX_TEXTE_LEMMES_FILE, is_text_field=True)
                create_inverted_index_from_xml_field(OUTPUT_XML_TD4_LEMMATIZED, "titre", INV_INDEX_TITRE_LEMMES_FILE, is_text_field=True)
                create_inverted_index_from_xml_field(OUTPUT_XML_TD4_LEMMATIZED, "rubrique", INV_INDEX_RUBRIQUE_FILE, is_text_field=False)
                create_inverted_index_from_xml_field(OUTPUT_XML_TD4_LEMMATIZED, "date", INV_INDEX_DATE_FILE, is_text_field=False)
                # Ajoutez d'autres champs si nécessaire (ex: auteur, etc.)

    print("\n=== FIN TRAITEMENT TD4 ===")