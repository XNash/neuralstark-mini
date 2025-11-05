import logging
from typing import List, Tuple, Optional
import re
from spellchecker import SpellChecker
from rapidfuzz import fuzz, process
import nltk
from nltk.corpus import wordnet

logger = logging.getLogger(__name__)


class QueryEnhancer:
    """Enhanced query processing with spell correction, expansion, and fuzzy matching - French-first"""
    
    def __init__(self):
        # Initialize spell checker (French as primary language)
        self.spell_checker_fr = SpellChecker(language='fr')
        self.spell_checker_en = SpellChecker(language='en')
        
        # Download NLTK data if not present (for synonyms)
        try:
            nltk.data.find('corpora/wordnet.zip')
        except LookupError:
            try:
                nltk.download('wordnet', quiet=True)
                nltk.download('omw-1.4', quiet=True)
            except Exception as e:
                logger.warning(f"Could not download NLTK data: {e}")
        
        # Common technical terms that shouldn't be spell-checked
        self.technical_terms = {
            'api', 'apis', 'pdf', 'pdfs', 'ceo', 'cto', 'cfo', 
            'sql', 'nosql', 'mongodb', 'chromadb', 'rag',
            'ai', 'ml', 'llm', 'nlp', 'ocr', 'url', 'urls',
            # French technical terms
            'pdg', 'dg', 'drh', 'daf', 'dsi', 'pme', 'sa', 'sarl'
        }
        
        # Common abbreviation expansions (French-first with English support)
        self.abbreviations = {
            # French abbreviations (primary)
            'pdg': 'président-directeur général',
            'dg': 'directeur général',
            'drh': 'directeur des ressources humaines',
            'daf': 'directeur administratif et financier',
            'dsi': 'directeur des systèmes d\'information',
            'dag': 'directeur administratif général',
            'ca': 'chiffre d\'affaires',
            'tva': 'taxe sur la valeur ajoutée',
            'pme': 'petite et moyenne entreprise',
            'tpe': 'très petite entreprise',
            'eti': 'entreprise de taille intermédiaire',
            'sa': 'société anonyme',
            'sarl': 'société à responsabilité limitée',
            'sas': 'société par actions simplifiée',
            'eurl': 'entreprise unipersonnelle à responsabilité limitée',
            'sce': 'société coopérative européenne',
            'rh': 'ressources humaines',
            'etc': 'et cetera',
            'svp': 's\'il vous plaît',
            'nb': 'nota bene',
            'cf': 'confer',
            'vs': 'versus',
            # English abbreviations (secondary support)
            'ceo': 'chief executive officer',
            'cto': 'chief technology officer',
            'cfo': 'chief financial officer',
            'vp': 'vice president',
            'hr': 'human resources',
            'it': 'information technology',
            'roi': 'return on investment',
            'kpi': 'key performance indicator',
        }
        
        logger.info("Query enhancer initialized with French-first language support, spell checking and expansion capabilities")
    
    def enhance_query(self, query: str, detect_language: str = 'fr') -> Tuple[str, List[str], Optional[str]]:
        """
        Enhance query with spell correction, expansion, and normalization
        DEFAULT LANGUAGE: French (fr)
        
        Returns:
            - corrected_query: Auto-corrected query
            - expanded_queries: List of query variations for search
            - suggestion: "Did you mean...?" suggestion if corrections were made
        """
        if not query or not query.strip():
            return query, [query], None
        
        # Step 1: Normalize query
        normalized_query = self._normalize_query(query)
        
        # Step 2: Detect and correct spelling (defaults to French)
        corrected_query, corrections_made = self._correct_spelling(normalized_query, detect_language)
        
        # Step 3: Create suggestion if corrections were made
        suggestion = None
        if corrections_made and corrected_query.lower() != normalized_query.lower():
            suggestion = corrected_query
        
        # Step 4: Expand query with synonyms and related terms
        expanded_queries = self._expand_query(corrected_query, detect_language)
        
        # Step 5: Add abbreviation expansions (French-first)
        expanded_queries = self._expand_abbreviations(expanded_queries)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_queries = []
        for q in expanded_queries:
            q_lower = q.lower()
            if q_lower not in seen:
                seen.add(q_lower)
                unique_queries.append(q)
        
        logger.info(f"Query enhancement (French-first): '{query}' -> {len(unique_queries)} variations")
        if suggestion:
            logger.info(f"Spelling suggestion: '{suggestion}'")
        
        return corrected_query, unique_queries, suggestion
    
    def _normalize_query(self, query: str) -> str:
        """Normalize query while preserving important punctuation"""
        # Remove extra whitespace
        query = ' '.join(query.split())
        
        # Preserve question marks and important punctuation
        query = re.sub(r'[!]+', '!', query)
        query = re.sub(r'[?]+', '?', query)
        query = re.sub(r'[.]+', '.', query)
        
        return query.strip()
    
    def _correct_spelling(self, query: str, language: str = 'fr') -> Tuple[str, bool]:
        """
        Correct spelling mistakes in the query
        DEFAULT LANGUAGE: French (fr)
        
        Returns:
            - corrected_query: Query with corrected spelling
            - corrections_made: True if any corrections were made
        """
        # Select appropriate spell checker (French as default)
        spell_checker = self.spell_checker_fr if language == 'fr' else self.spell_checker_en
        
        # Tokenize query
        words = query.split()
        corrected_words = []
        corrections_made = False
        
        for word in words:
            # Preserve original if it's a number, very short, or technical term
            word_lower = word.lower()
            if (len(word) <= 2 or 
                word.isdigit() or 
                word_lower in self.technical_terms or
                not word.isalpha()):
                corrected_words.append(word)
                continue
            
            # Check if word is misspelled
            if word_lower in spell_checker:
                # Word is correct
                corrected_words.append(word)
            else:
                # Word might be misspelled - get correction
                correction = spell_checker.correction(word_lower)
                
                if correction and correction != word_lower:
                    # Use correction but preserve original case pattern
                    if word.isupper():
                        corrected_words.append(correction.upper())
                    elif word[0].isupper():
                        corrected_words.append(correction.capitalize())
                    else:
                        corrected_words.append(correction)
                    corrections_made = True
                    logger.debug(f"Spelling correction ({language}): '{word}' -> '{correction}'")
                else:
                    # Keep original if no good correction found
                    corrected_words.append(word)
        
        corrected_query = ' '.join(corrected_words)
        return corrected_query, corrections_made
    
    def _expand_query(self, query: str, language: str = 'fr') -> List[str]:
        """
        Expand query with synonyms and related terms
        Note: WordNet is primarily for English; French expansion limited
        
        Returns list of query variations
        """
        variations = [query]
        
        # Only expand English queries with WordNet (WordNet has limited French support)
        if language != 'en':
            return variations
        
        words = query.lower().split()
        
        # Get synonyms for each content word (skip very common words)
        stop_words = {'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been',
                      'what', 'which', 'who', 'where', 'when', 'how', 'why',
                      'do', 'does', 'did', 'have', 'has', 'had', 'can', 'could',
                      'will', 'would', 'should', 'may', 'might', 'must'}
        
        synonym_map = {}
        for word in words:
            if word in stop_words or len(word) <= 2:
                continue
            
            synonyms = self._get_synonyms(word)
            if synonyms:
                synonym_map[word] = synonyms[:3]  # Limit to top 3 synonyms
        
        # Create variations by replacing words with synonyms
        if synonym_map:
            for word, synonyms in synonym_map.items():
                for synonym in synonyms:
                    # Create variation by replacing the word
                    variation = query.lower().replace(word, synonym)
                    if variation != query.lower():
                        variations.append(variation)
        
        return variations
    
    def _get_synonyms(self, word: str) -> List[str]:
        """Get synonyms for a word using WordNet"""
        synonyms = set()
        
        try:
            for syn in wordnet.synsets(word):
                for lemma in syn.lemmas():
                    synonym = lemma.name().replace('_', ' ')
                    if synonym.lower() != word.lower():
                        synonyms.add(synonym.lower())
        except Exception as e:
            logger.debug(f"Error getting synonyms for '{word}': {e}")
        
        return list(synonyms)
    
    def _expand_abbreviations(self, queries: List[str]) -> List[str]:
        """Expand known abbreviations in queries (French-first)"""
        expanded = list(queries)  # Copy original queries
        
        for query in queries:
            query_lower = query.lower()
            
            for abbrev, expansion in self.abbreviations.items():
                # Check if abbreviation exists as whole word
                pattern = r'\b' + re.escape(abbrev) + r'\b'
                if re.search(pattern, query_lower):
                    # Create variation with expansion
                    expanded_query = re.sub(pattern, expansion, query_lower, flags=re.IGNORECASE)
                    if expanded_query not in [q.lower() for q in expanded]:
                        expanded.append(expanded_query)
        
        return expanded
    
    def fuzzy_match_entities(self, query: str, entity_list: List[str], threshold: int = 80) -> List[Tuple[str, int]]:
        """
        Fuzzy match query against a list of entities (e.g., document names, product names)
        
        Returns list of (entity, score) tuples sorted by score
        """
        if not query or not entity_list:
            return []
        
        # Use rapidfuzz for fast fuzzy matching
        matches = process.extract(
            query,
            entity_list,
            scorer=fuzz.WRatio,  # Weighted ratio for better matching
            limit=10,
            score_cutoff=threshold
        )
        
        results = [(match[0], match[1]) for match in matches]
        logger.debug(f"Fuzzy matching '{query}': found {len(results)} matches above {threshold}%")
        
        return results
