"""Intelligent context window management for 1M token optimization."""

import logging
import json
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
import re


@dataclass
class ContextSegment:
    """A segment of context with metadata."""
    content: str
    tokens: int
    timestamp: datetime
    importance: float  # 0.0 to 1.0
    segment_type: str  # 'recent', 'character', 'world', 'summary', 'memory'
    characters: List[str] = None
    emotions: List[str] = None
    
    def __post_init__(self):
        if self.characters is None:
            self.characters = []
        if self.emotions is None:
            self.emotions = []


class ContextManager:
    """Intelligent context window management for optimal RP experience."""
    
    def __init__(self, max_tokens: int = 950000):  # Leave room for response
        """Initialize context manager.
        
        Args:
            max_tokens: Maximum tokens to use for context
        """
        self.max_tokens = max_tokens
        self.logger = logging.getLogger(__name__)
        
        # Context segments by priority
        self.recent_context: List[ContextSegment] = []
        self.character_sheets: List[ContextSegment] = []
        self.world_state: List[ContextSegment] = []
        self.memory_segments: List[ContextSegment] = []
        self.summaries: List[ContextSegment] = []
        
        # Configuration
        self.recent_token_reserve = 30000  # Always preserve recent context
        self.character_token_reserve = 20000  # Character sheets priority
        self.world_token_reserve = 15000  # World state priority
        
        self.logger.info(f"Initialized context manager with {max_tokens} token limit")
    
    def add_message(
        self,
        content: str,
        tokens: int,
        message_type: str = "conversation",
        characters: List[str] = None,
        emotions: List[str] = None,
        importance: float = 0.5
    ) -> None:
        """Add a new message to recent context.
        
        Args:
            content: Message content
            tokens: Token count
            message_type: Type of message
            characters: Characters involved
            emotions: Emotional tags
            importance: Importance score (0.0-1.0)
        """
        segment = ContextSegment(
            content=content,
            tokens=tokens,
            timestamp=datetime.now(),
            importance=importance,
            segment_type="recent",
            characters=characters or [],
            emotions=emotions or []
        )
        
        self.recent_context.append(segment)
        self.logger.debug(f"Added message: {tokens} tokens, importance {importance}")
        
        # Auto-compress if we're getting too large
        if self._total_tokens() > self.max_tokens:
            self._compress_context()
    
    def set_character_sheet(self, character_name: str, sheet_content: str, tokens: int) -> None:
        """Set or update a character sheet.
        
        Args:
            character_name: Character name
            sheet_content: Character sheet content
            tokens: Token count
        """
        # Remove existing sheet for this character
        self.character_sheets = [
            s for s in self.character_sheets 
            if character_name not in s.characters
        ]
        
        segment = ContextSegment(
            content=sheet_content,
            tokens=tokens,
            timestamp=datetime.now(),
            importance=1.0,  # Character sheets are high importance
            segment_type="character",
            characters=[character_name]
        )
        
        self.character_sheets.append(segment)
        self.logger.info(f"Updated character sheet for {character_name}: {tokens} tokens")
    
    def set_world_state(self, state_content: str, tokens: int) -> None:
        """Set or update world state.
        
        Args:
            state_content: World state content
            tokens: Token count
        """
        segment = ContextSegment(
            content=state_content,
            tokens=tokens,
            timestamp=datetime.now(),
            importance=0.9,  # World state is high importance
            segment_type="world"
        )
        
        self.world_state = [segment]  # Replace existing world state
        self.logger.info(f"Updated world state: {tokens} tokens")
    
    def add_memory(self, memory_content: str, tokens: int, importance: float = 0.7) -> None:
        """Add a memory segment.
        
        Args:
            memory_content: Memory content
            tokens: Token count
            importance: Importance score
        """
        segment = ContextSegment(
            content=memory_content,
            tokens=tokens,
            timestamp=datetime.now(),
            importance=importance,
            segment_type="memory"
        )
        
        self.memory_segments.append(segment)
        self.logger.debug(f"Added memory: {tokens} tokens, importance {importance}")
    
    def add_summary(self, summary_content: str, tokens: int, covered_range: str = "") -> None:
        """Add a summary segment.
        
        Args:
            summary_content: Summary content
            tokens: Token count
            covered_range: Description of what this summary covers
        """
        segment = ContextSegment(
            content=f"[SUMMARY: {covered_range}]\n{summary_content}",
            tokens=tokens,
            timestamp=datetime.now(),
            importance=0.6,
            segment_type="summary"
        )
        
        self.summaries.append(segment)
        self.logger.info(f"Added summary: {tokens} tokens, covers {covered_range}")
    
    def _total_tokens(self) -> int:
        """Calculate total tokens across all segments."""
        total = 0
        for segment_list in [
            self.recent_context,
            self.character_sheets,
            self.world_state,
            self.memory_segments,
            self.summaries
        ]:
            total += sum(s.tokens for s in segment_list)
        return total
    
    def _compress_context(self) -> None:
        """Compress context to fit within token limits."""
        self.logger.info("Starting context compression")
        
        # Always preserve recent context (last N tokens)
        recent_tokens = sum(s.tokens for s in self.recent_context)
        if recent_tokens > self.recent_token_reserve:
            # Move older messages to memory/summary
            self._archive_old_messages()
        
        # If still over limit, compress summaries and memories
        if self._total_tokens() > self.max_tokens:
            self._compress_memories()
        
        # Final check - remove lowest importance items if needed
        if self._total_tokens() > self.max_tokens:
            self._remove_low_importance()
        
        self.logger.info(f"Context compression complete: {self._total_tokens()} tokens")
    
    def _archive_old_messages(self) -> None:
        """Move old messages from recent context to summaries."""
        if len(self.recent_context) <= 5:  # Keep minimum recent messages
            return
        
        # Keep last 20 messages or recent_token_reserve worth, whichever is more
        keep_tokens = 0
        keep_count = 0
        
        for i in range(len(self.recent_context) - 1, -1, -1):
            keep_tokens += self.recent_context[i].tokens
            keep_count += 1
            
            if keep_tokens >= self.recent_token_reserve and keep_count >= 20:
                break
        
        if keep_count < len(self.recent_context):
            # Archive older messages
            to_archive = self.recent_context[:-keep_count]
            self.recent_context = self.recent_context[-keep_count:]
            
            # Create summary of archived messages
            archived_content = "\n".join(s.content for s in to_archive)
            archived_tokens = sum(s.tokens for s in to_archive)
            
            # This would be replaced with actual AI summarization
            summary = f"Summary of {len(to_archive)} messages ({archived_tokens} tokens): Key events and character interactions from recent conversation."
            
            self.add_summary(summary, archived_tokens // 4, f"{len(to_archive)} messages")
            
            self.logger.debug(f"Archived {len(to_archive)} messages to summary")
    
    def _compress_memories(self) -> None:
        """Compress memory segments by combining similar ones."""
        if len(self.memory_segments) <= 3:
            return
        
        # Sort by importance and keep top memories
        self.memory_segments.sort(key=lambda x: x.importance, reverse=True)
        
        if len(self.memory_segments) > 10:
            # Combine lower importance memories into summaries
            to_compress = self.memory_segments[10:]
            self.memory_segments = self.memory_segments[:10]
            
            if to_compress:
                combined_content = "\n".join(s.content for s in to_compress)
                combined_tokens = sum(s.tokens for s in to_compress)
                
                summary = f"Combined memories: {combined_content[:200]}..."
                self.add_summary(summary, combined_tokens // 3, f"{len(to_compress)} memories")
    
    def _remove_low_importance(self) -> None:
        """Remove lowest importance segments as last resort."""
        # Collect all non-essential segments
        removable = []
        
        for segment_list, min_keep in [
            (self.summaries, 1),
            (self.memory_segments, 2),
        ]:
            if len(segment_list) > min_keep:
                removable.extend(segment_list[min_keep:])
        
        # Sort by importance and remove lowest
        removable.sort(key=lambda x: x.importance)
        
        removed_tokens = 0
        while removable and self._total_tokens() > self.max_tokens:
            segment = removable.pop(0)
            removed_tokens += segment.tokens
            
            # Remove from appropriate list
            for segment_list in [self.summaries, self.memory_segments]:
                if segment in segment_list:
                    segment_list.remove(segment)
                    break
        
        if removed_tokens > 0:
            self.logger.warning(f"Removed {removed_tokens} tokens of low-importance content")
    
    def build_context(self, system_prompt: str = "") -> str:
        """Build the complete context for API call.
        
        Args:
            system_prompt: System prompt to include
            
        Returns:
            Complete context string
        """
        context_parts = []
        
        # System prompt first
        if system_prompt:
            context_parts.append(system_prompt)
        
        # Character sheets
        for segment in self.character_sheets:
            context_parts.append(f"[CHARACTER SHEET]\n{segment.content}")
        
        # World state
        for segment in self.world_state:
            context_parts.append(f"[WORLD STATE]\n{segment.content}")
        
        # Summaries
        for segment in self.summaries:
            context_parts.append(segment.content)
        
        # Important memories
        high_importance_memories = [
            s for s in self.memory_segments 
            if s.importance > 0.7
        ]
        for segment in high_importance_memories:
            context_parts.append(f"[MEMORY]\n{segment.content}")
        
        # Recent context
        for segment in self.recent_context:
            context_parts.append(segment.content)
        
        context = "\n\n".join(context_parts)
        
        self.logger.info(f"Built context: {self._total_tokens()} tokens")
        return context
    
    def get_character_context(self, character_name: str) -> str:
        """Get context specific to a character.
        
        Args:
            character_name: Character to get context for
            
        Returns:
            Character-specific context
        """
        parts = []
        
        # Character sheet
        for segment in self.character_sheets:
            if character_name in segment.characters:
                parts.append(segment.content)
        
        # Relevant memories
        for segment in self.memory_segments:
            if character_name in segment.characters:
                parts.append(segment.content)
        
        # Recent mentions
        for segment in self.recent_context[-10:]:  # Last 10 messages
            if character_name in segment.characters or character_name.lower() in segment.content.lower():
                parts.append(segment.content)
        
        return "\n\n".join(parts)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get context statistics.
        
        Returns:
            Statistics dictionary
        """
        return {
            "total_tokens": self._total_tokens(),
            "max_tokens": self.max_tokens,
            "utilization": self._total_tokens() / self.max_tokens,
            "segments": {
                "recent": len(self.recent_context),
                "characters": len(self.character_sheets),
                "world": len(self.world_state),
                "memories": len(self.memory_segments),
                "summaries": len(self.summaries)
            },
            "tokens_by_type": {
                "recent": sum(s.tokens for s in self.recent_context),
                "characters": sum(s.tokens for s in self.character_sheets),
                "world": sum(s.tokens for s in self.world_state),
                "memories": sum(s.tokens for s in self.memory_segments),
                "summaries": sum(s.tokens for s in self.summaries)
            }
        }