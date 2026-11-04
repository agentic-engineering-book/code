"""Fetch result pages and split them into paragraphs.

Polite by default: the fetcher names itself, obeys each site's robots.txt,
waits at most TIMEOUT seconds and reads at most MAX_BYTES. HTML is reduced to
its readable blocks (headings, paragraphs, list items); navigation, scripts,
forms and footers are dropped. PDFs are read as text. Blocks are merged into
paragraph chunks of about CHUNK_WORDS words that never cross a heading, so
each chunk is one coherent piece of a page.
"""
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser
import re

import requests

USER_AGENT = ('AgenticSearchDemo/0.1 (book demo; '
              '+https://agentic-engineering-book.com)')
TIMEOUT = 12
MAX_BYTES = 3_000_000
CHUNK_WORDS = 160
MAX_CHUNKS = 60
_robots = {}


def allowed(url):
    """robots.txt says this agent may fetch the URL (unknown means yes)."""
    parts = urlparse(url)
    root = f'{parts.scheme}://{parts.netloc}'
    if root not in _robots:
        parser = RobotFileParser()
        try:
            reply = requests.get(root + '/robots.txt', timeout=6,
                                 headers={'User-Agent': USER_AGENT})
            parser.parse(reply.text.splitlines()
                         if reply.status_code == 200 else [])
        except requests.RequestException:
            parser.parse([])
        _robots[root] = parser
    return _robots[root].can_fetch(USER_AGENT, url)


def download(url):
    response = requests.get(url, timeout=TIMEOUT, stream=True,
                            headers={'User-Agent': USER_AGENT})
    response.raise_for_status()
    body = b''
    for part in response.iter_content(65536):
        body += part
        if len(body) > MAX_BYTES:
            break
    return response.headers.get('Content-Type', ''), body, response.url


def html_blocks(html, base_url):
    """[(kind, text)] in reading order, plus the page's outgoing links."""
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html, 'lxml')
    title = soup.title.get_text(' ', strip=True) if soup.title else ''
    for tag in soup(['script', 'style', 'noscript', 'nav', 'footer',
                     'header', 'aside', 'form', 'svg', 'button']):
        tag.decompose()
    root = soup.find('article') or soup.find('main') or soup.body or soup
    links = {urljoin(base_url, a['href']).split('#')[0]
             for a in root.find_all('a', href=True)}
    blocks = []
    for node in root.find_all(['h1', 'h2', 'h3', 'h4', 'p', 'li',
                               'blockquote', 'pre', 'td']):
        if node.find_parent(['li', 'blockquote']) and node.name == 'p':
            continue
        text = ' '.join(node.get_text(' ', strip=True).split())
        if node.name.startswith('h'):
            blocks.append(('heading', text))
        elif len(text.split()) >= 6:
            blocks.append(('text', text))
    return title, blocks, links


def pdf_blocks(body):
    import fitz
    with fitz.open(stream=body, filetype='pdf') as doc:
        text = '\n'.join(page.get_text() for page in doc.pages(0, 30))
    paragraphs = [' '.join(p.split()) for p in re.split(r'\n\s*\n', text)]
    return [('text', p) for p in paragraphs if len(p.split()) >= 6]


def chunks(blocks):
    """Merge blocks into chunks of about CHUNK_WORDS words, starting a new
    chunk at each heading and carrying the heading as the chunk's label."""
    found, current, heading, size = [], [], '', 0

    def flush():
        if current:          # blocks: to find the passage in the page later
            found.append({'heading': heading, 'text': ' '.join(current),
                          'blocks': list(current)})
    for kind, text in blocks:
        if kind == 'heading':
            flush()
            current, heading, size = [], text, 0
            continue
        words = len(text.split())
        if current and size + words > CHUNK_WORDS:
            flush()
            current, size = [], 0
        current.append(text)
        size += words
    flush()
    return found[:MAX_CHUNKS]


def fetch(url):
    """A page as {url, title, chunks, links} or {url, error}."""
    if not url.startswith(('http://', 'https://')):
        return {'url': url, 'error': 'not a web address'}
    try:
        if not allowed(url):
            return {'url': url, 'error': 'robots.txt does not allow it'}
        kind, body, final = download(url)
    except requests.RequestException as error:
        return {'url': url, 'error': type(error).__name__}
    is_pdf = 'pdf' in kind or final.lower().endswith('.pdf')
    try:
        if is_pdf:
            title, blocks, links = '', pdf_blocks(body), set()
        elif 'html' in kind or not kind:
            title, blocks, links = html_blocks(body, final)
        else:
            return {'url': url, 'error': f'unsupported content: {kind}'}
    except Exception as error:        # a malformed page is skipped, not fatal
        return {'url': url,
                'error': f'could not parse: {type(error).__name__}'}
    found = chunks(blocks)
    if not found:
        return {'url': url, 'error': 'no readable text'}
    return {'url': url, 'final_url': final, 'title': title,
            'chunks': found, 'links': sorted(links), 'raw': body,
            'kind': 'pdf' if is_pdf else 'html'}
