import pandas as pd
from pathlib import Path
import string
import spacy
from collections import Counter

# --- Configuration ---
# Fichier de tokens bruts (sortie de la tokenisation spaCy du TD3 AVANT filtrage par anti-dictionnaire)
# C'est ce fichier qui servira à construire le lexique forme -> lemme
TOKENS_SOURCE_FOR_LEXICON_FILE = Path("td3_tokens.tsv") # Doit être le fichier avant suppression des stop-words du TD3

# Seuils
LEVENSHTEIN_MAX_DIST_PRIMARY = 1  # Distance max pour la correction principale (ED1)
LEVENSHTEIN_MAX_DIST_SECONDARY = 2 # Distance max si ED1 ne donne rien et qu'on utilise une autre méthode

PREFIX_MIN_LEN = 3
PREFIX_DIFF_MAX_LEN = 4
PREFIX_COMMON_MIN_PERCENT = 60

# Charger le modèle spaCy une seule fois
try:
    NLP_SPACY = spacy.load("fr_core_news_sm")
    print("Modèle spaCy 'fr_core_news_sm' chargé pour TD5.")
except OSError:
    print("ERREUR TD5: Modèle spaCy 'fr_core_news_sm' non trouvé.")
    NLP_SPACY = exit()

class SpellCorrector:
    def __init__(self, tokens_source_path: Path):
        self.word_to_lemma = {} # Dictionnaire principal: {forme_tokenisée: lemme}
        self.all_known_lemmas = set() # Ensemble de tous les lemmes valides
        self.lemma_frequencies = Counter() # sert à départager des candidats

        if NLP_SPACY and tokens_source_path and tokens_source_path.is_file():
            self._build_lexicon_from_tokens_and_spacy(tokens_source_path)
        else:
            print(f"WARN: Fichier de tokens source '{tokens_source_path}' non fourni, non trouvé ou modèle spaCy non chargé.")

    def _build_lexicon_from_tokens_and_spacy(self, file_path: Path):
        """
        Construit le lexique {forme_originale_tokenisée: lemme}, l'ensemble des lemmes
        et calcule la fréquence de chaque lemme à partir du fichier de tokens
        (ex: td3_tokens.tsv, qui contient tous les tokens après tokenisation spaCy
        et AVANT suppression des stop-words).
        """
        print(f"Construction du lexique et des fréquences de lemmes depuis '{file_path}' avec spaCy...")
        try:
            # Lire tous les tokens (colonne 'mot')
            df = pd.read_csv(file_path, sep='\t', usecols=['mot'], dtype={'mot': str}, keep_default_na=False, na_values=[''])
            if 'mot' not in df.columns:
                 print(f"ERREUR: La colonne 'mot' n'a pas été trouvée dans {file_path}. Vérifiez le format du fichier.")
                 return
            
            all_tokens_in_corpus = [str(word) for word in df['mot'] if pd.notna(word) and str(word).strip()]
            print(f"  Nombre total de tokens lus depuis le fichier source : {len(all_tokens_in_corpus)}")

            # 1. Calculer les fréquences des lemmes sur l'ensemble des tokens du corpus
           
           
            lemmas_for_frequency_counting = []
           
            batch_size = 10000
            for i in range(0, len(all_tokens_in_corpus), batch_size):
                batch_docs = NLP_SPACY.pipe(all_tokens_in_corpus[i:i+batch_size], disable=["parser", "ner"])
                for doc in batch_docs:
                    if len(doc) > 0: # Chaque "mot" du TSV devrait être un token
                        lemmas_for_frequency_counting.append(doc[0].lemma_.lower())
            
            self.lemma_frequencies = Counter(lemmas_for_frequency_counting)
            print(f"  Fréquences des lemmes calculées pour {len(self.lemma_frequencies)} lemmes uniques.")

            unique_original_forms = set(all_tokens_in_corpus) # Obtenir les formes uniques
            print(f"  Nombre de formes uniques à lemmatiser pour le mapping: {len(unique_original_forms)}")
            
            unique_forms_list = list(unique_original_forms)
            for i in range(0, len(unique_forms_list), batch_size):
                batch_docs_unique = NLP_SPACY.pipe(unique_forms_list[i:i+batch_size], disable=["parser", "ner"])
                for doc_unique in batch_docs_unique:
                    if len(doc_unique) > 0:
                        original_form_lower = doc_unique.text.lower() # La forme telle qu'elle était, en minuscule
                        lemma_lower = doc_unique[0].lemma_.lower()
                        
                        # Ajouter au dictionnaire forme -> lemme
                        # Si une forme a déjà été vue (par ex. à cause de la casse initiale différente
                        # mais même minuscule), on ne la remplace pas, spaCy devrait être cohérent.
                        if original_form_lower not in self.word_to_lemma:
                            self.word_to_lemma[original_form_lower] = lemma_lower
                        
                        # Ajouter le lemme à l'ensemble des lemmes connus
                        self.all_known_lemmas.add(lemma_lower)
            
            print(f"Lexique construit : {len(self.word_to_lemma)} formes distinctes (minuscules) mappées.")
            print(f"  Nombre total de lemmes uniques dans all_known_lemmas : {len(self.all_known_lemmas)}")

        except FileNotFoundError:
            print(f"ERREUR: Fichier de tokens source '{file_path}' non trouvé.")
        except Exception as e:
            print(f"ERREUR critique lors de la construction du lexique : {e}")
            import traceback
            traceback.print_exc() # Imprime la trace complète de l'erreur


    def _normalize_input_word(self, word: str) -> str:
        """Normalise un mot en entrée pour la correction (minuscule, sans ponctuation externe)."""
        # La tokenisation de la phrase d'entrée via spaCy devrait déjà bien gérer la ponctuation.
        # Cette fonction est pour s'assurer que le mot est propre avant de chercher dans le lexique.
        return word.lower().strip(string.punctuation + string.whitespace)

    def _levenshtein_distance(self, s1: str, s2: str) -> int:
        if len(s1) < len(s2):
            return self._levenshtein_distance(s2, s1)
        if len(s2) == 0:
            return len(s1)
        previous_row = range(len(s2) + 1)
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row
        return previous_row[-1]

    def _edits1(self, word):
        """Génère tous les mots à une distance d'édition de 1."""
        letters    = 'abcdefghijklmnopqrstuvwxyzéàèùâêîôûçëïüœæ' # Alphabet français étendu
        splits     = [(word[:i], word[i:])    for i in range(len(word) + 1)]
        deletes    = [L + R[1:]               for L, R in splits if R]
        transposes = [L + R[1] + R[0] + R[2:] for L, R in splits if len(R)>1]
        replaces   = [L + c + R[1:]           for L, R in splits if R for c in letters]
        inserts    = [L + c + R               for L, R in splits for c in letters]
        return set(deletes + transposes + replaces + inserts)

    def _known(self, words_to_check):
        """Retourne le sous-ensemble de `words_to_check` qui sont des lemmes connus."""
        return set(w for w in words_to_check if w in self.all_known_lemmas)

    def _prefix_similarity_score(self, word1: str, word2: str) -> float:
        len1, len2 = len(word1), len(word2)
        if len1 < PREFIX_MIN_LEN or len2 < PREFIX_MIN_LEN: return 0.0
        if abs(len1 - len2) > PREFIX_DIFF_MAX_LEN: return 0.0
        common_prefix_len = 0
        for i in range(min(len1, len2)):
            if word1[i] == word2[i]: common_prefix_len += 1
            else: break
        if common_prefix_len == 0 : return 0.0
        return (common_prefix_len / max(len1, len2)) * 100

    def correct_word(self, word_to_correct: str) -> tuple[str | None, str]:
        normalized_word = self._normalize_input_word(word_to_correct)
        if not normalized_word:
            return None, "Mot vide après normalisation."

        if not self.all_known_lemmas: # Si le lexique n'a pas pu être chargé
            return normalized_word, "Lexique vide (mot original retourné)."

        # 1. Vérifier si la forme normalisée est un lemme connu ou une forme connue
        if normalized_word in self.all_known_lemmas:
            return normalized_word, "Lemme trouvé directement dans le lexique."
        if normalized_word in self.word_to_lemma:
            return self.word_to_lemma[normalized_word], "Forme trouvée dans le lexique, lemme retourné."

        # 2. Générer les candidats à distance 1 et vérifier s'ils sont des lemmes connus
        candidates_ed1 = self._known(self._edits1(normalized_word))
        
        if candidates_ed1:
            # S'il y a plusieurs candidats ED1, choisir le plus fréquent (si info dispo) ou le premier
            # Pour l'instant, on prend le "meilleur" basé sur la fréquence du lemme
            # ou simplement un s'il n'y a pas de fréquence.
            if self.lemma_frequencies:
                best_candidate = max(candidates_ed1, key=self.lemma_frequencies.get)
            else:
                best_candidate = candidates_ed1.pop() # Prend un élément arbitraire
            return best_candidate, f"Corrigé par Levenshtein (dist 1 EDITS1) -> {best_candidate}"

        prefix_candidates_details = []
        # On cherche les préfixes sur les clés de word_to_lemma (les formes tokenisées)
        for known_form, lemme_associe in self.word_to_lemma.items():
            score = self._prefix_similarity_score(normalized_word, known_form)
            if score >= PREFIX_COMMON_MIN_PERCENT:
                prefix_candidates_details.append({'mot_lexique_form': known_form, 'lemme': lemme_associe, 'score_prefixe': score})
        
        if prefix_candidates_details:
            prefix_candidates_details.sort(key=lambda x: x['score_prefixe'], reverse=True)
            
            levenshtein_from_prefix = []
            # Tester Levenshtein sur les N meilleurs candidats par préfixe pour limiter le coût
            for cand_info in prefix_candidates_details[:10]: # Ex: sur les 10 meilleurs préfixes
                dist = self._levenshtein_distance(normalized_word, cand_info['mot_lexique_form'])
                if dist <= LEVENSHTEIN_MAX_DIST_SECONDARY : # Utiliser un seuil potentiellement différent
                    levenshtein_from_prefix.append({
                        'lemme': cand_info['lemme'], 
                        'distance': dist, 
                        'score_prefixe': cand_info['score_prefixe'],
                        'forme_candidate': cand_info['mot_lexique_form']
                    })
            
            if levenshtein_from_prefix:
                # Trier par distance, puis par score de préfixe (pour départager les égalités de distance)
                levenshtein_from_prefix.sort(key=lambda x: (x['distance'], -x['score_prefixe']))
                best_choice = levenshtein_from_prefix[0]
                return best_choice['lemme'], f"Corrigé par Levenshtein (dist: {best_choice['distance']}) sur préfixe '{best_choice['forme_candidate']}' (score: {best_choice['score_prefixe']:.0f})"
        
        return None, "Aucune correction satisfaisante trouvée (ED1, préfixe+Lev)."


    def correct_sentence(self, sentence: str) -> list[tuple[str, str | None, str]]:
        """Corrige une phrase en tokenisant avec spaCy et en corrigeant chaque mot."""

        doc = NLP_SPACY(sentence)
        corrections = []
        for token_spacy in doc:
            original_form = token_spacy.text
            
            # On ne corrige que les mots (pas la ponctuation, etc.)
            if token_spacy.is_punct or token_spacy.is_space:
                # On peut choisir de les garder tels quels ou de les ignorer dans la sortie
                # Pour l'instant, on les ignore pour se concentrer sur la correction des mots.
                # Si on veut les garder : corrections.append((original_form, original_form, "Ponctuation/Espace"))
                continue

            normalized_for_correction = self._normalize_input_word(original_form)
            if not normalized_for_correction:
                corrections.append((original_form, None, "Token original vide/ponctuation après normalisation"))
                continue
                
            corrected_lemme, method = self.correct_word(normalized_for_correction)
            corrections.append((original_form, corrected_lemme, method))
        return corrections

if __name__ == "__main__":
    print("=== DÉBUT TEST TD5 : Correcteur Orthographique ===")
    
    if not NLP_SPACY:
        print("Arrêt du script : Modèle spaCy requis mais non chargé.")
    else:
        corrector = SpellCorrector(tokens_source_path=TOKENS_SOURCE_FOR_LEXICON_FILE)

        if not corrector.all_known_lemmas:
            print("\nATTENTION: Le lexique est vide ou n'a pas pu être construit.")
            print("Les tests de correction ne seront pas significatifs.")
        else:
            print(f"\nLexique chargé et construit: {len(corrector.word_to_lemma)} formes mappées à {len(corrector.all_known_lemmas)} lemmes uniques.")
            print(f"Fréquence du lemme 'technologie': {corrector.lemma_frequencies.get('technologie', 0)}")
            print(f"Fréquence du lemme 'recherche': {corrector.lemma_frequencies.get('recherche', 0)}")


            phrases_a_tester = [
                "La technologis et la recherch sont importantes.",
                "Bonjourr le mondde",
                "Un exemmple de phrassse",
                "Les chercheur travaillent sur ce projet.",
                "J'aime la tecknologie",
                "nutritionn et santee",
                "environement et polution",
                "une chaire consacree aux Systemes embarques robustes", # pris de 74751.htm
                "nanoconstruction au service de lhydrogene", # pris de 74174.htm
                "challenges de linnolation sunaero", # pris de 74167.htm
                "ordinateur quantique et suprmatie",
                "le desvelopement durabl"
            ]
            print("\n--- Tests de correction de phrases ---")
            for phrase in phrases_a_tester:
                print(f"\nPhrase originale : \"{phrase}\"")
                resultats = corrector.correct_sentence(phrase)
                for mot_original, lemme_corrige, methode in resultats:
                    if lemme_corrige and lemme_corrige.lower() != mot_original.lower().strip(string.punctuation + string.whitespace):
                        print(f"  '{mot_original}' -> '{lemme_corrige}' (Méthode: {methode})")
                    elif lemme_corrige:
                         print(f"  '{mot_original}' -> '{lemme_corrige}' [OK]")
                    else:
                        print(f"  '{mot_original}' -> [NON CORRIGÉ] (Raison: {methode})")
        
        print("\n--- Test interactif ---")
        print("Entrez une phrase à corriger (ou 'quitter' pour arrêter):")
        while True:
            try:
                user_input = input("> ")
                if user_input.lower() == 'quitter':
                    break
                if not user_input.strip():
                    continue
                
                resultats = corrector.correct_sentence(user_input)
                for mot_original, lemme_corrige, methode in resultats:
                    if lemme_corrige and lemme_corrige.lower() != mot_original.lower().strip(string.punctuation + string.whitespace):
                        print(f"  '{mot_original}' -> '{lemme_corrige}' (Méthode: {methode})")
                    elif lemme_corrige:
                         print(f"  '{mot_original}' -> '{lemme_corrige}' [OK]")
                    else:
                        print(f"  '{mot_original}' -> [NON CORRIGÉ] (Raison: {methode})")

            except EOFError: break
            except KeyboardInterrupt: break
                
    print("\n=== FIN TEST TD5 ===")