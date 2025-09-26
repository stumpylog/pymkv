# sheldon woodward
# 3/18/18

"""ISO639-2 Three Character Language Codes"""

from iso639 import is_language


def is_iso_639_2_language_code(language: str) -> bool:
    return is_language(language, "pt2t")
