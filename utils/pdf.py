from fpdf import FPDF
from fpdf.errors import FPDFException
import os, re

# Optional HTML pipeline
_HAS_HTML = True
try:
    import markdown2
    from xhtml2pdf import pisa
except Exception:
    _HAS_HTML = False


# --- sanitizers ---
def sanitize_text(text: str):
    replacements = {
        "\u2013": "-",  # en dash
        "\u2014": "-",  # em dash
        "\u201C": '"',  # left double quote
        "\u201D": '"',  # right double quote
        "\u2019": "'",  # right single quote
        "\u00A0": " ",  # no-break space
        "\u200B": "",   # zero-width space
        "\u2060": "",   # word joiner
    }
    for bad, good in replacements.items():
        text = text.replace(bad, good)
    text = remove_emojis(text)  # ← strip emojis/pictographs
    return text

def break_long_sequences(text: str, max_len: int = 30):
    """
    Break sequences longer than max_len by inserting spaces.
    Prefers splitting at / or -; falls back to hard chunks.
    """
    tokens = re.split(r'(\s+)', text)  # keep whitespace tokens
    broken = []
    for tok in tokens:
        if tok.isspace() or len(tok) <= max_len:
            broken.append(tok)
            continue
        # try to split at / or -
        parts = re.split(r'([/-])', tok)
        current = ""
        for part in parts:
            if len(current + part) > max_len:
                if current:
                    broken.append(current)
                current = part
            else:
                current += part
        if current:
            broken.append(current)
    return "".join(broken)

# --- hard wrap fallback (character-level) ---
def write_wrapped_line(pdf: FPDF, text: str, line_h: float, max_w: float):
    """
    Write text wrapped at character level so it ALWAYS fits.
    Uses pdf.get_string_width to pack as many chars per line as will fit.
    """
    i = 0
    n = len(text)
    while i < n:
        # find the largest substring that fits
        lo, hi = 1, n - i
        fit = 1
        while lo <= hi:
            mid = (lo + hi) // 2
            chunk = text[i:i+mid]
            if pdf.get_string_width(chunk) <= max_w:
                fit = mid
                lo = mid + 1
            else:
                hi = mid - 1
        chunk = text[i:i+fit]
        pdf.cell(max_w, line_h, chunk, ln=1)  # single line
        i += fit


_EMOJI_RE = re.compile(
    "["                     # common emoji + pictograph ranges
    u"\U0001F300-\U0001F5FF"  # symbols & pictographs (includes 📧, 📎 range)
    u"\U0001F600-\U0001F64F"  # emoticons
    u"\U0001F680-\U0001F6FF"  # transport & map
    u"\U0001F700-\U0001F77F"  # alchemical symbols
    u"\U0001F780-\U0001F7FF"  # geometric shapes extended
    u"\U0001F800-\U0001F8FF"  # supplemental arrows-C
    u"\U0001F900-\U0001F9FF"  # supplemental symbols & pictographs
    u"\U0001FA00-\U0001FA6F"  # chess symbols, symbols & pictographs ext-A
    u"\U0001FA70-\U0001FAFF"  # symbols & pictographs ext-B
    u"\U00002700-\U000027BF"  # dingbats
    u"\U00002600-\U000026FF"  # misc symbols
    u"\U00002500-\U000025FF"  # box drawing & shapes
    "]+",
    flags=re.UNICODE
)

def remove_emojis(text: str) -> str:
    return _EMOJI_RE.sub("", text)

def generate_pdf_from_text(text: str, output_path: str):
    # Ensure directory exists BEFORE writing anything
    outdir = os.path.dirname(output_path) or "."
    os.makedirs(outdir, exist_ok=True)

    # Try HTML -> PDF if libs are available
    if _HAS_HTML:
        try:
            html = markdown2.markdown(text or "")
            with open(output_path, "wb") as f:
                pisa.CreatePDF(html, dest=f)
            # If xhtml2pdf produced a non-empty file, we're done
            if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                return output_path
        except Exception:
            # fall through to FPDF fallback
            pass

    # Fallback: plain FPDF rendering (always works)
    pdf = FPDF()
    pdf.set_margins(15, 15, 15)
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    # Load Unicode font if available; otherwise Arial
    font_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "fonts", "DejaVuSans.ttf"))
    if os.path.exists(font_path):
        pdf.add_font("DejaVu", "", font_path, uni=True)
        pdf.set_font("DejaVu", size=11)
    else:
        pdf.set_font("Arial", size=11)

    max_w = pdf.w - pdf.l_margin - pdf.r_margin
    line_h = 6

    cleaned = sanitize_text(text or "")
    for raw_line in cleaned.strip().split("\n"):
        prepped = break_long_sequences(raw_line, max_len=30)
        try:
            pdf.multi_cell(0, line_h, prepped)
        except FPDFException:
            pdf.set_x(pdf.l_margin)
            write_wrapped_line(pdf, prepped, line_h, max_w)

    pdf.output(output_path)
    return output_path
