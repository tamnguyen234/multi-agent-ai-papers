import logging
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def install_model():
    logger.info("Loading NLLB tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained("facebook/nllb-200-distilled-600M")
    logger.info("Loading NLLB model...")
    model = AutoModelForSeq2SeqLM.from_pretrained("facebook/nllb-200-distilled-600M")
    logger.info("NLLB model loaded and cached successfully.")
    
    # Optional test translation
    article = "Hello world, this is a test."
    inputs = tokenizer(article, return_tensors="pt")
    translated_tokens = model.generate(
        **inputs, forced_bos_token_id=tokenizer.convert_tokens_to_ids("vie_Latn"), max_length=100
    )
    res = tokenizer.batch_decode(translated_tokens, skip_special_tokens=True)[0]
    logger.info(f"Test translation: {res}")

if __name__ == "__main__":
    install_model()
