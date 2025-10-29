import hashlib
import math
import re

def chunk_for_lm_studio(
    text: str,
    max_tokens: int,
    overlap_tokens: int = 64,
    encoding_name: str = "cl100k_base",  # good default for many chat models
    reserve_tokens: int = 0,             # tokens you need to keep free (e.g., system/instructions)
):
    """
    Split `text` into token-safe chunks for LM Studio (or any OpenAI-compatible API).
    
    Strategy:
      1) Try to pack paragraphs (split on double newlines) up to the token limit.
      2) If a paragraph is still too big, split into sentences and retry.
      3) If still too big, split by words (hard wrap).
    Adds a small token overlap between chunks for continuity.

    Returns:
      List[dict] like:
        {
          "index": 0,
          "total": N,
          "content": "...chunk text...",
          "sha256": "hex",
          "start_token": int,
          "end_token": int
        }

    Notes:
      - `max_tokens` is the **per-message** limit you want for the *content only*.
      - Use `reserve_tokens` if your request will also include a system prompt or other
        fixed text so chunks never exceed the model’s true max context window.
      - If `tiktoken` isn't installed, a safe word-length approximation is used.
    """
    # --- tokenizer helpers ---
    try:
        import tiktoken
        enc = tiktoken.get_encoding(encoding_name)

        def count_tokens(s: str) -> int:
            return len(enc.encode(s))

        def trim_to_tokens(s: str, target: int) -> str:
            ids = enc.encode(s)
            if len(ids) <= target:
                return s
            return enc.decode(ids[:target])

    except Exception:
        # Fallback: approximate by words
        enc = None

        def count_tokens(s: str) -> int:
            # rough heuristic: ~1 token ≈ 0.75 words; invert => tokens ≈ words / 0.75
            # we intentionally over-estimate to be safer
            words = len(s.split())
            return math.ceil(words / 0.75)

        def trim_to_tokens(s: str, target: int) -> str:
            # trim by words proportionally
            words = s.split()
            approx_words_allowed = max(1, math.floor(target * 0.75))
            return " ".join(words[:approx_words_allowed])

    hard_cap = max_tokens - max(0, reserve_tokens)
    if hard_cap <= 0:
        raise ValueError("max_tokens must be greater than reserve_tokens")

    # Normalize line endings
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    # Primary boundaries
    paragraphs = re.split(r"\n{2,}", text)

    chunks = []
    current = []
    current_tokens = 0

    def flush_current():
        nonlocal chunks, current, current_tokens
        if not current:
            return
        chunk_text = "\n\n".join(current).strip()
        chunks.append(chunk_text)
        current = []
        current_tokens = 0

    for para in paragraphs:
        ptoks = count_tokens(para)
        if ptoks <= hard_cap:
            # can we add it to current?
            if current_tokens + (count_tokens("\n\n") if current else 0) + ptoks <= hard_cap:
                if current:
                    current.append(para)
                    current_tokens += count_tokens("\n\n") + ptoks
                else:
                    current = [para]
                    current_tokens = ptoks
            else:
                flush_current()
                current = [para]
                current_tokens = ptoks
        else:
            # paragraph itself too large → sentence split
            flush_current()
            sentences = re.split(r"(?<=[.!?])\s+(?=[A-Z0-9\"'])", para.strip())
            buf = []
            buf_tokens = 0
            for sent in sentences:
                stoks = count_tokens(sent)
                if stoks <= hard_cap:
                    if buf_tokens + (count_tokens(" ") if buf else 0) + stoks <= hard_cap:
                        if buf:
                            buf.append(sent)
                            buf_tokens += count_tokens(" ") + stoks
                        else:
                            buf = [sent]
                            buf_tokens = stoks
                    else:
                        # flush sentence buffer
                        if buf:
                            chunks.append(" ".join(buf).strip())
                        buf = [sent]
                        buf_tokens = stoks
                else:
                    # sentence too big → hard wrap by tokens/words
                    if buf:
                        chunks.append(" ".join(buf).strip())
                        buf, buf_tokens = [], 0
                    big = sent
                    # hard-slice using tokenizer or word fallback
                    while count_tokens(big) > hard_cap:
                        slice_text = trim_to_tokens(big, hard_cap)
                        chunks.append(slice_text.strip())
                        # remove the part we just used
                        if enc:
                            # precise: drop exactly the tokens used
                            used = slice_text
                            remaining_ids = enc.encode(big)[len(enc.encode(slice_text)):]
                            big = enc.decode(remaining_ids)
                        else:
                            # fallback: drop by words
                            used_words = len(slice_text.split())
                            big_words = big.split()
                            big = " ".join(big_words[used_words:])
                    if big.strip():
                        chunks.append(big.strip())
            if buf:
                chunks.append(" ".join(buf).strip())
            # reset paragraph packer
            current, current_tokens = [], 0

    flush_current()

    # apply overlap (by tokens) to all but first chunk
    if overlap_tokens > 0 and len(chunks) > 1:
        overlapped = []
        for i, c in enumerate(chunks):
            if i == 0:
                overlapped.append(c)
                continue
            # take ~overlap_tokens from the *end* of previous chunk and prepend (if space allows)
            prev = overlapped[-1]
            # tail from prev
            if enc:
                prev_ids = enc.encode(prev)
                tail_ids = prev_ids[-min(len(prev_ids), overlap_tokens):]
                tail = enc.decode(tail_ids)
            else:
                # approximate tail by words
                prev_words = prev.split()
                tail = " ".join(prev_words[-max(1, math.floor(overlap_tokens * 0.75)):])

            candidate = (tail + "\n" + c).strip()
            # ensure candidate still fits; if not, trim the *front* (i.e., the tail) down
            if count_tokens(candidate) > hard_cap:
                candidate = trim_to_tokens(candidate, hard_cap)
            overlapped.append(candidate)
        chunks = overlapped

    # package with metadata
    result = []
    running_tok = 0
    total = len(chunks)
    for idx, c in enumerate(chunks):
        ctoks = count_tokens(c)
        sha = hashlib.sha256(c.encode("utf-8")).hexdigest()
        result.append({
            "index": idx,
            "total": total,
            "content": c,
            "sha256": sha,
            "start_token": running_tok,
            "end_token": running_tok + ctoks - 1
        })
        running_tok += ctoks

    return result
