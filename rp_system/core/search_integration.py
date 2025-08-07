"""Smart web search integration for contextual RP enhancement."""

import logging
import requests
import json
import time
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from urllib.parse import quote_plus
import re


@dataclass
class SearchResult:
    """A search result with metadata."""
    title: str
    content: str
    url: str
    relevance_score: float
    source_type: str  # 'wiki', 'fandom', 'general'


class SearchIntegration:
    """Contextual web search for RP enhancement."""
    
    def __init__(self, enable_search: bool = True):
        """Initialize search integration.
        
        Args:
            enable_search: Whether to enable web search
        """
        self.enable_search = enable_search
        self.logger = logging.getLogger(__name__)
        
        # Rate limiting
        self.last_search_time = 0
        self.min_search_interval = 2.0  # Seconds between searches
        
        # Search cache
        self.search_cache: Dict[str, List[SearchResult]] = {}
        self.cache_max_age = 3600  # 1 hour cache
        self.cache_timestamps: Dict[str, float] = {}
        
        # Known fictional universes that benefit from search
        self.fictional_universes = {
            'rezero', 're:zero', 'subaru', 'emilia', 'rem', 'ram',
            'overlord', 'ainz', 'nazarick',
            'konosuba', 'kazuma', 'aqua', 'megumin', 'darkness',
            'shield hero', 'naofumi', 'raphtalia',
            'slime', 'rimuru', 'tempest',
            'goblin slayer', 'priestess',
            'danmachi', 'bell', 'hestia',
            'fate', 'saber', 'archer', 'rider', 'lancer', 'caster', 'assassin', 'berserker',
            'naruto', 'sasuke', 'sakura', 'kakashi', 'konoha',
            'one piece', 'luffy', 'zoro', 'nami', 'sanji',
            'dragon ball', 'goku', 'vegeta', 'gohan',
            'bleach', 'ichigo', 'rukia', 'soul society',
            'attack on titan', 'eren', 'mikasa', 'armin', 'titan',
            'my hero academia', 'deku', 'bakugo', 'todoroki', 'quirk',
            'jujutsu kaisen', 'yuji', 'megumi', 'nobara', 'cursed'
        }
        
        self.logger.info(f"Initialized search integration (enabled: {enable_search})")
    
    def should_search(
        self,
        query: str,
        context: str,
        character_names: List[str] = None
    ) -> bool:
        """Determine if a search should be performed.
        
        Args:
            query: Search query
            context: Current RP context
            character_names: Known character names
            
        Returns:
            True if search is warranted
        """
        if not self.enable_search:
            return False
        
        query_lower = query.lower()
        context_lower = context.lower()
        
        # Don't search for basic conversation
        basic_patterns = [
            r'\b(hello|hi|how are you|what\'s up|good morning|good night)\b',
            r'\b(yes|no|maybe|sure|okay|alright)\b',
            r'\b(thanks|thank you|please|sorry|excuse me)\b'
        ]
        
        for pattern in basic_patterns:
            if re.search(pattern, query_lower):
                return False
        
        # Don't search for personal user info
        personal_patterns = [
            r'\b(my name is|i am|i\'m|me|myself)\b',
            r'\b(real life|irl|personally)\b'
        ]
        
        for pattern in personal_patterns:
            if re.search(pattern, query_lower):
                return False
        
        # Search for unknown characters in known universes
        for universe_term in self.fictional_universes:
            if universe_term in context_lower or universe_term in query_lower:
                # Check if query mentions unknown characters
                potential_characters = re.findall(r'\b[A-Z][a-z]+\b', query)
                known_chars = character_names or []
                
                for char in potential_characters:
                    if char.lower() not in [c.lower() for c in known_chars]:
                        self.logger.debug(f"Unknown character '{char}' in known universe, should search")
                        return True
        
        # Search for world-building details
        worldbuilding_terms = [
            'magic system', 'power', 'ability', 'spell', 'technique',
            'location', 'city', 'kingdom', 'world', 'dimension',
            'organization', 'guild', 'clan', 'group',
            'item', 'weapon', 'artifact', 'tool',
            'race', 'species', 'monster', 'creature',
            'history', 'lore', 'legend', 'myth'
        ]
        
        for term in worldbuilding_terms:
            if term in query_lower:
                self.logger.debug(f"World-building term '{term}' detected, should search")
                return True
        
        # Search for technical details in sci-fi
        scifi_terms = [
            'technology', 'ship', 'weapon', 'device',
            'alien', 'species', 'planet', 'star system',
            'hyperspace', 'warp', 'ftl', 'faster than light'
        ]
        
        if any(term in context_lower for term in ['sci-fi', 'science fiction', 'space', 'future']):
            for term in scifi_terms:
                if term in query_lower:
                    self.logger.debug(f"Sci-fi term '{term}' detected, should search")
                    return True
        
        return False
    
    def search(
        self,
        query: str,
        context: str = "",
        max_results: int = 3
    ) -> List[SearchResult]:
        """Perform a contextual search.
        
        Args:
            query: Search query
            context: RP context for relevance
            max_results: Maximum results to return
            
        Returns:
            List of search results
        """
        if not self.enable_search:
            return []
        
        # Rate limiting
        now = time.time()
        if now - self.last_search_time < self.min_search_interval:
            self.logger.debug("Search rate limited")
            return []
        
        # Check cache
        cache_key = f"{query.lower()}:{len(context)}"
        if (cache_key in self.search_cache and 
            cache_key in self.cache_timestamps and
            now - self.cache_timestamps[cache_key] < self.cache_max_age):
            self.logger.debug("Returning cached search results")
            return self.search_cache[cache_key][:max_results]
        
        self.last_search_time = now
        
        try:
            results = []
            
            # Try different search strategies
            results.extend(self._search_duckduckgo(query, max_results))
            
            # Filter and rank by relevance
            filtered_results = self._filter_and_rank(results, query, context)
            
            # Cache results
            self.search_cache[cache_key] = filtered_results
            self.cache_timestamps[cache_key] = now
            
            self.logger.info(f"Search for '{query}' returned {len(filtered_results)} results")
            return filtered_results[:max_results]
            
        except Exception as e:
            self.logger.error(f"Search failed: {e}")
            return []
    
    def _search_duckduckgo(self, query: str, max_results: int) -> List[SearchResult]:
        """Search using DuckDuckGo instant answer API.
        
        Args:
            query: Search query
            max_results: Maximum results
            
        Returns:
            Search results
        """
        results = []
        
        try:
            # DuckDuckGo instant answer API
            url = "https://api.duckduckgo.com/"
            params = {
                'q': query,
                'format': 'json',
                'no_html': '1',
                'skip_disambig': '1'
            }
            
            response = requests.get(url, params=params, timeout=5)
            response.raise_for_status()
            
            data = response.json()
            
            # Abstract
            if data.get('Abstract'):
                results.append(SearchResult(
                    title=data.get('AbstractSource', 'Wikipedia'),
                    content=data['Abstract'],
                    url=data.get('AbstractURL', ''),
                    relevance_score=0.9,
                    source_type='wiki'
                ))
            
            # Related topics
            for topic in data.get('RelatedTopics', [])[:2]:
                if isinstance(topic, dict) and topic.get('Text'):
                    results.append(SearchResult(
                        title=topic.get('FirstURL', '').split('/')[-1].replace('_', ' '),
                        content=topic['Text'],
                        url=topic.get('FirstURL', ''),
                        relevance_score=0.7,
                        source_type='wiki'
                    ))
            
        except Exception as e:
            self.logger.warning(f"DuckDuckGo search failed: {e}")
        
        return results
    
    def _filter_and_rank(
        self,
        results: List[SearchResult],
        query: str,
        context: str
    ) -> List[SearchResult]:
        """Filter and rank search results by relevance.
        
        Args:
            results: Raw search results
            query: Original query
            context: RP context
            
        Returns:
            Filtered and ranked results
        """
        if not results:
            return []
        
        query_words = set(query.lower().split())
        context_words = set(context.lower().split())
        
        scored_results = []
        
        for result in results:
            score = result.relevance_score
            
            content_words = set(result.content.lower().split())
            title_words = set(result.title.lower().split())
            
            # Boost score for query word matches
            query_matches = len(query_words.intersection(content_words))
            title_matches = len(query_words.intersection(title_words))
            
            score += query_matches * 0.1
            score += title_matches * 0.2
            
            # Boost for context relevance
            context_matches = len(context_words.intersection(content_words))
            score += min(context_matches * 0.05, 0.3)
            
            # Boost trusted sources
            if result.source_type == 'wiki':
                score += 0.2
            elif 'fandom' in result.url.lower():
                score += 0.15
            
            # Penalize very short content
            if len(result.content) < 50:
                score -= 0.3
            
            # Penalize irrelevant content
            irrelevant_terms = ['disambiguation', 'may refer to', 'see also']
            if any(term in result.content.lower() for term in irrelevant_terms):
                score -= 0.4
            
            scored_results.append((score, result))
        
        # Sort by score and return results
        scored_results.sort(key=lambda x: x[0], reverse=True)
        
        # Filter out very low scoring results
        filtered = [result for score, result in scored_results if score > 0.3]
        
        return filtered
    
    def format_search_results(
        self,
        results: List[SearchResult],
        max_length: int = 800
    ) -> str:
        """Format search results for inclusion in RP context.
        
        Args:
            results: Search results to format
            max_length: Maximum total length
            
        Returns:
            Formatted search information
        """
        if not results:
            return ""
        
        formatted_parts = ["[SEARCH RESULTS]"]
        
        current_length = len(formatted_parts[0])
        
        for i, result in enumerate(results):
            if i >= 3:  # Limit to top 3 results
                break
            
            # Format result
            result_text = f"\n{result.title}: {result.content}"
            
            # Truncate if too long
            if current_length + len(result_text) > max_length:
                remaining = max_length - current_length - 20
                if remaining > 50:
                    result_text = f"\n{result.title}: {result.content[:remaining]}..."
                else:
                    break
            
            formatted_parts.append(result_text)
            current_length += len(result_text)
        
        return "".join(formatted_parts)
    
    def clear_cache(self) -> None:
        """Clear the search cache."""
        self.search_cache.clear()
        self.cache_timestamps.clear()
        self.logger.info("Search cache cleared")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get search statistics.
        
        Returns:
            Statistics dictionary
        """
        return {
            "enabled": self.enable_search,
            "cache_size": len(self.search_cache),
            "last_search": self.last_search_time,
            "fictional_universes": len(self.fictional_universes)
        }