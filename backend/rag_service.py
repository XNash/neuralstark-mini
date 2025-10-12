import logging
from typing import List, Dict, Tuple
import asyncio
from vector_store import VectorStoreService

# Try to import emergentintegrations, fall back to google-generativeai
try:
    from emergentintegrations.llm.chat import LlmChat, UserMessage
    USE_EMERGENT = True
    logger = logging.getLogger(__name__)
    logger.info("Using emergentintegrations for LLM")
except ImportError:
    import google.generativeai as genai
    USE_EMERGENT = False
    logger = logging.getLogger(__name__)
    logger.info("Using google-generativeai for LLM (emergentintegrations not available)")


class RAGService:
    """RAG service for answering queries using indexed documents with robust error handling"""
    
    def __init__(self, vector_service: VectorStoreService, db):
        self.vector_service = vector_service
        self.db = db
        self.api_key = None
        # Configuration for robustness
        self.max_retries = 3
        self.relevance_threshold = 0.3  # Filter out low-relevance chunks
        self.max_context_tokens = 8000  # Conservative estimate for context size
    
    def update_api_key(self, api_key: str):
        """Update the API key for Gemini"""
        self.api_key = api_key
    
    def _filter_relevant_docs(self, docs: List[str], metadata: List[Dict]) -> Tuple[List[str], List[Dict]]:
        """Filter documents based on relevance threshold"""
        filtered_docs = []
        filtered_metadata = []
        
        for doc, meta in zip(docs, metadata):
            relevance = meta.get('relevance_score', 0)
            if relevance >= self.relevance_threshold:
                filtered_docs.append(doc)
                filtered_metadata.append(meta)
        
        logger.info(f"Filtered {len(filtered_docs)}/{len(docs)} documents above relevance threshold {self.relevance_threshold}")
        return filtered_docs, filtered_metadata
    
    def _build_optimized_context(self, docs: List[str], metadata: List[Dict]) -> str:
        """Build optimized context from documents with proper formatting"""
        if not docs:
            return "No relevant documents found in the knowledge base."
        
        context_parts = []
        for i, (doc, meta) in enumerate(zip(docs, metadata), 1):
            source = meta.get('source', 'Unknown')
            relevance = meta.get('relevance_score', 0)
            
            # Format each document chunk with clear separation
            chunk_text = f"[Document {i}: {source} | Relevance: {relevance:.2f}]\n{doc.strip()}"
            context_parts.append(chunk_text)
        
        # Join with clear separators
        return "\n\n" + "="*80 + "\n\n".join(context_parts)
    
    async def get_response(
        self,
        query: str,
        session_id: str,
        api_key: str,
        chat_history: List[Dict] = None
    ) -> Tuple[str, List[Dict]]:
        """Get a response from the RAG agent with robust error handling and retry logic"""
        
        # Attempt with exponential backoff
        for attempt in range(self.max_retries):
            try:
                # Search for relevant documents with increased results
                relevant_docs, metadata = self.vector_service.search(query, n_results=8)
                
                if not relevant_docs:
                    # No documents found - provide helpful message
                    logger.warning(f"No relevant documents found for query: {query[:50]}...")
                    return self._handle_no_documents_found(query), []
                
                # Filter documents by relevance threshold
                filtered_docs, filtered_metadata = self._filter_relevant_docs(relevant_docs, metadata)
                
                if not filtered_docs:
                    # All documents below relevance threshold
                    logger.warning(f"All retrieved documents below relevance threshold for query: {query[:50]}...")
                    return self._handle_low_relevance(query), []
                
                # Build optimized context
                context = self._build_optimized_context(filtered_docs, filtered_metadata)
                
                # Prepare sources for response
                sources = [
                    {
                        "source": meta.get('source', 'Unknown'),
                        "chunk_index": meta.get('chunk_index', 0),
                        "relevance_score": round(meta.get('relevance_score', 0), 3)
                    }
                    for meta in filtered_metadata
                ]
                
                # Build enhanced system message with better instructions
                system_message = self._build_system_prompt(context)
                
                # Call LLM based on available library
                if USE_EMERGENT:
                    # Use emergentintegrations
                    chat = LlmChat(
                        api_key=api_key,
                        session_id=session_id,
                        system_message=system_message
                    ).with_model("gemini", "gemini-2.5-flash")
                    
                    user_message = UserMessage(text=query)
                    response = await chat.send_message(user_message)
                else:
                    # Use google-generativeai
                    genai.configure(api_key=api_key)
                    model = genai.GenerativeModel(
                        model_name='gemini-2.0-flash-exp',
                        system_instruction=system_message
                    )
                    
                    result = await asyncio.to_thread(
                        model.generate_content,
                        query
                    )
                    response = result.text
                
                logger.info(f"Successfully generated response for session {session_id} (attempt {attempt + 1})")
                return response, sources
            
            except Exception as e:
                error_str = str(e).lower()
                
                # Check if it's a quota/rate limit error
                if "quota" in error_str or "429" in error_str or "resource_exhausted" in error_str:
                    logger.error(f"API quota exceeded: {e}")
                    raise Exception(
                        "The Gemini API quota has been exceeded. Please check your API key's billing details at "
                        "https://aistudio.google.com/app/apikey or try again later. "
                        "Free tier allows 250 requests per day."
                    )
                
                # Check if it's an authentication error
                if "unauthorized" in error_str or "401" in error_str or "invalid" in error_str:
                    logger.error(f"API authentication failed: {e}")
                    raise Exception(
                        "Invalid or unauthorized API key. Please check your Gemini API key in Settings. "
                        "Get a valid key from https://aistudio.google.com/app/apikey"
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