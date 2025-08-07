"""Long-term memory system with hierarchical storage and summarization."""

import logging
import json
import pickle
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from pathlib import Path
import re
import hashlib


@dataclass
class MemoryEntry:
    """A single memory entry with metadata."""
    content: str
    timestamp: datetime
    importance: float
    characters: List[str]
    emotions: List[str]
    tags: List[str]
    context_hash: str
    summary: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "importance": self.importance,
            "characters": self.characters,
            "emotions": self.emotions,
            "tags": self.tags,
            "context_hash": self.context_hash,
            "summary": self.summary
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MemoryEntry":
        """Create from dictionary."""
        return cls(
            content=data["content"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            importance=data["importance"],
            characters=data["characters"],
            emotions=data["emotions"],
            tags=data["tags"],
            context_hash=data["context_hash"],
            summary=data.get("summary")
        )


class MemorySystem:
    """Hierarchical memory system for long-term RP context preservation."""
    
    def __init__(self, storage_path: Optional[str] = None):
        """Initialize memory system.
        
        Args:
            storage_path: Path to store memory files
        """
        self.storage_path = Path(storage_path) if storage_path else Path("rp_memory")
        self.storage_path.mkdir(exist_ok=True)
        
        self.logger = logging.getLogger(__name__)
        
        # Memory stores
        self.recent_memories: List[MemoryEntry] = []  # Last 24 hours
        self.important_memories: List[MemoryEntry] = []  # High importance
        self.character_memories: Dict[str, List[MemoryEntry]] = {}  # Per character
        self.summaries: List[MemoryEntry] = []  # Compressed memories
        
        # Configuration
        self.max_recent_memories = 100
        self.max_important_memories = 50
        self.max_character_memories = 30
        self.importance_threshold = 0.7
        
        # Load existing memories
        self._load_memories()
        
        self.logger.info(f"Initialized memory system with storage at {self.storage_path}")
    
    def add_memory(
        self,
        content: str,
        characters: List[str] = None,
        emotions: List[str] = None,
        tags: List[str] = None,
        importance: float = 0.5,
        context: str = ""
    ) -> MemoryEntry:
        """Add a new memory entry.
        
        Args:
            content: Memory content
            characters: Characters involved
            emotions: Emotional tags
            tags: Additional tags
            importance: Importance score (0.0-1.0)
            context: Context for duplicate detection
            
        Returns:
            Created memory entry
        """
        # Create context hash for duplicate detection
        context_hash = hashlib.md5(
            (content + (context or "")).encode()
        ).hexdigest()
        
        # Check for duplicates
        if self._is_duplicate(context_hash):
            self.logger.debug("Skipping duplicate memory")
            return None
        
        memory = MemoryEntry(
            content=content,
            timestamp=datetime.now(),
            importance=importance,
            characters=characters or [],
            emotions=emotions or [],
            tags=tags or [],
            context_hash=context_hash
        )
        
        # Auto-tag based on content
        memory.tags.extend(self._extract_tags(content))
        
        # Add to appropriate stores
        self.recent_memories.append(memory)
        
        if importance >= self.importance_threshold:
            self.important_memories.append(memory)
        
        # Add to character-specific memories
        for character in memory.characters:
            if character not in self.character_memories:
                self.character_memories[character] = []
            self.character_memories[character].append(memory)
        
        # Maintain memory limits
        self._trim_memories()
        
        # Auto-save
        self._save_memories()
        
        self.logger.debug(f"Added memory: {len(content)} chars, importance {importance}")
        return memory
    
    def _is_duplicate(self, context_hash: str) -> bool:
        """Check if memory is duplicate based on context hash."""
        all_memories = (
            self.recent_memories + 
            self.important_memories + 
            self.summaries
        )
        
        for memory in all_memories:
            if memory.context_hash == context_hash:
                return True
        return False
    
    def _extract_tags(self, content: str) -> List[str]:
        """Extract tags from content using pattern matching."""
        tags = []
        
        # Common RP tags
        tag_patterns = {
            r'\b(fight|battle|combat|attack)\b': 'combat',
            r'\b(love|romance|kiss|hug|affection)\b': 'romance',
            r'\b(death|die|dead|kill|murder)\b': 'death',
            r'\b(magic|spell|power|ability)\b': 'magic',
            r'\b(travel|journey|move|go)\b': 'travel',
            r'\b(secret|hidden|mystery)\b': 'mystery',
            r'\b(fear|scared|afraid|terror)\b': 'fear',
            r'\b(happy|joy|laugh|smile)\b': 'joy',
            r'\b(sad|cry|tears|sorrow)\b': 'sadness',
            r'\b(angry|rage|fury|mad)\b': 'anger'
        }
        
        content_lower = content.lower()
        for pattern, tag in tag_patterns.items():
            if re.search(pattern, content_lower):
                tags.append(tag)
        
        return tags
    
    def _trim_memories(self) -> None:
        """Trim memory stores to maintain limits."""
        # Trim recent memories by time and count
        cutoff = datetime.now() - timedelta(hours=24)
        self.recent_memories = [
            m for m in self.recent_memories 
            if m.timestamp > cutoff
        ]
        
        if len(self.recent_memories) > self.max_recent_memories:
            self.recent_memories.sort(key=lambda x: x.timestamp, reverse=True)
            # Move excess to summaries if important enough
            excess = self.recent_memories[self.max_recent_memories:]
            self.recent_memories = self.recent_memories[:self.max_recent_memories]
            
            for memory in excess:
                if memory.importance > 0.5:
                    self.summaries.append(memory)
        
        # Trim important memories
        if len(self.important_memories) > self.max_important_memories:
            self.important_memories.sort(key=lambda x: x.importance, reverse=True)
            excess = self.important_memories[self.max_important_memories:]
            self.important_memories = self.important_memories[:self.max_important_memories]
            
            self.summaries.extend(excess)
        
        # Trim character memories
        for character in self.character_memories:
            memories = self.character_memories[character]
            if len(memories) > self.max_character_memories:
                memories.sort(key=lambda x: (x.importance, x.timestamp), reverse=True)
                self.character_memories[character] = memories[:self.max_character_memories]
    
    def retrieve_memories(
        self,
        query: str = "",
        characters: List[str] = None,
        tags: List[str] = None,
        emotions: List[str] = None,
        limit: int = 10,
        min_importance: float = 0.0
    ) -> List[MemoryEntry]:
        """Retrieve relevant memories based on criteria.
        
        Args:
            query: Text query to match against content
            characters: Characters to filter by
            tags: Tags to filter by
            emotions: Emotions to filter by
            limit: Maximum number of memories to return
            min_importance: Minimum importance threshold
            
        Returns:
            List of matching memories
        """
        all_memories = (
            self.recent_memories + 
            self.important_memories + 
            self.summaries
        )
        
        # Remove duplicates by hash
        seen_hashes = set()
        unique_memories = []
        for memory in all_memories:
            if memory.context_hash not in seen_hashes:
                unique_memories.append(memory)
                seen_hashes.add(memory.context_hash)
        
        # Apply filters
        filtered = []
        for memory in unique_memories:
            if memory.importance < min_importance:
                continue
            
            if characters and not any(char in memory.characters for char in characters):
                continue
            
            if tags and not any(tag in memory.tags for tag in tags):
                continue
            
            if emotions and not any(emotion in memory.emotions for emotion in emotions):
                continue
            
            if query:
                query_lower = query.lower()
                content_lower = memory.content.lower()
                if query_lower not in content_lower:
                    # Also check summary if available
                    if memory.summary and query_lower not in memory.summary.lower():
                        continue
            
            filtered.append(memory)
        
        # Sort by relevance (importance + recency)
        def relevance_score(memory: MemoryEntry) -> float:
            age_hours = (datetime.now() - memory.timestamp).total_seconds() / 3600
            age_factor = max(0.1, 1.0 - (age_hours / (24 * 7)))  # Decay over week
            return memory.importance * 0.7 + age_factor * 0.3
        
        filtered.sort(key=relevance_score, reverse=True)
        
        return filtered[:limit]
    
    def get_character_memories(self, character: str, limit: int = 10) -> List[MemoryEntry]:
        """Get memories specific to a character.
        
        Args:
            character: Character name
            limit: Maximum memories to return
            
        Returns:
            Character-specific memories
        """
        if character not in self.character_memories:
            return []
        
        memories = self.character_memories[character]
        memories.sort(key=lambda x: (x.importance, x.timestamp), reverse=True)
        
        return memories[:limit]
    
    def summarize_memories(
        self,
        memories: List[MemoryEntry],
        target_length: int = 500
    ) -> str:
        """Create a summary of multiple memories.
        
        Args:
            memories: Memories to summarize
            target_length: Target summary length in characters
            
        Returns:
            Summary text
        """
        if not memories:
            return ""
        
        # Group by importance and recency
        high_importance = [m for m in memories if m.importance > 0.7]
        recent = [m for m in memories if (datetime.now() - m.timestamp).days < 1]
        
        # Build summary sections
        summary_parts = []
        
        if high_importance:
            key_events = []
            for memory in high_importance[:5]:  # Top 5 important
                key_events.append(f"• {memory.content[:100]}...")
            summary_parts.append("Key Events:\n" + "\n".join(key_events))
        
        if recent:
            recent_events = []
            for memory in recent[:3]:  # Last 3 recent
                recent_events.append(f"• {memory.content[:100]}...")
            summary_parts.append("Recent Events:\n" + "\n".join(recent_events))
        
        # Character relationships
        all_characters = set()
        for memory in memories:
            all_characters.update(memory.characters)
        
        if all_characters:
            summary_parts.append(f"Characters involved: {', '.join(sorted(all_characters))}")
        
        summary = "\n\n".join(summary_parts)
        
        # Trim to target length
        if len(summary) > target_length:
            summary = summary[:target_length-3] + "..."
        
        return summary
    
    def compress_old_memories(self, days_old: int = 7) -> int:
        """Compress old memories into summaries.
        
        Args:
            days_old: Age threshold in days
            
        Returns:
            Number of memories compressed
        """
        cutoff = datetime.now() - timedelta(days=days_old)
        
        # Find old memories
        old_memories = []
        
        # Check recent memories
        recent_old = [m for m in self.recent_memories if m.timestamp < cutoff]
        self.recent_memories = [m for m in self.recent_memories if m.timestamp >= cutoff]
        old_memories.extend(recent_old)
        
        # Don't compress important memories or summaries
        
        if old_memories:
            # Create summary
            summary_text = self.summarize_memories(old_memories)
            
            # Create summary memory entry
            summary_memory = MemoryEntry(
                content=f"[COMPRESSED SUMMARY - {len(old_memories)} memories from {cutoff.date()}]\n{summary_text}",
                timestamp=datetime.now(),
                importance=0.6,
                characters=list(set().union(*[m.characters for m in old_memories])),
                emotions=list(set().union(*[m.emotions for m in old_memories])),
                tags=["summary"] + list(set().union(*[m.tags for m in old_memories])),
                context_hash=hashlib.md5(summary_text.encode()).hexdigest(),
                summary=summary_text
            )
            
            self.summaries.append(summary_memory)
            
            self.logger.info(f"Compressed {len(old_memories)} old memories into summary")
            self._save_memories()
            
            return len(old_memories)
        
        return 0
    
    def _save_memories(self) -> None:
        """Save memories to disk."""
        try:
            memory_data = {
                "recent": [m.to_dict() for m in self.recent_memories],
                "important": [m.to_dict() for m in self.important_memories],
                "summaries": [m.to_dict() for m in self.summaries],
                "characters": {
                    char: [m.to_dict() for m in memories]
                    for char, memories in self.character_memories.items()
                }
            }
            
            with open(self.storage_path / "memories.json", "w") as f:
                json.dump(memory_data, f, indent=2, default=str)
            
            self.logger.debug("Saved memories to disk")
            
        except Exception as e:
            self.logger.error(f"Failed to save memories: {e}")
    
    def _load_memories(self) -> None:
        """Load memories from disk."""
        memory_file = self.storage_path / "memories.json"
        
        if not memory_file.exists():
            return
        
        try:
            with open(memory_file) as f:
                memory_data = json.load(f)
            
            self.recent_memories = [
                MemoryEntry.from_dict(m) for m in memory_data.get("recent", [])
            ]
            
            self.important_memories = [
                MemoryEntry.from_dict(m) for m in memory_data.get("important", [])
            ]
            
            self.summaries = [
                MemoryEntry.from_dict(m) for m in memory_data.get("summaries", [])
            ]
            
            self.character_memories = {}
            for char, memories in memory_data.get("characters", {}).items():
                self.character_memories[char] = [
                    MemoryEntry.from_dict(m) for m in memories
                ]
            
            self.logger.info(f"Loaded {len(self.recent_memories)} recent, "
                           f"{len(self.important_memories)} important, "
                           f"{len(self.summaries)} summary memories")
            
        except Exception as e:
            self.logger.error(f"Failed to load memories: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get memory system statistics.
        
        Returns:
            Statistics dictionary
        """
        total_memories = (
            len(self.recent_memories) + 
            len(self.important_memories) + 
            len(self.summaries)
        )
        
        character_counts = {
            char: len(memories) 
            for char, memories in self.character_memories.items()
        }
        
        return {
            "total_memories": total_memories,
            "recent_memories": len(self.recent_memories),
            "important_memories": len(self.important_memories),
            "summaries": len(self.summaries),
            "characters": len(self.character_memories),
            "character_memory_counts": character_counts,
            "storage_path": str(self.storage_path)
        }