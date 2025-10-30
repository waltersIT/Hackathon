import hashlib, math, re, json

def chunk_for_lm_studio(
    text: str,
    max_tokens: int,
    overlap_tokens: int = 64,
    encoding_name: str = "cl100k_base",   # used if tiktoken is available
    reserve_tokens: int = 0,
    detect_json: bool = True,
    json_max_bytes: int | None = None,    # optional hard byte cap per JSON chunk; if None, derived from max_tokens
    pretty_json: bool = True              # indent JSON envelopes for readability
):
    """
    Token-safe chunker with JSON awareness.

    - If the input looks like JSON (and detect_json=True), it splits structure-aware into
      multiple VALID JSON documents, each wrapped as:
        {"path": "<pointer-ish>", "data": <partial JSON>}
      to avoid breaking objects/arrays mid-key. This is *byte*-capped to avoid transport
      limits that cause 'Channel Error' with LM Studio.

    - Otherwise, it uses a token-based strategy (paragraph -> sentence -> word) with overlap.

    Returns: List[dict] with: index, total, content, sha256, start_token, end_token
    """

    # --- tokenizer helpers (tiktoken optional) ---
    try:
        import tiktoken
        enc = tiktoken.get_encoding(encoding_name)
        def count_tokens(s: str) -> int: return len(enc.encode(s))
        def trim_to_tokens(s: str, target: int) -> str:
            ids = enc.encode(s)
            if len(ids) <= target: return s
            return enc.decode(ids[:target])
    except Exception:
        enc = None
        def count_tokens(s: str) -> int:
            # conservative over-estimate: tokens ~ words / 0.75
            return math.ceil(len(s.split()) / 0.75) if s else 0
        def trim_to_tokens(s: str, target: int) -> str:
            words = s.split()
            n = max(1, math.floor(target * 0.75))
            return " ".join(words[:n])

    hard_cap = max_tokens - max(0, reserve_tokens)
    if hard_cap <= 0:
        raise ValueError("max_tokens must be greater than reserve_tokens")

    # ------------- JSON-AWARE BRANCH -------------
    def _size_bytes(s: str) -> int:
        return len(s.encode("utf-8", "replace"))

    def _wrap(path: str, payload, pretty: bool) -> str:
        if pretty:
            return json.dumps({"path": path, "data": payload}, ensure_ascii=False, indent=2)
        return json.dumps({"path": path, "data": payload}, ensure_ascii=False, separators=(",", ":"))

    def _byte_chunks_fallback(raw: str, max_bytes: int, path: str, pretty: bool):
        bs = raw.encode("utf-8", "replace")
        out = []
        i = 0
        # keep some headroom for the {"path":..,"data":..} envelope
        overhead = 64 + len(path.encode("utf-8", "replace"))
        while i < len(bs):
            j = min(len(bs), i + max(1024, max_bytes - overhead))
            if j < len(bs):
                # back up to a likely boundary
                back = 0
                while j - back > i and bs[j - back:j - back + 1] not in b", \n\r\t}]":
                    back += 1
                if j - back <= i:
                    back = 0
                j -= back
            chunk = bs[i:j].decode("utf-8", "replace")
            out.append(_wrap(path, chunk, pretty))
            i = j
        return out

    def _split_any(obj, max_bytes: int, path: str, pretty: bool):
        if isinstance(obj, dict):
            return _pack_dict(obj, max_bytes, path, pretty)
        if isinstance(obj, list):
            return _pack_list(obj, max_bytes, path, pretty)
        s = _wrap(path, obj, pretty)
        if _size_bytes(s) <= max_bytes:
            return [s]
        # extremely long primitive (usually a huge string)
        raw = json.dumps(obj, ensure_ascii=False)
        return _byte_chunks_fallback(raw, max_bytes, path, pretty)

    def _pack_dict(d: dict, max_bytes: int, path: str, pretty: bool):
        out, current = [], {}
        for k, v in d.items():
            tentative = dict(current); tentative[k] = v
            if _size_bytes(_wrap(path, tentative, pretty)) <= max_bytes:
                current = tentative
                continue
            single = _wrap(f"{path}.{k}" if path else k, v, pretty)
            if _size_bytes(single) <= max_bytes:
                if current:
                    out.append(_wrap(path, current, pretty)); current = {}
                out.append(single)
            else:
                if current:
                    out.append(_wrap(path, current, pretty)); current = {}
                out.extend(_split_any(v, max_bytes, f"{path}.{k}" if path else k, pretty))
        if current:
            out.append(_wrap(path, current, pretty))
        return out

    def _pack_list(arr: list, max_bytes: int, path: str, pretty: bool):
        out, buf = [], []
        for idx, item in enumerate(arr):
            tentative = list(buf); tentative.append(item)
            if _size_bytes(_wrap(path, tentative, pretty)) <= max_bytes:
                buf = tentative
                continue
            single = _wrap(f"{path}[{idx}]", item, pretty)
            if _size_bytes(single) <= max_bytes:
                if buf:
                    out.append(_wrap(path, buf, pretty)); buf = []
                out.append(single)
            else:
                if buf:
                    out.append(_wrap(path, buf, pretty)); buf = []
                out.extend(_split_any(item, max_bytes, f"{path}[{idx}]", pretty))
        if buf:
            out.append(_wrap(path, buf, pretty))
        return out

    looks_like_json = detect_json and text.strip()[:1] in "{[" and text.strip()[-1:] in "}]"
    if looks_like_json:
        try:
            obj = json.loads(text)
            # derive a byte ceiling from tokens if explicit json_max_bytes not set
            if json_max_bytes is None:
                # crude mapping: ~4 chars per token + envelope headroom
                approx_chars = hard_cap * 4
                json_max_bytes = max(16_000, min(256_000, approx_chars))
            json_chunks = _split_any(obj, json_max_bytes, path="", pretty=pretty_json)

            # convert json chunks -> standardized result with metadata
            result = []
            running_tok = 0
            total = len(json_chunks)
            for idx, c in enumerate(json_chunks):
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

            # Optional: add small overlap (by tokens) to aid continuity
            if overlap_tokens > 0 and len(result) > 1:
                overlapped = []
                for i, part in enumerate(result):
                    c = part["content"]
                    if i == 0:
                        overlapped.append(part)
                        continue
                    prev = overlapped[-1]["content"]
                    if enc:
                        prev_ids = enc.encode(prev)
                        tail_ids = prev_ids[-min(len(prev_ids), overlap_tokens):]
                        tail = enc.decode(tail_ids)
                    else:
                        prev_words = prev.split()
                        tail = " ".join(prev_words[-max(1, math.floor(overlap_tokens * 0.75)):])
                    candidate = (tail + "\n" + c).strip()
                    if count_tokens(candidate) > hard_cap:
                        candidate = trim_to_tokens(candidate, hard_cap)
                    # refresh metadata
                    ctoks = count_tokens(candidate)
                    sha = hashlib.sha256(candidate.encode("utf-8")).hexdigest()
                    part = part.copy()
                    part["content"] = candidate
                    part["sha256"] = sha
                    part["start_token"] = overlapped[-1]["end_token"] + 1
                    part["end_token"] = part["start_token"] + ctoks - 1
                    overlapped.append(part)
                result = overlapped

            # normalize indexes/total
            for i, r in enumerate(result):
                r["index"], r["total"] = i, len(result)
            return result

        except Exception:
            # parsing failed -> fall through to prose splitter
            pass

    # ------------- PROSE/TEXT BRANCH (token-based) -------------
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    paragraphs = re.split(r"\n{2,}", text)

    chunks, current, current_tokens = [], [], 0

    def flush_current():
        nonlocal chunks, current, current_tokens
        if not current: return
        chunk_text = "\n\n".join(current).strip()
        chunks.append(chunk_text)
        current, current_tokens = [], 0

    for para in paragraphs:
        ptoks = count_tokens(para)
        if ptoks <= hard_cap:
            sep_toks = count_tokens("\n\n") if current else 0
            if current_tokens + sep_toks + ptoks <= hard_cap:
                if current:
                    current.append(para); current_tokens += sep_toks + ptoks
                else:
                    current = [para]; current_tokens = ptoks
            else:
                flush_current()
                current = [para]; current_tokens = ptoks
        else:
            flush_current()
            sentences = re.split(r"(?<=[.!?])\s+(?=[A-Z0-9\"'])", para.strip())
            buf, buf_tokens = [], 0
            for sent in sentences:
                stoks = count_tokens(sent)
                if stoks <= hard_cap:
                    sep = count_tokens(" ") if buf else 0
                    if buf_tokens + sep + stoks <= hard_cap:
                        if buf:
                            buf.append(sent); buf_tokens += sep + stoks
                        else:
                            buf = [sent]; buf_tokens = stoks
                    else:
                        if buf:
                            chunks.append(" ".join(buf).strip()); buf, buf_tokens = [], 0
                        buf = [sent]; buf_tokens = stoks
                else:
                    if buf:
                        chunks.append(" ".join(buf).strip()); buf, buf_tokens = [], 0
                    big = sent
                    while count_tokens(big) > hard_cap:
                        slice_text = trim_to_tokens(big, hard_cap)
                        chunks.append(slice_text.strip())
                        if enc:
                            used_ids = enc.encode(slice_text)
                            remaining_ids = enc.encode(big)[len(used_ids):]
                            big = enc.decode(remaining_ids)
                        else:
                            used_words = len(slice_text.split())
                            big = " ".join(big.split()[used_words:])
                    if big.strip():
                        chunks.append(big.strip())
            if buf:
                chunks.append(" ".join(buf).strip())
            current, current_tokens = [], 0

    flush_current()

    # apply overlap to prose chunks
    if overlap_tokens > 0 and len(chunks) > 1:
        overlapped = []
        for i, c in enumerate(chunks):
            if i == 0:
                overlapped.append(c); continue
            prev = overlapped[-1]
            if enc:
                prev_ids = enc.encode(prev)
                tail_ids = prev_ids[-min(len(prev_ids), overlap_tokens):]
                tail = enc.decode(tail_ids)
            else:
                prev_words = prev.split()
                tail = " ".join(prev_words[-max(1, math.floor(overlap_tokens * 0.75)):])
            candidate = (tail + "\n" + c).strip()
            if count_tokens(candidate) > hard_cap:
                candidate = trim_to_tokens(candidate, hard_cap)
            overlapped.append(candidate)
        chunks = overlapped

    # package metadata for prose
    result, running_tok = [], 0
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
