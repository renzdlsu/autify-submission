"""This module downloads and caches the model and tokenizer files.

It ensures that model dependencies are available at build time to ensure faster runtime execution.
"""

import logging
import os
from dotenv import load_dotenv
from transformers import AutoModelForCausalLM, AutoTokenizer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

HF_CACHE_DIR = os.environ.get("HF_CACHE_DIR", "~/.cache/huggingface/transformers/")
HF_TOKEN = os.environ.get("HF_TOKEN")

load_dotenv()

logger.info("Downloading the tokenizer and model files to %s", HF_CACHE_DIR)

tokenizer = AutoTokenizer.from_pretrained("stabilityai/stablecode-instruct-alpha-3b")
tokenizer.save_pretrained(HF_CACHE_DIR)
logger.info("Tokenizer downloaded successfully")

model = AutoModelForCausalLM.from_pretrained(
    "stabilityai/stablecode-instruct-alpha-3b",
    trust_remote_code=True,
    torch_dtype="auto",
)
model.save_pretrained(HF_CACHE_DIR)
logger.info("Model downloaded successfully")

logger.info("Successfully completed the download of the tokenizer and model")
