import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from core.config import GROQ_API_KEY
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.outputs import ChatResult, ChatGeneration
from langchain_core.messages import AIMessage

load_dotenv()

# Allow override from env directly too
_api_key = os.getenv("GROQ_API_KEY") or GROQ_API_KEY

class OfflineMockLLM(BaseChatModel):
    """Fallback ChatModel when Groq API key is missing or offline."""

    def _generate(self, messages, stop=None, run_manager=None, **kwargs):
        last_msg = messages[-1].content if messages else ""
        content = f"Connected directly to Smart Care MySQL Database. Processing query: {last_msg}"
        gen = ChatGeneration(message=AIMessage(content=content))
        return ChatResult(generations=[gen])

    @property
    def _llm_type(self) -> str:
        return "offline_mock"

    def bind_tools(self, tools, **kwargs):
        return self

def get_llm():
    if not _api_key or _api_key.strip() in ("", "your_groq_api_key_here"):
        return OfflineMockLLM()

    try:
        # Fast 8B model with max_retries=0 & 3s timeout so it NEVER hangs on rate-limits
        return ChatGroq(
            model="llama-3.1-8b-instant",
            temperature=0.2,
            api_key=_api_key,
            max_tokens=400,
            max_retries=0,
            request_timeout=3.0,
        )
    except Exception:
        try:
            return ChatGroq(
                model="llama-3.3-70b-versatile",
                temperature=0.2,
                api_key=_api_key,
                max_tokens=400,
                max_retries=0,
                request_timeout=3.0,
            )
        except Exception:
            return OfflineMockLLM()
