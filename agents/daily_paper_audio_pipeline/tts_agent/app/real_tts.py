import os
import re
import tempfile
import logging
from typing import Optional
import torch

logger = logging.getLogger("tts_agent")

class RealTTSEngine:
    _instance = None
    
    # Translation model lazy cache
    _translation_tokenizer = None
    _translation_model = None
    _tried_translation_load = False
    _translation_error = None
    
    # TTS model lazy cache
    _tts_model = None
    _tried_tts_load = False
    _tts_error = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def load_translation_model(self):
        """
        Lazy load Meta NLLB-200 English-to-Vietnamese Translate model weights.
        """
        if self._tried_translation_load:
            if self._translation_error:
                raise self._translation_error
            return self._translation_tokenizer, self._translation_model

        self._tried_translation_load = True
        logger.info("Initializing Meta NLLB-200 Translate model (facebook/nllb-200-distilled-600M)...")
        try:
            import torch
            device = "cuda" if torch.cuda.is_available() else "cpu"
            env_mode = os.getenv("TTS_MODE", "mock_fallback").lower().strip()
            if device == "cpu" and env_mode == "mock_fallback":
                raise RuntimeError("Running on CPU in mock_fallback mode. Skipping translation model load to prevent API hangs.")

            from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
            model_name = "facebook/nllb-200-distilled-600M"
            
            self._translation_tokenizer = AutoTokenizer.from_pretrained(model_name, src_lang="eng_Latn")
            if device == "cuda":
                self._translation_model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
            else:
                self._translation_model = AutoModelForSeq2SeqLM.from_pretrained(model_name, torch_dtype=torch.bfloat16)
            self._translation_model.to(device)
            
            logger.info(f"Meta NLLB-200 Translate model loaded successfully on {device}.")
            return self._translation_tokenizer, self._translation_model
        except Exception as e:
            self._translation_error = RuntimeError(f"Translation model load failed: {str(e)}")
            logger.error(f"Failed to load Meta NLLB-200 Translate model: {str(e)}", exc_info=True)
            raise self._translation_error


    def load_tts_model(self):
        """
        Lazy load VieNeu-TTS model weights.
        """
        if self._tried_tts_load:
            if self._tts_error:
                raise self._tts_error
            return self._tts_model

        self._tried_tts_load = True
        logger.info("Initializing VieNeu-TTS model...")
        try:
            # Lazy import to avoid loading during fast health checks
            from vieneu import Vieneu
            
            # Using v3turbo mode which is fast, lightweight and torch-free on CPU
            self._tts_model = Vieneu(mode="v3turbo")
            logger.info("VieNeu-TTS model loaded successfully.")
            return self._tts_model
        except Exception as e:
            self._tts_error = RuntimeError(f"VieNeu model load failed: {str(e)}")
            logger.error(f"Failed to load VieNeu-TTS model: {str(e)}", exc_info=True)
            raise self._tts_error

    def is_loaded(self) -> bool:
        """
        Check if the TTS model is currently initialized in memory.
        """
        return self._tts_model is not None

    def translate_en_to_vi(self, text: str) -> str:
        """
        Translate English text to Vietnamese using Meta NLLB-200.
        Splits paragraph into sentences for better performance.
        """
        tokenizer, model = self.load_translation_model()
        device = "cuda" if torch.cuda.is_available() else "cpu"
        
        # Split text into sentences
        sentences = re.split(r'(?<=[.!?])\s+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        translated_sentences = []
        for sentence in sentences:
            if not sentence:
                continue
            logger.info(f"Translating sentence: '{sentence}'")
            input_ids = tokenizer(sentence, return_tensors="pt").to(device)
            output_ids = model.generate(
                **input_ids,
                forced_bos_token_id=tokenizer.convert_tokens_to_ids("vie_Latn"),
                num_return_sequences=1,
                num_beams=5,
                early_stopping=True
            )
            translated = tokenizer.batch_decode(output_ids, skip_special_tokens=True)[0]
            translated_sentences.append(translated)
            
        vi_text = " ".join(translated_sentences)
        logger.info(f"Translation completed. Output: '{vi_text}'")
        return vi_text

    def synthesize(self, text: str, voice: str = "default", language: str = "vi", speed: float = 1.0) -> bytes:
        """
        Synthesize text to speech WAV bytes.
        Automatically translates text from English to Vietnamese if language is 'en'.
        """
        if not text or not text.strip():
            raise ValueError("Input text is empty")
            
        # Detect if we need to translate from English to Vietnamese
        # Translate if language code starts with 'en' or if it looks like English and language is 'en'
        normalized_language = language.lower().strip()
        if normalized_language.startswith("en"):
            logger.info("Detecting English text. Starting translation to Vietnamese...")
            vi_text = self.translate_en_to_vi(text)
        else:
            vi_text = text

        # Load VieNeu-TTS model
        tts_engine = self.load_tts_model()
        
        logger.info(f"Synthesizing speech for: '{vi_text[:100]}...' using voice: '{voice}'")
        
        # Verify voice parameter and fallback if not loaded in VieNeu preset voices
        preset_voices = list(tts_engine._preset_voices.keys()) if hasattr(tts_engine, '_preset_voices') else []
        if voice not in preset_voices:
            voice = "Ngọc Linh" if "Ngọc Linh" in preset_voices else (preset_voices[0] if preset_voices else None)
            
        # Synthesize audio array using the resolved voice
        audio = tts_engine.infer(vi_text, voice=voice, emotion="natural")
        
        # Save to temp file and read bytes
        temp_dir = tempfile.gettempdir()
        temp_file = os.path.join(temp_dir, f"tts_output_{os.getpid()}.wav")
        try:
            tts_engine.save(audio, temp_file)
            with open(temp_file, "rb") as f:
                wav_bytes = f.read()
            return wav_bytes
        finally:
            if os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                except Exception:
                    pass
