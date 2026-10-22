"""Install a local-only tokenizer factory without changing upstream files."""
from pathlib import Path


def install(path):
    path = Path(path).resolve(strict=True)
    import sentencepiece
    from openpi.models import tokenizer
    def local_init(self,max_len=48):
        self._max_len = max_len
        self._tokenizer = sentencepiece.SentencePieceProcessor(model_file=str(path))
    tokenizer.PaligemmaTokenizer.__init__ = local_init
