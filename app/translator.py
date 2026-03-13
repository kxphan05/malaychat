"""English <-> Malay translation using mesolitica/nanot5."""

import logging
import time

import streamlit as st
import torch
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

logger = logging.getLogger("malaychat.translator")

MODEL_ID = "mesolitica/nanot5-base-malaysian-translation-v2.1"


@st.cache_resource(show_spinner="Loading translation model...")
def load_translator() -> tuple[AutoModelForSeq2SeqLM, AutoTokenizer]:
    """Load the nanot5 translation model and tokenizer."""
    logger.info("Loading translator: %s", MODEL_ID)
    t0 = time.perf_counter()
    tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)
    model = AutoModelForSeq2SeqLM.from_pretrained(MODEL_ID)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = model.to(device)
    logger.info("Translator loaded in %.2fs, device=%s", time.perf_counter() - t0, device)
    return model, tokenizer


def _translate(text: str, prefix: str, max_length: int = 256) -> str:
    """Run translation with given prefix."""
    model, tokenizer = load_translator()
    input_text = f"{prefix}: {text}"
    logger.debug("Translating: %r", input_text[:200])

    inputs = tokenizer(input_text, return_tensors="pt", truncation=True, max_length=512)
    inputs = inputs.to(model.device)

    with torch.no_grad():
        output_ids = model.generate(**inputs, max_length=max_length)

    result = tokenizer.decode(output_ids[0], skip_special_tokens=True).strip()
    logger.debug("Translation result: %r", result[:200])
    return result


def to_malay(text: str) -> str:
    """Translate English text to Malay."""
    return _translate(text, "terjemah ke Melayu")


def to_english(text: str) -> str:
    """Translate Malay text to English."""
    return _translate(text, "terjemah ke Inggeris")
