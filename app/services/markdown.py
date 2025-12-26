import markdown
from markdown.extensions.codehilite import CodeHiliteExtension
from markdown.extensions.fenced_code import FencedCodeExtension
from markdown.extensions.toc import TocExtension
import re


def estimate_read_time(text: str) -> int:
    """Estimate reading time in minutes (avg 200 words/min)."""
    words = len(re.findall(r'\w+', text))
    minutes = max(1, round(words / 200))
    return minutes


def render_markdown(text: str) -> str:
    """Convert markdown to HTML with syntax highlighting."""
    md = markdown.Markdown(
        extensions=[
            'fenced_code',
            'tables',
            'nl2br',
            CodeHiliteExtension(css_class='highlight', linenums=False),
            TocExtension(permalink=False),
        ]
    )
    return md.convert(text)


def strip_markdown(text: str) -> str:
    """Strip markdown formatting for excerpts."""
    # Remove code blocks
    text = re.sub(r'```[\s\S]*?```', '', text)
    # Remove inline code
    text = re.sub(r'`[^`]+`', '', text)
    # Remove headers
    text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)
    # Remove bold/italic
    text = re.sub(r'\*{1,2}([^*]+)\*{1,2}', r'\1', text)
    # Remove links
    text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)
    # Remove images
    text = re.sub(r'!\[[^\]]*\]\([^)]+\)', '', text)
    # Clean up whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def generate_excerpt(content: str, max_length: int = 200) -> str:
    """Generate a plain text excerpt from markdown."""
    plain = strip_markdown(content)
    if len(plain) <= max_length:
        return plain
    return plain[:max_length].rsplit(' ', 1)[0] + '...'
