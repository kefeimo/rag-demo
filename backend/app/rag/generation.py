"""
RAG Generation Module
LLM response generation with GPT4All and OpenAI support
"""

import logging
from typing import List, Dict, Any, Optional
from abc import ABC, abstractmethod

from langchain_core.prompts import PromptTemplate

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
    # Determine the documentation domain based on collection name
    collection_name = settings.chroma_collection_name.lower()
    
    if "visa" in collection_name or "vcc" in collection_name or "chart" in collection_name:
        domain = "vcc"
    elif "fastapi" in collection_name:
        domain = "fastapi"
    else:
        domain = "general"
    
    # Use PromptBuilder with domain-specific configuration
    prompt_builder = PromptBuilder(domain=domain)
    
    # Build prompt with sources
    full_prompt = prompt_builder.build_prompt_with_sources(
        query=query,
        retrieved_docs=[
            {
                "source": doc.get("metadata", {}).get("source", "unknown"),
                "content": doc.get("content", ""),
                "similarity": doc.get("confidence", 0.0)
            }
            for doc in context_documents
        ]
    )
    
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
        logger.info(f"Prompt preview (first 2000 chars):\n{prompt[:2000]}")
        logger.info(f"Prompt preview (last 500 chars):\n...{prompt[-500:]}")
        
        # Generate response
        answer = llm_client.generate(
            prompt,
            max_tokens=max_tokens,
            temperature=temperature
        )
        
        return answer
        
    except Exception as e:
        logger.error(f"Answer generation failed: {str(e)}", exc_info=True)
        
        # Attempt fallback to GPT4All if OpenAI fails
        if settings.llm_provider.lower() == "openai":
            logger.warning("⚠️ OpenAI failed, attempting fallback to GPT4All (CPU)...")
            try:
                fallback_client = GPT4AllClient()
                prompt = construct_prompt(query, retrieved_documents)
                answer = fallback_client.generate(prompt, max_tokens=max_tokens, temperature=temperature)
                logger.info("✅ Fallback to GPT4All successful")
                return f"⚠️ Warning: OpenAI API failed, using local GPT4All fallback.\n\n{answer}"
            except Exception as fallback_error:
                logger.error(f"Fallback to GPT4All also failed: {str(fallback_error)}")
                return f"Error: Both OpenAI and GPT4All failed. OpenAI error: {str(e)}, GPT4All error: {str(fallback_error)}"
        
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
    
    # Domain configurations
    DOMAIN_CONFIGS = {
        "vcc": {
            "domain": "Visa Chart Components (VCC)",
            "domain_topics": "chart types, accessibility features, data props, API usage, or integration guides",
            "known_acronyms": "  - VCC = Visa Chart Components\n  - WCAG = Web Content Accessibility Guidelines\n  - a11y = accessibility",
            "domain_guidance": "- VCC is a charting library focused on accessibility\n- When discussing charts, consider accessibility features\n- Props and interfaces follow TypeScript conventions"
        },
        "fastapi": {
            "domain": "FastAPI web framework",
            "domain_topics": "path operations, dependencies, middleware, or deployment",
            "known_acronyms": "  - API = Application Programming Interface\n  - ASGI = Asynchronous Server Gateway Interface\n  - ORM = Object-Relational Mapping",
            "domain_guidance": "- FastAPI is a modern Python web framework\n- Path operations use decorators (@app.get, @app.post)\n- Type hints are essential for automatic validation"
        },
        "general": {
            "domain": "technical documentation",
            "domain_topics": "specific features or concepts",
            "known_acronyms": "  - Common technical abbreviations may be used",
            "domain_guidance": "- Focus on providing accurate technical information\n- Reference documentation sections when available"
        }
    }
    
    def __init__(self, domain: str = "general"):
        """
        Initialize prompt builder with LangChain PromptTemplate
        
        Args:
            domain: Domain context for prompt customization (vcc, fastapi, general)
        """
        self.domain = domain
        self.domain_config = self.DOMAIN_CONFIGS.get(domain, self.DOMAIN_CONFIGS["general"])
        self.prompt_template = self._create_prompt_template()
    
    def _create_prompt_template(self) -> PromptTemplate:
        """
        Create LangChain PromptTemplate with domain-specific customization
        
        Returns:
            LangChain PromptTemplate instance
        """
        template = """You are a helpful AI assistant specialized in {domain}. Answer the user's question based on the provided context.

IMPORTANT RULES:
1. Use the information from the provided context to answer the question
2. If you see code examples, usage patterns, or component descriptions in the context, use them to explain how to accomplish the user's goal
3. Code snippets may contain placeholders like {{...}} or {{data}} - these are intentional and show where users should insert their own values
4. Cite sources when possible (e.g., "According to the documentation...")
5. Be helpful and provide actionable information when the context contains relevant examples or descriptions
6. Only say you don't have enough information if the context is truly unrelated to the question

QUERY UNDERSTANDING:
- If the query contains minor spelling variations or typos, try to understand the intent from context
- Consider common acronyms and abbreviations: {known_acronyms}
- Look for semantically similar terms in the context even if exact spelling differs
- If you recognize what the user is asking about despite minor differences, provide the answer

DOMAIN-SPECIFIC GUIDANCE:
{domain_guidance}

{context}

QUESTION:
{query}

ANSWER:"""
        
        return PromptTemplate(
            template=template,
            input_variables=["context", "query"],
            partial_variables=self.domain_config
        )
    
    def build_prompt(self, query: str, context: str) -> str:
        """
        Build prompt with query and context using LangChain template
        
        Args:
            query: User query
            context: Context text
            
        Returns:
            Complete prompt string
        """
        context_text = f"CONTEXT:\n{context}" if context and context.strip() else "CONTEXT:\nNo relevant context found."
        return self.prompt_template.format(query=query, context=context_text)
    
    def build_prompt_with_sources(
        self,
        query: str,
        retrieved_docs: List[Dict[str, Any]]
    ) -> str:
        """
        Build prompt with structured source information using LangChain template
        
        Args:
            query: User query
            retrieved_docs: List of retrieved documents with metadata
            
        Returns:
            Complete prompt string with sources
        """
        # Format context with sources
        if retrieved_docs:
            context_parts = ["CONTEXT:\n"]
            for i, doc in enumerate(retrieved_docs, 1):
                source = doc.get("source", "unknown")
                content = doc.get("content", "")
                similarity = doc.get("similarity", 0.0)
                
                context_parts.append(f"[Source {i}: {source} (relevance: {similarity:.2f})]\n{content}\n\n---\n")
            context_text = "\n".join(context_parts)
        else:
            context_text = "CONTEXT:\nNo relevant context found."
        
        return self.prompt_template.format(query=query, context=context_text)

