from dataclasses import dataclass

@dataclass
class PolishComment:
    """
    V1: simple comment wrapper.
    V2-ready: can add fields like severity/category/confidence later.
    """
    text: str
