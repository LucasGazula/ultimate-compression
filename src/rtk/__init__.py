from .autodetect import auto_detect_filter

def compress_text(text):
    """
    Compresses text using the auto-detected RTK filter.
    Returns:
        (compressed_text, filter_name, saved_bytes)
    """
    if not text:
        return text, None, 0
    
    filter_name, filter_fn = auto_detect_filter(text)
    if not filter_fn:
        return text, None, 0
        
    try:
        compressed = filter_fn(text)
        saved = len(text) - len(compressed)
        if saved > 0:
            return compressed, filter_name, saved
    except Exception as e:
        print(f"[RTK] Error running filter {filter_name}: {e}")
        
    return text, None, 0
