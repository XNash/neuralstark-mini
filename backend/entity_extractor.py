import logging
import re
from typing import List, Dict, Set, Tuple
import spacy
from collections import defaultdict

logger = logging.getLogger(__name__)


class EntityExtractor:
    """Extract and preserve named entities and data patterns for precise RAG"""
    
    def __init__(self, enable_ner: bool = True):
        """Initialize with NER ENABLED for maximum precision on French text"""
        # LAZY LOADING: Only load spaCy when needed to save memory
        self.nlp = None
        self.enable_ner = enable_ner
        self._ner_attempted = False
        
        if enable_ner:
            self._load_ner_model()
        else:
            logger.info("Entity extractor initialized (NER disabled for memory optimization)")
        
        # Data patterns for precise extraction (French-optimized)
        self.patterns = {
            'email': re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),
            'phone': re.compile(r'(?:\+33|0)[1-9](?:[\s.-]?\d{2}){4}'),
            'url': re.compile(r'https?://(?:www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b(?:[-a-zA-Z0-9()@:%_\+.~#?&/=]*)'),
            'postal_code': re.compile(r'\b\d{5}\b'),
            'siret': re.compile(r'\b\d{14}\b'),
            'siren': re.compile(r'\b\d{9}\b'),
            'reference': re.compile(r'\b[A-Z]{2,4}[-_]?\d{3,8}\b'),
            'code': re.compile(r'\b[A-Z0-9]{6,12}\b'),
            'date_fr': re.compile(r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b'),
            'amount': re.compile(r'\b\d+(?:[.,]\d{1,2})?\s?(?:€|EUR|euros?)\b', re.IGNORECASE),
            'percentage': re.compile(r'\b\d+(?:[.,]\d{1,2})?\s?%\b'),
            # Additional French patterns for better precision
            'tva': re.compile(r'\bFR\s?\d{11}\b', re.IGNORECASE),  # French VAT number
            'iban': re.compile(r'\bFR\d{2}\s?\d{4}\s?\d{4}\s?\d{4}\s?\d{4}\s?\d{4}\s?\d{3}\b', re.IGNORECASE),
            'number': re.compile(r'\b\d+(?:[.,]\d+)?\b'),  # General numbers for exact matching
        }
        
        logger.info(f"Entity extractor initialized with French patterns (NER enabled={enable_ner})")
    
    def _load_ner_model(self):
        """Lazy load spaCy NER model - CPU-OPTIMIZED (small model for speed)"""
        if self._ner_attempted:
            return
        
        self._ner_attempted = True
        try:
            # Try SMALL model FIRST for CPU performance (15MB, très rapide)
            try:
                self.nlp = spacy.load('fr_core_news_sm')
                # Disable unused pipes for CPU speed
                self.nlp.disable_pipes('parser')  # Keep only NER and basic processing
                logger.info("Loaded lightweight French spaCy model: fr_core_news_sm (CPU-optimized)")
                return
            except:
                logger.info("fr_core_news_sm not found, attempting to download...")
                import subprocess
                subprocess.run(['python', '-m', 'spacy', 'download', 'fr_core_news_sm'], check=False)
                try:
                    self.nlp = spacy.load('fr_core_news_sm')
                    self.nlp.disable_pipes('parser')
                    logger.info("Downloaded and loaded fr_core_news_sm (CPU-optimized)")
                    return
                except:
                    pass
            
            # Fallback to medium model if small not available
            try:
                self.nlp = spacy.load('fr_core_news_md')
                self.nlp.disable_pipes('parser')
                logger.info("Loaded French spaCy model: fr_core_news_md")
                return
            except:
                pass
            
            logger.warning("No French spaCy model available, NER disabled (regex patterns still active)")
        except Exception as e:
            logger.error(f"Failed to load spaCy model: {e}")
            self.nlp = None
    
    def extract_entities(self, text: str) -> Dict[str, List[str]]:
        """Extract named entities and data patterns from text (CPU-optimized)"""
        entities = defaultdict(list)
        
        if not text or not text.strip():
            return dict(entities)
        
        # Extract using spaCy NER (CPU-optimized with text truncation)
        if self.nlp and self.enable_ner:
            try:
                # CPU optimization: Limit text length for fast processing
                max_length = 20000  # Reduced from 50000 for CPU speed
                doc = self.nlp(text[:max_length])
                
                for ent in doc.ents:
                    entity_type = ent.label_
                    entity_text = ent.text.strip()
                    
                    # Map spaCy labels to our categories
                    if entity_type in ['PER', 'PERSON']:
                        entities['person'].append(entity_text)
                    elif entity_type in ['ORG', 'ORGANIZATION']:
                        entities['organization'].append(entity_text)
                    elif entity_type in ['LOC', 'LOCATION', 'GPE']:
                        entities['location'].append(entity_text)
                    elif entity_type in ['DATE']:
                        entities['date'].append(entity_text)
                    elif entity_type in ['MONEY']:
                        entities['money'].append(entity_text)
                    else:
                        entities['misc'].append(entity_text)
            except Exception as e:
                logger.error(f"Error in spaCy NER: {e}")
        
        # Extract using regex patterns (always active, very fast)
        for pattern_name, pattern in self.patterns.items():
            matches = pattern.findall(text)
            if matches:
                entities[pattern_name].extend(matches)
        
        # Deduplicate while preserving order
        for key in entities:
            entities[key] = list(dict.fromkeys(entities[key]))
        
        return dict(entities)
    
    def find_exact_matches(self, query: str, text: str) -> List[Tuple[str, int]]:
        """Find exact matches of query entities in text - CRITICAL for detail precision"""
        exact_matches = []
        
        # Extract entities from query
        query_entities = self.extract_entities(query)
        
        # Find exact matches in text
        text_lower = text.lower()
        
        for entity_type, entity_list in query_entities.items():
            for entity in entity_list:
                entity_lower = entity.lower()
                pos = text_lower.find(entity_lower)
                if pos != -1:
                    exact_matches.append((entity, pos))
                    logger.debug(f"Exact match found: '{entity}' (type: {entity_type}) at position {pos}")
        
        return exact_matches
    
    def compute_entity_overlap(self, query: str, text: str) -> float:
        """Compute entity overlap score (0-1) - Higher = more precision on details"""
        query_entities = self.extract_entities(query)
        
        # Flatten all query entities
        all_query_entities = []
        for entity_list in query_entities.values():
            all_query_entities.extend(entity_list)
        
        if not all_query_entities:
            return 0.0
        
        # Count how many query entities appear in text
        text_lower = text.lower()
        matches = 0
        
        for entity in all_query_entities:
            if entity.lower() in text_lower:
                matches += 1
        
        # Return overlap ratio
        overlap_score = matches / len(all_query_entities)
        
        if overlap_score > 0:
            logger.debug(f"Entity overlap: {matches}/{len(all_query_entities)} = {overlap_score:.2f}")
        
        return overlap_score
    
    def enhance_chunk_metadata(self, text: str, metadata: Dict) -> Dict:
        """Enhance chunk metadata with extracted entities for better retrieval"""
        entities = self.extract_entities(text)
        
        # Add entity counts
        metadata['entity_counts'] = {k: len(v) for k, v in entities.items()}
        metadata['total_entities'] = sum(metadata['entity_counts'].values())
        
        # Store important entities (top 5 of each type)
        metadata['persons'] = entities.get('person', [])[:5]
        metadata['organizations'] = entities.get('organization', [])[:5]
        metadata['locations'] = entities.get('location', [])[:5]
        metadata['emails'] = entities.get('email', [])
        metadata['phones'] = entities.get('phone', [])
        metadata['references'] = entities.get('reference', [])
        metadata['amounts'] = entities.get('amount', [])
        metadata['dates'] = entities.get('date_fr', [])
        
        return metadata
    
    def extract_keyphrases(self, text: str, max_phrases: int = 10) -> List[str]:
        """Extract key phrases from text for indexing (CPU-optimized)"""
        keyphrases = []
        
        if not self.nlp or not text:
            return keyphrases
        
        try:
            # CPU optimization: Limit text length
            doc = self.nlp(text[:5000])  # Reduced from 10000 for CPU
            
            # Extract noun phrases
            for chunk in doc.noun_chunks:
                phrase = chunk.text.strip()
                if len(phrase) > 3:  # Minimum length
                    keyphrases.append(phrase)
            
            # Extract named entities
            for ent in doc.ents:
                keyphrases.append(ent.text.strip())
            
            # Deduplicate and limit
            keyphrases = list(dict.fromkeys(keyphrases))[:max_phrases]
        except Exception as e:
            logger.error(f"Error extracting keyphrases: {e}")
        
        return keyphrases
