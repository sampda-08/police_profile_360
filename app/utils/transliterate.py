import re
import unicodedata
from indic_transliteration import sanscript
from indic_transliteration.sanscript import transliterate

def is_english(text: str) -> bool:
    """Checks whether the input string contains English/Latin characters."""
    return bool(re.search(r'[a-zA-Z]', text))

def clean_text(text: str) -> str:
    if not text:
        return ""
    return unicodedata.normalize('NFC', text.strip())

def transliterate_token(token: str) -> list:
    """
    Algorithmically converts any arbitrary English token into Devanagari.
    Works for any name: 'suresh', 'kamble', 'chandrakant', 'dnyaneshwar', etc.
    """
    token = token.lower().strip()
    if not token:
        return []

    variants = set()

    # Rule adjustments for common Marathi phonetic spellings in English
    phonetic_pre_pass = (
        token.replace("ee", "i")
             .replace("oo", "u")
             .replace("w", "v")
             .replace("shh", "sh")
    )

    try:
        # Standard Devanagari mapping via ITRANS
        dev_primary = transliterate(phonetic_pre_pass, sanscript.ITRANS, sanscript.DEVANAGARI)
        if dev_primary:
            variants.add(clean_text(dev_primary))

        # Handle schwa deletion (e.g., 'kamble' / 'kamblea', 'suresh' / 'suresha')
        if not phonetic_pre_pass.endswith(('a', 'i', 'u', 'e', 'o')):
            dev_with_vowel = transliterate(phonetic_pre_pass + 'a', sanscript.ITRANS, sanscript.DEVANAGARI)
            if dev_with_vowel:
                variants.add(clean_text(dev_with_vowel))
        elif phonetic_pre_pass.endswith('a') and len(phonetic_pre_pass) > 2:
            dev_without_vowel = transliterate(phonetic_pre_pass[:-1], sanscript.ITRANS, sanscript.DEVANAGARI)
            if dev_without_vowel:
                variants.add(clean_text(dev_without_vowel))

        # Handle Marathi specific 'ळ' (L in Kamble, Ingle, etc.)
        l_variants = set()
        for v in variants:
            if 'ल' in v:
                l_variants.add(v.replace('ल', 'ळ'))
        variants.update(l_variants)

    except Exception:
        pass

    return list(variants)