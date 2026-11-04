"""Search engines for agentic search: each returns its top results, ranked.

DuckDuckGo works without a key through the unofficial ddgs library, which
can be rate-limited or break when DuckDuckGo changes. Google and Bing have no
open official API for new users, so they come through a results provider:
set SERPAPI_API_KEY in the environment (never in code) to enable them.
"""
import os

import requests


class DuckDuckGo:
    name, label = 'duckduckgo', 'DuckDuckGo'

    def available(self):
        return True, 'no key needed (unofficial library)'

    def search(self, query, top_n):
        from ddgs import DDGS
        found = DDGS().text(query, max_results=top_n, backend='duckduckgo')
        return [{'title': r.get('title', ''), 'url': r.get('href', ''),
                 'snippet': r.get('body', '')} for r in found][:top_n]


class SerpApiEngine:
    """Google or Bing results through SerpApi (one key for both)."""

    def __init__(self, name, label):
        self.name, self.label = name, label

    def available(self):
        if os.environ.get('SERPAPI_API_KEY'):
            return True, 'via SerpApi'
        return False, 'set SERPAPI_API_KEY to enable'

    def search(self, query, top_n):
        response = requests.get('https://serpapi.com/search.json', params={
            'engine': self.name, 'q': query, 'num': top_n,
            'api_key': os.environ['SERPAPI_API_KEY']}, timeout=30)
        response.raise_for_status()
        found = response.json().get('organic_results', [])
        return [{'title': r.get('title', ''), 'url': r.get('link', ''),
                 'snippet': r.get('snippet', '')} for r in found][:top_n]


ENGINES = {engine.name: engine for engine in [
    DuckDuckGo(), SerpApiEngine('google', 'Google'),
    SerpApiEngine('bing', 'Bing')]}


def status():
    """Which engines can run, for the page's settings."""
    return [{'name': e.name, 'label': e.label,
             'available': e.available()[0], 'note': e.available()[1]}
            for e in ENGINES.values()]
