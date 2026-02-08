"""
RAG Chatbot Module
"""
import requests
from typing import List, Optional, Any
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory
from langchain.prompts import PromptTemplate
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, AIMessage, ChatMessage
from langchain_core.callbacks.manager import CallbackManagerForLLMRun
from langchain_core.messages import BaseMessage as LangChainBaseMessage
from langchain.schema import ChatGeneration, ChatResult
from app.core.config import GROQ_API_KEY, GROQ_MODEL, RETRIEVER_K


class GroqChatModel(BaseChatModel):
    """Custom Groq chat model implementation - FREE online API, no OpenAI dependencies."""
    
    model_name: str
    api_key: str
    temperature: float = 0.7
    api_base: str = "https://api.groq.com/openai/v1"
    
    def __init__(self, model_name: str = None, api_key: str = None, temperature: float = 0.7, **kwargs):
        # Initialize fields before calling super().__init__ or pass them in
        model_name = model_name or GROQ_MODEL
        api_key = api_key or GROQ_API_KEY
        
        # In Pydantic v2 (used by recent LangChain), we must pass fields to super().__init__
        super().__init__(
            model_name=model_name, 
            api_key=api_key, 
            temperature=temperature, 
            **kwargs
        )
    
    @property
    def _llm_type(self) -> str:
        return "groq"
    
    def _generate(
        self,
        messages: List[LangChainBaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> ChatResult:
        """Generate a response from Groq API."""
        # Convert LangChain messages to OpenAI-compatible format
        formatted_messages = []
        for msg in messages:
            if isinstance(msg, HumanMessage):
                formatted_messages.append({"role": "user", "content": msg.content})
            elif isinstance(msg, AIMessage):
                formatted_messages.append({"role": "assistant", "content": msg.content})
            elif isinstance(msg, ChatMessage):
                formatted_messages.append({"role": msg.role, "content": msg.content})
            else:
                formatted_messages.append({"role": "user", "content": str(msg.content)})
        
        # Call Groq API
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model_name,
            "messages": formatted_messages,
            "temperature": self.temperature
        }
        
        if stop:
            payload["stop"] = stop
        
        response = requests.post(
            f"{self.api_base}/chat/completions",
            headers=headers,
            json=payload,
            timeout=60
        )
        
        if response.status_code != 200:
            raise ValueError(f"Groq API error: {response.status_code} - {response.text}")
        
        result = response.json()
        content = result["choices"][0]["message"]["content"]
        
        # Return LangChain message
        message = AIMessage(content=content)
        generation = ChatGeneration(message=message)
        return ChatResult(generations=[generation])


def create_chatbot(vector_store, model_name: str = GROQ_MODEL):
    """
    Create a conversational chatbot with RAG capabilities using Groq (FREE online API).
    
    Args:
        vector_store: Vector store containing document embeddings
        model_name: Name of the Groq model to use
        
    Returns:
        ConversationalRetrievalChain instance
    """
    if not GROQ_API_KEY:
        raise ValueError("GROQ_API_KEY not found. Please set it in your .env file. Get a free key from https://console.groq.com/")
    
    # Initialize Groq LLM using custom implementation
    llm = GroqChatModel(
        model_name=model_name,
        api_key=GROQ_API_KEY,
        temperature=0.7
    )
    
    # Create a retriever from the vector store
    retriever = vector_store.as_retriever(
        search_kwargs={"k": RETRIEVER_K}
    )
    
    # Custom prompt template for better responses
    custom_prompt = PromptTemplate(
        input_variables=["chat_history", "question", "context"],
        template="""You are a helpful AI assistant that answers questions based on the provided context from PDF documents.

Context from documents:
{context}

Chat history:
{chat_history}

User question: {question}

Please provide a helpful and accurate answer based on the context. If the answer is not in the context, say so politely and use your general knowledge if appropriate. Always cite which document(s) you're referencing when possible.

Answer:"""
    )
    
    # Create memory for conversation history
    memory = ConversationBufferMemory(
        memory_key="chat_history",
        return_messages=True,
        output_key="answer"
    )
    
    # Create the conversational retrieval chain
    chain = ConversationalRetrievalChain.from_llm(
        llm=llm,
        retriever=retriever,
        memory=memory,
        combine_docs_chain_kwargs={"prompt": custom_prompt},
        return_source_documents=True,
        verbose=False
    )
    
    return chain


def chat(chain, question: str, chat_history: list = None):
    """
    Process a user question and return the answer.
    
    Args:
        chain: ConversationalRetrievalChain instance
        question: User's question
        chat_history: Optional chat history (if not using chain's memory)
        
    Returns:
        Dictionary with 'answer' and 'source_documents'
    """
    if chat_history is None:
        result = chain.invoke({"question": question})
    else:
        result = chain.invoke({"question": question, "chat_history": chat_history})
    
    return {
        "answer": result["answer"],
        "source_documents": result.get("source_documents", [])
    }
