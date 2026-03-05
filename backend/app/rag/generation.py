"""
RAG Generation Module
LLM response generation with GPT4All and OpenAI support
"""

import logging
from typing import List, Dict, Any, Optional
from abc import ABC, abstractmethod

from app.config import settings

logger = logging.getLogger(__name__)


class LLMClient(ABC):
    """Abstract base class for LLM clients"""
    
    @abstractmethod
    def generate(self, prompt: str) -> str:
        """Generate response from prompt"""
        pass


class GPT4AllClient(LLMClient):
    """GPT4All local LLM client"""
    
    def __init__(self, model_name: str = None):
        """
        Initialize GPT4All client
        
        Args:
            model_name: Name of GPT4All model to use (downloads if not cached)
        """
        try:
            from gpt4all import GPT4All
        except ImportError:
            raise ImportError("gpt4all not installed. Run: pip install gpt4all")
        
        self.model_name = model_name or settings.gpt4all_model
        
        logger.info(f"Loading GPT4All model: {self.model_name}")
        logger.info("Note: First run will download model (~4GB) to ~/.cache/gpt4all/")
        
        try:
            # Set up CUDA library paths for GPU support
            import os
            import sys
            cuda_libs = []
            site_packages = [p for p in sys.path if 'site-packages' in p]
            if site_packages:
                sp = site_packages[0]
                cuda_runtime = os.path.join(sp, 'nvidia', 'cuda_runtime', 'lib')
                cuda_blas = os.path.join(sp, 'nvidia', 'cublas', 'lib')
                if os.path.exists(cuda_runtime):
                    cuda_libs.append(cuda_runtime)
                if os.path.exists(cuda_blas):
                    cuda_libs.append(cuda_blas)
            
            if cuda_libs:
                os.environ['LD_LIBRARY_PATH'] = ':'.join(cuda_libs) + ':' + os.environ.get('LD_LIBRARY_PATH', '')
                logger.info("Set CUDA library path for GPU support")
            
            # Try GPU first, fall back to CPU if unavailable
            try:
                self.model = GPT4All(self.model_name, device='cuda')
                logger.info("GPT4All model loaded successfully with GPU acceleration")
            except (ValueError, RuntimeError) as e:
                logger.warning(f"GPU initialization failed ({str(e)}), falling back to CPU")
                self.model = GPT4All(self.model_name)
                logger.info("GPT4All model loaded successfully (CPU mode)")
        except Exception as e:
            logger.error(f"Failed to load GPT4All model: {str(e)}")
            raise
    
    def generate(self, prompt: str, max_tokens: int = 512, temperature: float = 0.7) -> str:
        """
        Generate response using GPT4All
        
        Args:
            prompt: Input prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature (0.0-1.0)
            
        Returns:
            Generated text response
        """
        try:
            logger.info(f"Generating response (max_tokens={max_tokens}, temp={temperature})")
            
            response = self.model.generate(
                prompt,
                max_tokens=max_tokens,
                temp=temperature
            )
            
            logger.info(f"Generated response ({len(response)} chars)")
            return response.strip()
            
        except Exception as e:
            logger.error(f"Generation error: {str(e)}", exc_info=True)
            raise


class OpenAIClient(LLMClient):
    """OpenAI API client (optional alternative)"""
    
    def __init__(self, api_key: str = None, model: str = None):
        """
        Initialize OpenAI client
        
        Args:
            api_key: OpenAI API key (from settings if not provided)
            model: Model name (default: gpt-3.5-turbo)
        """
        try:
            from openai import OpenAI
        except ImportError:
            raise ImportError("openai not installed. Run: pip install openai")
        
        self.api_key = api_key or settings.openai_api_key
        if not self.api_key:
            raise ValueError("OpenAI API key not provided")
        
        self.model = model or settings.openai_model
        self.client = OpenAI(api_key=self.api_key)
        
        logger.info(f"OpenAI client initialized (model={self.model})")
    
    def generate(self, prompt: str, max_tokens: int = 512, temperature: float = 0.7) -> str:
        """
        Generate response using OpenAI API
        
        Args:
            prompt: Input prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            
        Returns:
            Generated text response
        """
        try:
            logger.info(f"Calling OpenAI API (model={self.model})")
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=temperature
            )
            
            answer = response.choices[0].message.content.strip()
            logger.info(f"Received response ({len(answer)} chars)")
            return answer
            
        except Exception as e:
            logger.error(f"OpenAI API error: {str(e)}", exc_info=True)
            raise


def get_llm_client() -> LLMClient:
    """
    Get LLM client based on configuration
    
    Returns:
        Initialized LLM client (GPT4All or OpenAI)
    """
    provider = settings.llm_provider.lower()
    
    logger.info(f"Initializing LLM client: {provider}")
    
    if provider == "gpt4all":
        return GPT4AllClient()
    elif provider == "openai":
        return OpenAIClient()
    else:
        raise ValueError(f"Unknown LLM provider: {provider}. Use 'gpt4all' or 'openai'")


def construct_prompt(query: str, context_documents: List[Dict[str, Any]]) -> str:
    """
    Construct prompt with system instructions and context
    
    Args:
        query: User query
        context_documents: Retrieved documents with metadata
        
    Returns:
        Formatted prompt string
    """
    # System instructions
    system_prompt = """You are a helpful AI assistant that answers questions based ONLY on the provided context.

IMPORTANT RULES:
1. Use ONLY information from the context provided below
2. If the context doesn't contain enough information, say "I don't have enough information to answer that question based on the provided documentation."
3. Always cite which source(s) you used in your answer
4. Be concise but complete
5. Do not make up or infer information not present in the context
6. If asked about topics outside the context, politely decline and suggest what you can help with

"""
    
    # Format context
    context_text = ""
    if context_documents:
        context_text = "CONTEXT:\n\n"
        for i, doc in enumerate(context_documents, 1):
            source = doc.get("metadata", {}).get("source", "unknown")
            content = doc.get("content", "")
            confidence = doc.get("confidence", 0.0)
            
            context_text += f"[Source {i}: {source} (confidence: {confidence:.2f})]\n{content}\n\n---\n\n"
    else:
        context_text = "CONTEXT:\n\nNo relevant context found.\n\n"
    
    # User query
    user_query = f"QUESTION:\n{query}\n\nANSWER:"
    
    # Combine all parts
    full_prompt = system_prompt + context_text + user_query
    
    return full_prompt


def generate_answer(
    query: str,
    retrieved_documents: List[Dict[str, Any]],
    llm_client: Optional[LLMClient] = None,
    max_tokens: int = 512,
    temperature: float = 0.7
) -> str:
    """
    Generate answer using LLM with retrieved context
    
    Args:
        query: User query
        retrieved_documents: Documents retrieved from vector store
        llm_client: LLM client (creates default if not provided)
        max_tokens: Maximum tokens to generate
        temperature: Sampling temperature
        
    Returns:
        Generated answer text
    """
    try:
        # Initialize LLM client if not provided
        if llm_client is None:
            llm_client = get_llm_client()
        
        # Construct prompt with context
        prompt = construct_prompt(query, retrieved_documents)
        
        logger.info(f"Prompt length: {len(prompt)} chars")
        
        # Generate response
        answer = llm_client.generate(
            prompt,
            max_tokens=max_tokens,
            temperature=temperature
        )
        
        return answer
        
    except Exception as e:
        logger.error(f"Answer generation failed: {str(e)}", exc_info=True)
        return f"Error generating answer: {str(e)}"


def extract_sources(retrieved_documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Extract source information from retrieved documents
    
    Args:
        retrieved_documents: Documents with metadata
        
    Returns:
        List of source dictionaries for API response
    """
    sources = []
    for doc in retrieved_documents:
        sources.append({
            "content": doc.get("content", ""),
            "metadata": doc.get("metadata", {}),
            "confidence": doc.get("confidence", 0.0)
        })
    return sources


class PromptBuilder:
    """
    Builder class for constructing prompts for LLM generation
    Provides flexible prompt templates and construction methods
    """
    
    def __init__(self, system_prompt: Optional[str] = None):
        """
        Initialize prompt builder
        
        Args:
            system_prompt: Custom system prompt (uses default if not provided)
        """
        self.system_prompt = system_prompt or self.get_default_system_prompt()
    
    @staticmethod
    def get_default_system_prompt() -> str:
        """
        Get default system prompt with instructions
        
        Returns:
            Default system prompt string
        """
        return """You are a helpful AI assistant. Answer the user's question based ONLY on the provided context.

IMPORTANT RULES:
1. Only use information from the provided context
2. If the context doesn't contain enough information, say "I don't have enough information to answer that"
3. Cite sources when possible (e.g., "According to [source]...")
4. Be concise and accurate
5. Do not infer or assume information beyond what's explicitly stated

"""
    
    def get_system_prompt(self) -> str:
        """
        Get the current system prompt
        
        Returns:
            System prompt string
        """
        return self.system_prompt
    
    def build_prompt(self, query: str, context: str) -> str:
        """
        Build prompt with query and context
        
        Args:
            query: User query
            context: Context text
            
        Returns:
            Complete prompt string
        """
        prompt = self.system_prompt
        
        if context and context.strip():
            prompt += f"\nCONTEXT:\n{context}\n\n"
        else:
            prompt += "\nCONTEXT:\nNo relevant context found.\n\n"
        
        prompt += f"QUESTION:\n{query}\n\nANSWER:"
        
        return prompt
    
    def build_prompt_with_sources(
        self,
        query: str,
        retrieved_docs: List[Dict[str, Any]]
    ) -> str:
        """
        Build prompt with structured source information
        
        Args:
            query: User query
            retrieved_docs: List of retrieved documents with metadata
            
        Returns:
            Complete prompt string with sources
        """
        prompt = self.system_prompt
        
        # Add context with sources
        if retrieved_docs:
            prompt += "\nCONTEXT:\n\n"
            for i, doc in enumerate(retrieved_docs, 1):
                source = doc.get("source", "unknown")
                content = doc.get("content", "")
                similarity = doc.get("similarity", 0.0)
                
                prompt += f"[Source {i}: {source} (relevance: {similarity:.2f})]\n"
                prompt += f"{content}\n\n"
                prompt += "---\n\n"
        else:
            prompt += "\nCONTEXT:\nNo relevant context found.\n\n"
        
        prompt += f"QUESTION:\n{query}\n\nANSWER:"
        
        return prompt

