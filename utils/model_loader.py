import os
import sys
from dotenv import load_dotenv
from typing import Literal, Optional, Any
from pydantic import BaseModel, Field
from utils.config_loader import load_config
from langchain_groq import ChatGroq
from langchain_openai import ChatOpenAI

from logger.logging import get_logger
from exception.exceptionhandling import TripPlannerException

logger = get_logger(__name__)


class ConfigLoader:
    def __init__(self):
        logger.info("Loading config from config/config.yaml")
        self.config = load_config()

    def __getitem__(self, key):
        return self.config[key]


class ModelLoader(BaseModel):
    model_provider: Literal["groq", "openai"] = "groq"
    config: Optional[ConfigLoader] = Field(default=None, exclude=True)

    def model_post_init(self, __context: Any) -> None:
        self.config = ConfigLoader()

    class Config:
        arbitrary_types_allowed = True

    def load_llm(self):
        """
        Load and return the LLM model for the configured provider.
        """
        logger.info(f"Loading LLM for provider: {self.model_provider}")
        try:
            if self.model_provider == "groq":
                groq_api_key = os.getenv("GROQ_API_KEY")
                if not groq_api_key:
                    raise ValueError("GROQ_API_KEY is not set in the environment.")
                model_name = self.config["llm"]["groq"]["model_name"]
                logger.info(f"Using Groq model: {model_name}")
                llm = ChatGroq(model=model_name, api_key=groq_api_key)

            elif self.model_provider == "openai":
                openai_api_key = os.getenv("OPENAI_API_KEY")
                if not openai_api_key:
                    raise ValueError("OPENAI_API_KEY is not set in the environment.")
                # NOTE: previously this ignored the configured model name and
                # hardcoded "o4-mini" below. Now it actually uses the value
                # read from config/config.yaml.
                model_name = self.config["llm"]["openai"]["model_name"]
                logger.info(f"Using OpenAI model: {model_name}")
                llm = ChatOpenAI(model_name=model_name, api_key=openai_api_key)

            else:
                raise ValueError(f"Unsupported model provider: {self.model_provider}")

            return llm

        except Exception as e:
            logger.error(f"Failed to load LLM for provider '{self.model_provider}': {e}")
            raise TripPlannerException(e, sys) from e
