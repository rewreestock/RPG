"""Personality engine for consistent character behavior."""

import logging
import random
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import re


@dataclass
class PersonalityTrait:
    """Represents a personality trait with intensity."""
    name: str
    value: float  # -1.0 to 1.0
    description: str = ""


@dataclass
class EmotionalState:
    """Represents current emotional state."""
    primary_emotion: str
    intensity: float  # 0.0 to 1.0
    secondary_emotions: List[str]
    triggers: List[str]  # What caused this state


class PersonalityEngine:
    """Engine for generating consistent character behavior and responses."""
    
    def __init__(self):
        """Initialize personality engine."""
        self.logger = logging.getLogger(__name__)
        
        # Core personality dimensions (Big Five + additional)
        self.personality_dimensions = {
            "openness": "Open to experience vs Traditional",
            "conscientiousness": "Organized vs Spontaneous", 
            "extraversion": "Outgoing vs Reserved",
            "agreeableness": "Cooperative vs Competitive",
            "neuroticism": "Anxious vs Calm",
            "dominance": "Assertive vs Submissive",
            "warmth": "Friendly vs Aloof",
            "impulsiveness": "Impulsive vs Deliberate"
        }
        
        # Emotion categories and related words
        self.emotion_categories = {
            "joy": ["happy", "excited", "cheerful", "elated", "content", "amused"],
            "sadness": ["sad", "melancholy", "depressed", "heartbroken", "mournful"],
            "anger": ["angry", "furious", "irritated", "enraged", "annoyed", "frustrated"],
            "fear": ["afraid", "terrified", "anxious", "worried", "nervous", "panicked"],
            "surprise": ["surprised", "amazed", "astonished", "shocked", "stunned"],
            "disgust": ["disgusted", "revolted", "appalled", "nauseated"],
            "contempt": ["contemptuous", "disdainful", "scornful", "dismissive"],
            "love": ["loving", "affectionate", "devoted", "adoring", "tender"],
            "trust": ["trusting", "confident", "secure", "believing"],
            "anticipation": ["eager", "hopeful", "expectant", "optimistic"]
        }
        
        # Speech patterns for different personality types
        self.speech_patterns = {
            "formal": {
                "patterns": ["I believe that", "It appears to me", "One might consider"],
                "vocabulary": "sophisticated",
                "sentence_length": "long"
            },
            "casual": {
                "patterns": ["I think", "You know", "Like", "Kinda"],
                "vocabulary": "simple",
                "sentence_length": "short"
            },
            "dramatic": {
                "patterns": ["Surely you must", "How could you", "Never have I"],
                "vocabulary": "expressive",
                "sentence_length": "varied"
            },
            "analytical": {
                "patterns": ["Given that", "Therefore", "However", "Nevertheless"],
                "vocabulary": "precise",
                "sentence_length": "medium"
            }
        }
        
        self.logger.info("Initialized personality engine")
    
    def create_personality_profile(
        self,
        traits: Dict[str, float],
        background_factors: List[str] = None
    ) -> Dict[str, Any]:
        """Create a comprehensive personality profile.
        
        Args:
            traits: Dictionary of trait names to values (-1.0 to 1.0)
            background_factors: Factors that influence personality
            
        Returns:
            Complete personality profile
        """
        background_factors = background_factors or []
        
        # Normalize trait values
        normalized_traits = {}
        for trait, value in traits.items():
            normalized_traits[trait] = max(-1.0, min(1.0, value))
        
        # Determine speech style
        speech_style = self._determine_speech_style(normalized_traits)
        
        # Generate behavioral tendencies
        behavioral_tendencies = self._generate_behavioral_tendencies(normalized_traits)
        
        # Determine emotional patterns
        emotional_patterns = self._generate_emotional_patterns(normalized_traits)
        
        # Generate relationship tendencies
        relationship_tendencies = self._generate_relationship_tendencies(normalized_traits)
        
        profile = {
            "traits": normalized_traits,
            "speech_style": speech_style,
            "behavioral_tendencies": behavioral_tendencies,
            "emotional_patterns": emotional_patterns,
            "relationship_tendencies": relationship_tendencies,
            "background_factors": background_factors
        }
        
        self.logger.debug(f"Created personality profile with {len(normalized_traits)} traits")
        return profile
    
    def _determine_speech_style(self, traits: Dict[str, float]) -> Dict[str, Any]:
        """Determine speech style based on personality traits."""
        style = {"patterns": [], "characteristics": []}
        
        # Extraversion affects verbosity
        if traits.get("extraversion", 0) > 0.5:
            style["verbosity"] = "high"
            style["characteristics"].append("talkative")
        elif traits.get("extraversion", 0) < -0.5:
            style["verbosity"] = "low"
            style["characteristics"].append("reserved")
        else:
            style["verbosity"] = "medium"
        
        # Conscientiousness affects formality
        if traits.get("conscientiousness", 0) > 0.5:
            style["formality"] = "high"
            style["patterns"].extend(self.speech_patterns["formal"]["patterns"])
        elif traits.get("conscientiousness", 0) < -0.5:
            style["formality"] = "low"
            style["patterns"].extend(self.speech_patterns["casual"]["patterns"])
        else:
            style["formality"] = "medium"
        
        # Neuroticism affects emotional expression
        if traits.get("neuroticism", 0) > 0.5:
            style["emotional_expression"] = "high"
            style["characteristics"].append("expressive")
        else:
            style["emotional_expression"] = "controlled"
        
        # Dominance affects assertiveness
        if traits.get("dominance", 0) > 0.5:
            style["assertiveness"] = "high"
            style["characteristics"].append("direct")
        elif traits.get("dominance", 0) < -0.5:
            style["assertiveness"] = "low"
            style["characteristics"].append("indirect")
        
        return style
    
    def _generate_behavioral_tendencies(self, traits: Dict[str, float]) -> List[str]:
        """Generate behavioral tendencies based on traits."""
        tendencies = []
        
        # Openness
        if traits.get("openness", 0) > 0.5:
            tendencies.extend([
                "Seeks new experiences",
                "Open to different perspectives",
                "Curious about unusual topics"
            ])
        elif traits.get("openness", 0) < -0.5:
            tendencies.extend([
                "Prefers familiar routines",
                "Skeptical of new ideas",
                "Values tradition"
            ])
        
        # Conscientiousness
        if traits.get("conscientiousness", 0) > 0.5:
            tendencies.extend([
                "Plans ahead carefully",
                "Keeps commitments",
                "Pays attention to details"
            ])
        elif traits.get("conscientiousness", 0) < -0.5:
            tendencies.extend([
                "Acts spontaneously",
                "Flexible with plans",
                "May overlook details"
            ])
        
        # Extraversion
        if traits.get("extraversion", 0) > 0.5:
            tendencies.extend([
                "Seeks social interaction",
                "Energized by groups",
                "Speaks up in conversations"
            ])
        elif traits.get("extraversion", 0) < -0.5:
            tendencies.extend([
                "Prefers solitude or small groups",
                "Thinks before speaking",
                "Observes before participating"
            ])
        
        # Agreeableness
        if traits.get("agreeableness", 0) > 0.5:
            tendencies.extend([
                "Seeks harmony in relationships",
                "Considers others' feelings",
                "Cooperative in conflicts"
            ])
        elif traits.get("agreeableness", 0) < -0.5:
            tendencies.extend([
                "Prioritizes own interests",
                "Direct in expressing disagreement",
                "Competitive in interactions"
            ])
        
        # Neuroticism
        if traits.get("neuroticism", 0) > 0.5:
            tendencies.extend([
                "Sensitive to stress",
                "Experiences emotions intensely",
                "May worry about outcomes"
            ])
        elif traits.get("neuroticism", 0) < -0.5:
            tendencies.extend([
                "Remains calm under pressure",
                "Even emotional responses",
                "Optimistic outlook"
            ])
        
        return tendencies
    
    def _generate_emotional_patterns(self, traits: Dict[str, float]) -> Dict[str, Any]:
        """Generate emotional response patterns."""
        patterns = {
            "default_emotions": [],
            "stress_responses": [],
            "triggers": {},
            "coping_mechanisms": []
        }
        
        # Default emotional state based on traits
        if traits.get("neuroticism", 0) > 0.5:
            patterns["default_emotions"].extend(["anxious", "worried"])
        elif traits.get("neuroticism", 0) < -0.5:
            patterns["default_emotions"].extend(["calm", "content"])
        
        if traits.get("extraversion", 0) > 0.5:
            patterns["default_emotions"].extend(["cheerful", "energetic"])
        elif traits.get("extraversion", 0) < -0.5:
            patterns["default_emotions"].extend(["reserved", "contemplative"])
        
        # Stress responses
        if traits.get("agreeableness", 0) > 0.5:
            patterns["stress_responses"].append("seeks social support")
        else:
            patterns["stress_responses"].append("withdraws or becomes confrontational")
        
        if traits.get("conscientiousness", 0) > 0.5:
            patterns["coping_mechanisms"].extend([
                "makes detailed plans",
                "follows routines",
                "breaks problems into steps"
            ])
        else:
            patterns["coping_mechanisms"].extend([
                "goes with the flow",
                "seeks immediate solutions",
                "adapts quickly"
            ])
        
        return patterns
    
    def _generate_relationship_tendencies(self, traits: Dict[str, float]) -> Dict[str, Any]:
        """Generate relationship behavior patterns."""
        tendencies = {
            "attachment_style": "",
            "conflict_style": "",
            "social_preferences": [],
            "trust_patterns": []
        }
        
        # Attachment style (simplified)
        agreeableness = traits.get("agreeableness", 0)
        neuroticism = traits.get("neuroticism", 0)
        
        if agreeableness > 0.3 and neuroticism < 0.3:
            tendencies["attachment_style"] = "secure"
        elif agreeableness > 0.3 and neuroticism > 0.3:
            tendencies["attachment_style"] = "anxious"
        elif agreeableness < -0.3 and neuroticism < 0.3:
            tendencies["attachment_style"] = "avoidant"
        else:
            tendencies["attachment_style"] = "disorganized"
        
        # Conflict style
        dominance = traits.get("dominance", 0)
        agreeableness = traits.get("agreeableness", 0)
        
        if dominance > 0.3 and agreeableness < 0:
            tendencies["conflict_style"] = "competitive"
        elif dominance < 0 and agreeableness > 0.3:
            tendencies["conflict_style"] = "accommodating"
        elif dominance > 0.3 and agreeableness > 0.3:
            tendencies["conflict_style"] = "collaborative"
        elif dominance < 0 and agreeableness < 0:
            tendencies["conflict_style"] = "avoidant"
        else:
            tendencies["conflict_style"] = "compromising"
        
        # Social preferences
        extraversion = traits.get("extraversion", 0)
        if extraversion > 0.5:
            tendencies["social_preferences"].extend([
                "large groups",
                "public settings",
                "being center of attention"
            ])
        elif extraversion < -0.5:
            tendencies["social_preferences"].extend([
                "one-on-one interactions",
                "quiet settings",
                "deep conversations"
            ])
        
        return tendencies
    
    def generate_response_guidance(
        self,
        personality_profile: Dict[str, Any],
        current_emotion: str,
        situation_context: str,
        relationship_context: Dict[str, float] = None
    ) -> str:
        """Generate guidance for how a character should respond.
        
        Args:
            personality_profile: Character's personality profile
            current_emotion: Current emotional state
            situation_context: Description of current situation
            relationship_context: Relationships with other characters
            
        Returns:
            Response guidance text
        """
        relationship_context = relationship_context or {}
        
        guidance_parts = []
        
        # Core personality guidance
        traits = personality_profile.get("traits", {})
        speech_style = personality_profile.get("speech_style", {})
        
        # Speech style guidance
        if speech_style.get("verbosity") == "high":
            guidance_parts.append("Respond with detailed, elaborate explanations")
        elif speech_style.get("verbosity") == "low":
            guidance_parts.append("Keep responses brief and to the point")
        
        if speech_style.get("formality") == "high":
            guidance_parts.append("Use formal, proper language")
        elif speech_style.get("formality") == "low":
            guidance_parts.append("Use casual, informal language")
        
        # Emotional expression
        if traits.get("neuroticism", 0) > 0.5:
            guidance_parts.append("Express emotions more intensely")
        elif traits.get("neuroticism", 0) < -0.5:
            guidance_parts.append("Maintain emotional composure")
        
        # Social behavior
        if traits.get("extraversion", 0) > 0.5:
            guidance_parts.append("Be outgoing and engage actively")
        elif traits.get("extraversion", 0) < -0.5:
            guidance_parts.append("Be more reserved and thoughtful")
        
        # Relationship considerations
        behavioral_tendencies = personality_profile.get("behavioral_tendencies", [])
        if behavioral_tendencies:
            guidance_parts.append(f"Behavior: {'; '.join(behavioral_tendencies[:3])}")
        
        # Current emotion influence
        if current_emotion:
            emotion_guidance = self._get_emotion_guidance(current_emotion, traits)
            if emotion_guidance:
                guidance_parts.append(f"Emotional state: {emotion_guidance}")
        
        return " | ".join(guidance_parts)
    
    def _get_emotion_guidance(self, emotion: str, traits: Dict[str, float]) -> str:
        """Get guidance for expressing a specific emotion."""
        emotion_lower = emotion.lower()
        
        # Find emotion category
        emotion_category = None
        for category, emotions in self.emotion_categories.items():
            if emotion_lower in emotions or emotion_lower == category:
                emotion_category = category
                break
        
        if not emotion_category:
            return f"Currently feeling {emotion}"
        
        # Adjust expression based on traits
        expression_intensity = "moderately"
        
        if traits.get("neuroticism", 0) > 0.5:
            expression_intensity = "intensely"
        elif traits.get("neuroticism", 0) < -0.5:
            expression_intensity = "subtly"
        
        if traits.get("extraversion", 0) > 0.5:
            expression_style = "openly"
        elif traits.get("extraversion", 0) < -0.5:
            expression_style = "internally"
        else:
            expression_style = "carefully"
        
        return f"Express {emotion} {expression_intensity} and {expression_style}"
    
    def predict_emotional_response(
        self,
        personality_profile: Dict[str, Any],
        trigger_event: str,
        current_relationships: Dict[str, float] = None
    ) -> EmotionalState:
        """Predict how a character would emotionally respond to an event.
        
        Args:
            personality_profile: Character's personality profile
            trigger_event: Description of triggering event
            current_relationships: Current relationship states
            
        Returns:
            Predicted emotional state
        """
        current_relationships = current_relationships or {}
        traits = personality_profile.get("traits", {})
        
        # Analyze trigger event for emotional cues
        trigger_lower = trigger_event.lower()
        
        # Detect emotional triggers
        primary_emotion = "neutral"
        intensity = 0.5
        secondary_emotions = []
        
        # Positive triggers
        if any(word in trigger_lower for word in ["success", "achievement", "compliment", "gift", "victory"]):
            primary_emotion = "joy"
            intensity = 0.7
        
        # Negative triggers
        elif any(word in trigger_lower for word in ["failure", "loss", "death", "betrayal", "insult"]):
            primary_emotion = "sadness"
            intensity = 0.8
            if "betrayal" in trigger_lower or "insult" in trigger_lower:
                secondary_emotions.append("anger")
        
        # Threat triggers
        elif any(word in trigger_lower for word in ["danger", "threat", "attack", "enemy"]):
            primary_emotion = "fear"
            intensity = 0.8
            if traits.get("dominance", 0) > 0.5:
                secondary_emotions.append("anger")
        
        # Surprise triggers
        elif any(word in trigger_lower for word in ["unexpected", "sudden", "surprise"]):
            primary_emotion = "surprise"
            intensity = 0.6
        
        # Adjust intensity based on personality
        neuroticism = traits.get("neuroticism", 0)
        if neuroticism > 0.5:
            intensity = min(1.0, intensity * 1.3)
        elif neuroticism < -0.5:
            intensity = max(0.1, intensity * 0.7)
        
        # Add secondary emotions based on traits
        if traits.get("agreeableness", 0) < -0.5 and primary_emotion in ["sadness", "fear"]:
            secondary_emotions.append("anger")
        
        return EmotionalState(
            primary_emotion=primary_emotion,
            intensity=intensity,
            secondary_emotions=secondary_emotions,
            triggers=[trigger_event]
        )
    
    def get_character_consistency_check(
        self,
        personality_profile: Dict[str, Any],
        proposed_action: str,
        current_context: str
    ) -> Tuple[bool, str]:
        """Check if a proposed action is consistent with character personality.
        
        Args:
            personality_profile: Character's personality profile
            proposed_action: Action the character might take
            current_context: Current situation context
            
        Returns:
            Tuple of (is_consistent, explanation)
        """
        traits = personality_profile.get("traits", {})
        behavioral_tendencies = personality_profile.get("behavioral_tendencies", [])
        
        action_lower = proposed_action.lower()
        inconsistencies = []
        
        # Check against major traits
        
        # Conscientiousness vs spontaneous actions
        if traits.get("conscientiousness", 0) > 0.5:
            if any(word in action_lower for word in ["impulsive", "sudden", "without thinking"]):
                inconsistencies.append("Character is highly conscientious but action seems impulsive")
        
        # Agreeableness vs aggressive actions
        if traits.get("agreeableness", 0) > 0.5:
            if any(word in action_lower for word in ["attack", "insult", "argue", "fight"]):
                inconsistencies.append("Character is agreeable but action seems aggressive")
        
        # Extraversion vs withdrawal
        if traits.get("extraversion", 0) > 0.5:
            if any(word in action_lower for word in ["hide", "withdraw", "avoid", "isolate"]):
                inconsistencies.append("Character is extraverted but action involves withdrawal")
        
        # Dominance vs submissive actions
        if traits.get("dominance", 0) > 0.5:
            if any(word in action_lower for word in ["submit", "obey", "follow", "yield"]):
                inconsistencies.append("Character is dominant but action seems submissive")
        
        if inconsistencies:
            return False, "; ".join(inconsistencies)
        else:
            return True, "Action is consistent with character personality"