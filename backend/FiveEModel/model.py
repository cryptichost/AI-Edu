import os

from dotenv import load_dotenv
from google.adk.models.lite_llm import LiteLlm
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_openai import OpenAIEmbeddings

load_dotenv()

DEFAULT_RAG_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
DEFAULT_RESOURCE_DIRECTORY = 'data/Book'
CHROMA_PERSIST_DIRACTORY = 'fiveE/chroma_db'

API_KEY = os.getenv("NAPI_KEY") or os.getenv("api_key")
MODEL = os.getenv("MODEL") or os.getenv("model_name")
ENDPOINT = os.getenv("ENDPOINT") or os.getenv("base_url")

if not API_KEY or not MODEL or not ENDPOINT:
    raise RuntimeError(
        "5E model config missing: set NAPI_KEY/MODEL/ENDPOINT "
        "or api_key/model_name/base_url in .env"
    )

deepseek = LiteLlm(
    model=f"{MODEL}",
    base_url=ENDPOINT,
    api_key=API_KEY,
    tool_choice="auto",
    extra_body={
        "thinking": {
            "type": "disabled"
        }
    },
    response_format={
        'type': 'json_object'
    }
)

