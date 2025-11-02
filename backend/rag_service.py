import logging
from typing import List, Dict, Tuple, Optional
import asyncio
from vector_store import VectorStoreService
from cerebras.cloud.sdk import Cerebras
from query_enhancer import QueryEnhancer
from reranker import Reranker

logger = logging.getLogger(__name__)


class RAGService:
    """Enhanced RAG service with query enhancement, hybrid retrieval, and reranking"""
    
    def __init__(self, vector_service: VectorStoreService, db):
        self.vector_service = vector_service
        self.db = db
        self.api_key = None
        
        # Initialize enhanced components
        self.query_enhancer = QueryEnhancer()
        self.reranker = Reranker(model_name='cross-encoder/ms-marco-MiniLM-L-6-v2')
        
        # Configuration for robustness
        self.max_retries = 3
        self.initial_retrieval_count = 20  # Retrieve more candidates for reranking
        self.final_results_count = 8  # Return top 8 after reranking
        self.min_reranker_score = -5.0  # Dynamic threshold (will be computed)
        self.max_context_tokens = 8000
        
        logger.info("Enhanced RAG service initialized with query enhancement and reranking")
    
    def update_api_key(self, api_key: str):
        """Update the API key for Cerebras"""
        self.api_key = api_key
    
    def _detect_language(self, query: str) -> str:
        """Simple language detection (English or French)"""
        # Count French-specific characters and common words
        french_indicators = ['à', 'é', 'è', 'ê', 'ç', 'ù', 'où', 'quoi', 'quel', 'quelle']
        text_lower = query.lower()
        
        french_count = sum(1 for indicator in french_indicators if indicator in text_lower)
        
        return 'fr' if french_count > 0 else 'en'
    
    async def get_response(
        self,
        query: str,
        session_id: str,
        api_key: str,
        chat_history: List[Dict] = None
    ) -> Tuple[str, List[Dict], Optional[str]]:
        """
        Get a response from the RAG agent with enhanced accuracy
        
        Returns:
            - response: Generated answer
            - sources: List of source documents with metadata
            - spelling_suggestion: "Did you mean...?" suggestion if applicable
        """
        
        # Detect language for better processing
        language = self._detect_language(query)
        logger.info(f"Detected language: {language}")
        
        # Step 1: QUERY ENHANCEMENT - Spell correction and expansion
        corrected_query, query_variations, spelling_suggestion = self.query_enhancer.enhance_query(
            query, detect_language=language
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
                for variation in query_variations[1:min(3, len(query_variations))]:
                    if variation.lower() != corrected_query.lower():
                        docs_var, meta_var = self.vector_service.search(
                            variation,
                            n_results=5,  # Fewer results from variations
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
                    return self._handle_no_documents_found(query), [], spelling_suggestion
                
                # Step 3: RERANKING - Use cross-encoder for precise relevance
                reranked_docs, reranked_metadata = self.reranker.rerank(
                    corrected_query,
                    unique_docs,
                    unique_metadata,
                    top_k=self.initial_retrieval_count
                )
                
                # Step 4: DYNAMIC THRESHOLD - Filter by reranker confidence
                if reranked_metadata:
                    scores = [meta.get('reranker_score', 0.0) for meta in reranked_metadata]
                    dynamic_threshold = self.reranker.compute_dynamic_threshold(scores, percentile=30)
                    
                    # Apply filter
                    filtered_docs, filtered_metadata = self.reranker.filter_by_confidence(
                        reranked_docs,
                        reranked_metadata,
                        min_score=max(self.min_reranker_score, dynamic_threshold)
                    )
                else:
                    filtered_docs, filtered_metadata = reranked_docs, reranked_metadata
                
                # Take top N results
                final_docs = filtered_docs[:self.final_results_count]
                final_metadata = filtered_metadata[:self.final_results_count]
                
                if not final_docs:
                    # All documents below confidence threshold
                    logger.warning(f"All retrieved documents below confidence threshold")
                    return self._handle_low_relevance(query), [], spelling_suggestion
                
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
                
                # Step 6: GENERATE RESPONSE
                system_message = self._build_system_prompt(context, corrected_query)
                
                # Call Cerebras LLM
                client = Cerebras(api_key=api_key)
                
                chat_completion = await asyncio.to_thread(
                    client.chat.completions.create,
                    messages=[
                        {"role": "system", "content": system_message},
                        {"role": "user", "content": corrected_query}
                    ],
                    model="llama-3.3-70b",
                    max_completion_tokens=2048,
                    temperature=0.7,
                    top_p=1
                )
                
                response = chat_completion.choices[0].message.content
                
                logger.info(f"Successfully generated response for session {session_id} (attempt {attempt + 1})")
                return response, sources, spelling_suggestion
            
            except Exception as e:
                error_str = str(e).lower()
                
                # Check if it's a quota/rate limit error
                if "quota" in error_str or "429" in error_str or "resource_exhausted" in error_str or "rate" in error_str:
                    logger.error(f"API quota exceeded: {e}")
                    raise Exception(
                        "The Cerebras API rate limit has been exceeded. Please try again later or check your API key's billing details at "
                        "https://cloud.cerebras.ai"
                    )
                
                # Check if it's an authentication error
                if "unauthorized" in error_str or "401" in error_str or "invalid" in error_str or "authentication" in error_str:
                    logger.error(f"API authentication failed: {e}")
                    raise Exception(
                        "Invalid or unauthorized API key. Please check your Cerebras API key in Settings. "
                        "Get a valid key from https://cloud.cerebras.ai"
                    )
                
                # For other errors, retry with exponential backoff
                if attempt < self.max_retries - 1:
                    wait_time = 2 ** attempt  # Exponential backoff: 1s, 2s, 4s
                    logger.warning(f"Error on attempt {attempt + 1}, retrying in {wait_time}s: {e}")
                    await asyncio.sleep(wait_time)
                else:
                    logger.error(f"Error in RAG service after {self.max_retries} attempts: {e}")
                    raise Exception(f"Failed to generate response after {self.max_retries} attempts: {str(e)}")
                
                # Call Cerebras LLM
                client = Cerebras(api_key=api_key)
                
                # Create chat completion with Cerebras
                chat_completion = await asyncio.to_thread(
                    client.chat.completions.create,
                    messages=[
                        {"role": "system", "content": system_message},
                        {"role": "user", "content": query}
                    ],
                    model="gpt-oss-120b",
                    max_completion_tokens=2048,
                    temperature=0.7,
                    top_p=1
                )
                
                response = chat_completion.choices[0].message.content
                
                logger.info(f"Successfully generated response for session {session_id} (attempt {attempt + 1})")
                return response, sources
            
            except Exception as e:
                error_str = str(e).lower()
                
                # Check if it's a quota/rate limit error
                if "quota" in error_str or "429" in error_str or "resource_exhausted" in error_str or "rate" in error_str:
                    logger.error(f"API quota exceeded: {e}")
                    raise Exception(
                        "The Cerebras API rate limit has been exceeded. Please try again later or check your API key's billing details at "
                        "https://cloud.cerebras.ai"
                    )
                
                # Check if it's an authentication error
                if "unauthorized" in error_str or "401" in error_str or "invalid" in error_str or "authentication" in error_str:
                    logger.error(f"API authentication failed: {e}")
                    raise Exception(
                        "Invalid or unauthorized API key. Please check your Cerebras API key in Settings. "
                        "Get a valid key from https://cloud.cerebras.ai"
                    )
                
                # For other errors, retry with exponential backoff
                if attempt < self.max_retries - 1:
                    wait_time = 2 ** attempt  # Exponential backoff: 1s, 2s, 4s
                    logger.warning(f"Error on attempt {attempt + 1}, retrying in {wait_time}s: {e}")
                    await asyncio.sleep(wait_time)
                else:
                    logger.error(f"Error in RAG service after {self.max_retries} attempts: {e}")
                    raise Exception(f"Failed to generate response after {self.max_retries} attempts: {str(e)}")
    
    def _build_system_prompt(self, context: str) -> str:
        """Build an enhanced system prompt for better RAG accuracy"""
        return f"""You are an expert AI assistant specialized in answering questions based on provided document context.

CORE PRINCIPLES:
1. **STRICT CONTEXT ADHERENCE**: Answer ONLY using information from the provided documents below
2. **ACCURACY FIRST**: If the context lacks relevant information, explicitly state: "I don't have information about this in the indexed documents."
3. **NO HALLUCINATION**: Never invent, assume, or use external knowledge not present in the context
4. **SOURCE ATTRIBUTION**: Reference specific documents when providing information
5. **MULTILINGUAL SUPPORT**: Handle both English and French queries naturally
6. **CLARITY**: Provide clear, concise, and well-structured answers

INDEXED DOCUMENT CONTEXT:
{context}

RESPONSE GUIDELINES:
- Extract and synthesize relevant information from the documents
- Cite document sources when answering (e.g., "According to [Document Name]...")
- If multiple documents contain relevant info, integrate them coherently
- For unclear or ambiguous queries, ask for clarification
- Maintain professional and helpful tone
- Preserve the language of the query in your response when appropriate

Now answer the user's question based solely on the above context."""
    
    def _handle_no_documents_found(self, query: str) -> str:
        """Handle case when no documents are found"""
        return (
            "I apologize, but I couldn't find any relevant documents in the knowledge base to answer your question. "
            "This could mean:\n"
            "1. The information you're looking for hasn't been indexed yet\n"
            "2. The query might be too specific or use different terminology\n"
            "3. No documents have been added to the system\n\n"
            "Please try:\n"
            "- Rephrasing your question with different keywords\n"
            "- Adding relevant documents to the files directory\n"
            "- Using the 'Reindex Documents' button to update the knowledge base"
        )
    
    def _handle_low_relevance(self, query: str) -> str:
        """Handle case when all documents have low relevance"""
        return (
            "I found some documents, but none of them appear to be sufficiently relevant to your question. "
            "The indexed documents may not contain information about this specific topic.\n\n"
            "Please try:\n"
            "- Rephrasing your question with different keywords\n"
            "- Being more specific or more general in your query\n"
            "- Adding more relevant documents to the files directory"
        )