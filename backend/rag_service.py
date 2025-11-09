import logging
from typing import List, Dict, Tuple, Optional
import asyncio
from vector_store import VectorStoreService
from cerebras.cloud.sdk import Cerebras
from query_enhancer import QueryEnhancer
from reranker import Reranker

logger = logging.getLogger(__name__)


class RAGService:
    """Enhanced RAG service with query enhancement, hybrid retrieval, and reranking - FRENCH-FIRST"""
    
    def __init__(self, vector_service: VectorStoreService, db):
        self.vector_service = vector_service
        self.db = db
        self.api_key = None
        
        # Initialize OPTIMIZED components
        self.query_enhancer = QueryEnhancer()
        
        # Use optimized reranker with CamemBERT for French precision (CPU-only)
        try:
            from reranker_optimized import RerankerOptimized
            # Use CamemBERT-large for maximum French accuracy on CPU
            self.reranker = RerankerOptimized(model_name='dangvantuan/sentence-camembert-large')
            logger.info("Using CPU-OPTIMIZED CamemBERT reranker with exact match boosting + NER")
        except Exception as e:
            logger.warning(f"Could not load optimized reranker: {e}, falling back to standard")
            self.reranker = Reranker(model_name='cross-encoder/ms-marco-MiniLM-L-6-v2')
        
        # ULTRA-OPTIMIZED Configuration for CPU-only: near-instant responses (300-500ms) + precision
        self.max_retries = 3
        self.initial_retrieval_count = 10  # CPU-optimized: reduced for speed (was 12, 15, 20)
        self.variation_retrieval_count = 2  # CPU-optimized: minimal for speed (was 3, 5)
        self.final_results_count = 8  # Return top 8 after reranking
        self.min_reranker_score = -2.5  # Even stricter for meticulous precision (was -3.0)
        self.max_context_tokens = 8000
        self.prefilter_threshold = 0.20  # CPU-optimized: stricter pre-filter (was 0.25)
        
        logger.info("CPU-OPTIMIZED RAG service initialized: CamemBERT + caching + exact match boosting + NER ENABLED")
    
    def update_api_key(self, api_key: str):
        """Update the API key for Cerebras"""
        self.api_key = api_key
    
    def _detect_language(self, query: str) -> str:
        """
        Simple language detection (French as default, with English support)
        French is the PRIMARY language - defaults to 'fr'
        """
        # Count French-specific characters and common words
        french_indicators = ['à', 'é', 'è', 'ê', 'ç', 'ù', 'où', 'quoi', 'quel', 'quelle', 'qui', 'dont', 'lequel']
        text_lower = query.lower()
        
        french_count = sum(1 for indicator in french_indicators if indicator in text_lower)
        
        # Always default to French - system is French-first
        return 'fr'
    
    async def get_response(
        self,
        query: str,
        session_id: str,
        api_key: str,
        chat_history: List[Dict] = None
    ) -> Tuple[str, List[Dict], Optional[str]]:
        """
        Get a response from the RAG agent with enhanced accuracy - ALWAYS RESPONDS IN FRENCH
        
        Returns:
            - response: Generated answer (ALWAYS IN FRENCH)
            - sources: List of source documents with metadata
            - spelling_suggestion: "Did you mean...?" suggestion if applicable
        """
        
        # Detect if query is in non-French language (for adding note in response)
        french_indicators = ['à', 'é', 'è', 'ê', 'ç', 'ù', 'où', 'quoi', 'quel', 'quelle', 'qui', 'dont', 'lequel', 'pourquoi', 'comment']
        english_indicators = ['the', 'what', 'how', 'why', 'where', 'when', 'who', 'which', 'can', 'could', 'would', 'should']
        text_lower = query.lower()
        
        french_count = sum(1 for indicator in french_indicators if indicator in text_lower)
        english_count = sum(1 for indicator in english_indicators if ' ' + indicator + ' ' in ' ' + text_lower + ' ')
        
        is_non_french_query = (english_count > 0 and french_count == 0)
        logger.info(f"Query language check: French indicators={french_count}, English indicators={english_count}, Will add French-only note={is_non_french_query}")
        
        # Step 1: QUERY ENHANCEMENT - Spell correction and expansion (French-first)
        corrected_query, query_variations, spelling_suggestion = self.query_enhancer.enhance_query(
            query, detect_language='fr'  # Always use French for query enhancement
        )
        
        if spelling_suggestion:
            logger.info(f"Spelling correction applied: '{query}' -> '{spelling_suggestion}'")
        
        # Attempt with exponential backoff
        for attempt in range(self.max_retries):
            try:
                # Step 2: HYBRID RETRIEVAL - Search with multiple query variations
                all_docs = []
                all_metadata = []
                
                # Search with original corrected query (most important)
                docs, meta = self.vector_service.search(
                    corrected_query, 
                    n_results=self.initial_retrieval_count,
                    use_hybrid=True
                )
                all_docs.extend(docs)
                all_metadata.extend(meta)
                
                # Also search with top query variations (for better coverage)
                for variation in query_variations[1:min(2, len(query_variations))]:  # Only 2 best variations
                    if variation.lower() != corrected_query.lower():
                        docs_var, meta_var = self.vector_service.search(
                            variation,
                            n_results=self.variation_retrieval_count,  # Reduced to 3 for speed
                            use_hybrid=True
                        )
                        all_docs.extend(docs_var)
                        all_metadata.extend(meta_var)
                
                # Remove duplicates while preserving metadata
                unique_docs = []
                unique_metadata = []
                seen = set()
                
                for doc, meta in zip(all_docs, all_metadata):
                    doc_key = doc[:100]  # Use first 100 chars as key
                    if doc_key not in seen:
                        seen.add(doc_key)
                        unique_docs.append(doc)
                        unique_metadata.append(meta)
                
                logger.info(f"Retrieved {len(unique_docs)} unique documents from hybrid search")
                
                if not unique_docs:
                    # No documents found
                    logger.warning(f"No relevant documents found for query: {query[:50]}...")
                    response = self._handle_no_documents_found(query)
                    if is_non_french_query:
                        response += "\n\n*Note: Ce système répond uniquement en français.*"
                    return response, [], spelling_suggestion
                
                # Step 2.5: INTELLIGENT PRE-FILTERING before expensive reranking
                # Filter out clearly irrelevant docs to speed up CamemBERT reranking
                prefiltered_docs = []
                prefiltered_metadata = []
                
                for doc, meta in zip(unique_docs, unique_metadata):
                    relevance = meta.get('relevance_score', 0)
                    # Keep docs above threshold OR with high BM25/RRF scores
                    if (relevance >= self.prefilter_threshold or 
                        meta.get('bm25_score', 0) > 2.0 or 
                        meta.get('rrf_score', 0) > 0.02):
                        prefiltered_docs.append(doc)
                        prefiltered_metadata.append(meta)
                
                # Fallback: if too aggressive filtering, keep top documents
                if len(prefiltered_docs) < 5 and len(unique_docs) >= 5:
                    prefiltered_docs = unique_docs[:10]
                    prefiltered_metadata = unique_metadata[:10]
                    logger.info(f"Pre-filter too aggressive, keeping top 10 docs")
                elif prefiltered_docs:
                    logger.info(f"Pre-filtered {len(unique_docs)} -> {len(prefiltered_docs)} docs (threshold={self.prefilter_threshold})")
                else:
                    prefiltered_docs = unique_docs
                    prefiltered_metadata = unique_metadata
                
                # Step 3: OPTIMIZED RERANKING - CamemBERT + exact match boosting (on pre-filtered set)
                reranked_docs, reranked_metadata = self.reranker.rerank(
                    corrected_query,
                    prefiltered_docs,  # Use pre-filtered docs for faster reranking
                    prefiltered_metadata,
                    top_k=min(self.initial_retrieval_count, len(prefiltered_docs)),
                    enable_exact_match_boost=True  # Boost for names and data
                )
                
                # Step 4: STRICTER DYNAMIC THRESHOLD - Better precision (20th percentile)
                if reranked_metadata:
                    scores = [meta.get('reranker_score', 0.0) for meta in reranked_metadata]
                    # Use 20th percentile (stricter) for better precision on details
                    dynamic_threshold = self.reranker.compute_dynamic_threshold(scores, percentile=20)
                    
                    # Apply filter with dynamic threshold
                    filtered_docs, filtered_metadata = self.reranker.filter_by_confidence(
                        reranked_docs,
                        reranked_metadata,
                        min_score=max(self.min_reranker_score, dynamic_threshold),
                        use_dynamic_threshold=True
                    )
                else:
                    filtered_docs, filtered_metadata = reranked_docs, reranked_metadata
                
                # Take top N results
                final_docs = filtered_docs[:self.final_results_count]
                final_metadata = filtered_metadata[:self.final_results_count]
                
                if not final_docs:
                    # All documents below confidence threshold
                    logger.warning(f"All retrieved documents below confidence threshold")
                    response = self._handle_low_relevance(query)
                    if is_non_french_query:
                        response += "\n\n*Note: Ce système répond uniquement en français.*"
                    return response, [], spelling_suggestion
                
                logger.info(f"Final result set: {len(final_docs)} documents after reranking and filtering")
                
                # Step 5: BUILD CONTEXT
                context = self._build_optimized_context(final_docs, final_metadata)
                
                # Prepare sources for response
                sources = [
                    {
                        "source": meta.get('source', 'Unknown'),
                        "chunk_index": meta.get('chunk_index', 0),
                        "relevance_score": round(meta.get('relevance_score', 0), 3),
                        "reranker_score": round(meta.get('reranker_score', 0), 3),
                        "retrieval_method": meta.get('retrieval_method', 'dense')
                    }
                    for meta in final_metadata
                ]
                
                # Step 6: GENERATE RESPONSE (ALWAYS IN FRENCH)
                system_message = self._build_system_prompt(context, corrected_query, is_non_french_query)
                
                # Call Cerebras LLM with gpt-oss-120b model
                client = Cerebras(api_key=api_key)
                
                chat_completion = await asyncio.to_thread(
                    client.chat.completions.create,
                    messages=[
                        {"role": "system", "content": system_message},
                        {"role": "user", "content": corrected_query}
                    ],
                    model="gpt-oss-120b",  # Changed from llama-3.3-70b to gpt-oss-120b
                    max_completion_tokens=2048,
                    temperature=0.7,
                    top_p=1
                )
                
                response = chat_completion.choices[0].message.content
                
                # Add French-only note if query was in another language
                if is_non_french_query:
                    response += "\n\n*Note: Ce système répond uniquement en français. Si vous avez posé votre question dans une autre langue, veuillez noter que toutes les réponses sont générées en français.*"
                
                logger.info(f"Successfully generated French response for session {session_id} (attempt {attempt + 1})")
                return response, sources, spelling_suggestion
            
            except Exception as e:
                error_str = str(e).lower()
                
                # Check if it's a quota/rate limit error
                if "quota" in error_str or "429" in error_str or "resource_exhausted" in error_str or "rate" in error_str:
                    logger.error(f"API quota exceeded: {e}")
                    raise Exception(
                        "La limite de débit de l'API Cerebras a été dépassée. Veuillez réessayer plus tard ou vérifier les détails de facturation de votre clé API sur "
                        "https://cloud.cerebras.ai"
                    )
                
                # Check if it's an authentication error
                if "unauthorized" in error_str or "401" in error_str or "invalid" in error_str or "authentication" in error_str:
                    logger.error(f"API authentication failed: {e}")
                    raise Exception(
                        "Clé API invalide ou non autorisée. Veuillez vérifier votre clé API Cerebras dans les Paramètres. "
                        "Obtenez une clé valide depuis https://cloud.cerebras.ai"
                    )
                
                # For other errors, retry with exponential backoff
                if attempt < self.max_retries - 1:
                    wait_time = 2 ** attempt  # Exponential backoff: 1s, 2s, 4s
                    logger.warning(f"Error on attempt {attempt + 1}, retrying in {wait_time}s: {e}")
                    await asyncio.sleep(wait_time)
                else:
                    logger.error(f"Error in RAG service after {self.max_retries} attempts: {e}")
                    raise Exception(f"Échec de génération de réponse après {self.max_retries} tentatives: {str(e)}")
    
    def _build_optimized_context(self, docs: List[str], metadata: List[Dict]) -> str:
        """Build optimized context from documents with proper formatting"""
        if not docs:
            return "Aucun document pertinent trouvé dans la base de connaissances."
        
        context_parts = []
        for i, (doc, meta) in enumerate(zip(docs, metadata), 1):
            source = meta.get('source', 'Inconnu')
            relevance = meta.get('relevance_score', 0)
            reranker_score = meta.get('reranker_score', 0)
            method = meta.get('retrieval_method', 'N/A')
            
            # Format each document chunk with clear separation and enhanced metadata
            chunk_text = (
                f"[Document {i}: {source} | "
                f"Pertinence: {relevance:.2f} | "
                f"Reclass.: {reranker_score:.2f} | "
                f"Méthode: {method}]\n"
                f"{doc.strip()}"
            )
            context_parts.append(chunk_text)
        
        # Join with clear separators
        return "\n\n" + "="*80 + "\n\n".join(context_parts)
    
    def _build_system_prompt(self, context: str, query: str = "", is_non_french_query: bool = False) -> str:
        """Build an enhanced system prompt for better RAG accuracy - ALWAYS RESPOND IN FRENCH"""
        french_instruction = ""
        if is_non_french_query:
            french_instruction = "\n\n**LANGUE DE RÉPONSE OBLIGATOIRE**: Vous DEVEZ répondre UNIQUEMENT en français, quelle que soit la langue de la question. C'est une exigence absolue du système.\n"
        
        return f"""Vous êtes un assistant IA expert spécialisé dans la réponse aux questions basées sur le contexte documentaire fourni.

PRINCIPES FONDAMENTAUX:
1. **ADHÉRENCE STRICTE AU CONTEXTE**: Répondez UNIQUEMENT en utilisant les informations des documents fournis ci-dessous
2. **PRÉCISION AVANT TOUT**: Si le contexte manque d'informations pertinentes, indiquez explicitement : "Je n'ai pas d'information à ce sujet dans les documents indexés."
3. **PAS D'HALLUCINATION**: N'inventez jamais, ne supposez jamais et n'utilisez jamais de connaissances externes non présentes dans le contexte
4. **ATTRIBUTION DES SOURCES**: Référencez les documents spécifiques lors de la fourniture d'informations
5. **RÉPONSE EN FRANÇAIS UNIQUEMENT**: Vous devez TOUJOURS répondre en français, quelle que soit la langue de la question posée
6. **CLARTÉ**: Fournissez des réponses claires, concises et bien structurées en français
7. **ORIENTÉ VERS LES DÉTAILS**: Portez une attention particulière aux détails subtils, aux chiffres spécifiques, aux noms et aux dates dans les documents{french_instruction}
CONTEXTE DOCUMENTAIRE INDEXÉ:
{context}

DIRECTIVES DE RÉPONSE:
- Extrayez et synthétisez les informations pertinentes des documents
- Citez les sources documentaires lors de votre réponse (par ex., "Selon [Nom du Document]...")
- Si plusieurs documents contiennent des informations pertinentes, intégrez-les de manière cohérente
- Pour les questions sur des détails spécifiques (chiffres, noms, dates), soyez extrêmement précis
- Si la question contient des variations orthographiques ou des synonymes, comprenez l'intention
- Pour les questions peu claires ou ambiguës, fournissez les informations les plus pertinentes disponibles
- Maintenez un ton professionnel et utile
- **IMPORTANT**: Répondez TOUJOURS en français, même si la question est dans une autre langue

Répondez maintenant à la question de l'utilisateur en vous basant uniquement sur le contexte ci-dessus, EN FRANÇAIS."""
    
    def _handle_no_documents_found(self, query: str) -> str:
        """Handle case when no documents are found - FRENCH RESPONSE"""
        return (
            "Je m'excuse, mais je n'ai pas trouvé de documents pertinents dans la base de connaissances pour répondre à votre question. "
            "Cela pourrait signifier :\n"
            "1. Les informations que vous recherchez n'ont pas encore été indexées\n"
            "2. La requête pourrait être trop spécifique ou utiliser une terminologie différente\n"
            "3. Aucun document n'a été ajouté au système\n\n"
            "Veuillez essayer :\n"
            "- Reformuler votre question avec des mots-clés différents\n"
            "- Ajouter des documents pertinents au répertoire des fichiers\n"
            "- Utiliser le bouton 'Réindexer les documents' pour mettre à jour la base de connaissances"
        )
    
    def _handle_low_relevance(self, query: str) -> str:
        """Handle case when all documents have low relevance - FRENCH RESPONSE"""
        return (
            "J'ai trouvé quelques documents, mais aucun d'entre eux ne semble suffisamment pertinent pour votre question. "
            "Les documents indexés ne contiennent peut-être pas d'informations sur ce sujet spécifique.\n\n"
            "Veuillez essayer :\n"
            "- Reformuler votre question avec des mots-clés différents\n"
            "- Être plus spécifique ou plus général dans votre requête\n"
            "- Ajouter des documents plus pertinents au répertoire des fichiers"
        )
