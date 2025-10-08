import logging
from typing import List, Dict, Tuple
from vector_store import VectorStoreService
from emergentintegrations.llm.chat import LlmChat, UserMessage

logger = logging.getLogger(__name__)


class RAGService:
    """RAG service for answering queries using indexed documents"""
    
    def __init__(self, vector_service: VectorStoreService, db):
        self.vector_service = vector_service
        self.db = db
        self.api_key = None
    
    def update_api_key(self, api_key: str):
        """Update the API key for Gemini"""
        self.api_key = api_key
    
    async def get_response(
        self,
        query: str,
        session_id: str,
        api_key: str,
        chat_history: List[Dict] = None
    ) -> Tuple[str, List[Dict]]:
        """Get a response from the RAG agent"""
        try:
            # Search for relevant documents
            relevant_docs, metadata = self.vector_service.search(query, n_results=5)
            
            if not relevant_docs:
                # No documents found
                context = "No relevant documents found in the knowledge base."
                sources = []
            else:
                # Build context from retrieved documents
                context = "\n\n".join([
                    f"[Source: {meta.get('source', 'Unknown')}]\n{doc}"
                    for doc, meta in zip(relevant_docs, metadata)
                ])
                
                # Prepare sources for response
                sources = [
                    {
                        "source": meta.get('source', 'Unknown'),
                        "chunk_index": meta.get('chunk_index', 0),
                        "relevance_score": round(meta.get('relevance_score', 0), 3)
                    }
                    for meta in metadata
                ]
            
            # Build system message
            system_message = """You are a helpful AI assistant that answers questions based ONLY on the provided context from indexed documents.

IMPORTANT RULES:
1. Answer questions using ONLY the information from the provided context
2. If the context doesn't contain relevant information, clearly state: "I don't have information about this in the indexed documents."
3. Do not make up information or use external knowledge
4. Cite sources when providing information
5. Support both French and English queries
6. Be concise and accurate

Context from indexed documents:
---
{context}
---

Answer the user's question based on the above context."""
            
            system_message = system_message.format(context=context)
            
            # Initialize chat with Gemini
            chat = LlmChat(
                api_key=api_key,
                session_id=session_id,
                system_message=system_message
            ).with_model("gemini", "gemini-2.5-flash")
            
            # Build conversation history (last 5 messages)
            if chat_history:
                recent_history = chat_history[-5:]
                for msg in recent_history:
                    # Note: emergentintegrations manages history internally
                    # We're just using it for context here
                    pass
            
            # Send query
            user_message = UserMessage(text=query)
            response = await chat.send_message(user_message)
            
            logger.info(f"Generated response for session {session_id}")
            return response, sources
        
        except Exception as e:
            logger.error(f"Error in RAG service: {e}")
            raise Exception(f"Failed to generate response: {str(e)}")