import logging
import re

from transformers import AutoTokenizer
from pathlib import Path


logger = logging.getLogger(__name__)


def get_tokenizer(path: str):
    path = Path(path)
    if not path.exists():
        # raise FileNotFoundError(f"Model directory {path} does not exist")
        return None

    tokenizer_path = path / "tokenizer.json"
    if not tokenizer_path.exists():
        # raise FileNotFoundError(f"Tokenizer file {tokenizer_path} does not exist")
        return None

    tokenizer = AutoTokenizer.from_pretrained(path)
    return tokenizer


def get_all_chinese_tokens(tokenizer: AutoTokenizer) -> list[int]:
    """
    Extract Chinese tokens from byte-level BPE tokenizers like Qwen's.
    """
    chinese_tokens = []
    chinese_tokens_ids = []
    for token_id in range(tokenizer.vocab_size):
        decoded_token = tokenizer.decode([token_id], skip_special_tokens=True)
        
        if re.search(r'[\u4e00-\u9fa5]', decoded_token):
            if decoded_token:
                chinese_tokens.append(decoded_token)
                chinese_tokens_ids.append(token_id)
    return chinese_tokens, chinese_tokens_ids


def prepare_logit_bias(tokenizer: AutoTokenizer):
    """
    map for `logit_bias` params of OpenAI API.
    """
    if tokenizer is None:
        return None
    _ , chinese_tokens_ids = get_all_chinese_tokens(tokenizer)
    logit_bias = {
        token_id: -9999 for token_id in chinese_tokens_ids
    }
    return logit_bias
