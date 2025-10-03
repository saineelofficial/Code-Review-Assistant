def prune_patch(patch: str, max_chars: int = 2000) -> str:
    """Keep unified diff within budget; preserve head/tail for context."""
    if not patch:
        return ""
    if len(patch) <= max_chars:
        return patch
    head = patch[:800]
    tail = patch[-(max_chars - 800 - 7):]  # 7 for the separator
    return head + "\n...\n" + tail
