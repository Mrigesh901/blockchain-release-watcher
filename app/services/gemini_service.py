"""
Google Gemini AI service.
Handles AI-powered analysis of blockchain version changes.
"""
import json
import re
from typing import Dict, Any, List, Optional

try:
    import google.generativeai as genai
except ImportError:
    genai = None

from app.config import Config


class GeminiService:
    """Service for AI analysis using Google Gemini."""
    
    def __init__(self):
        """Initialize Gemini service."""
        if not genai:
            raise ImportError(
                "google-generativeai package not installed. "
                "Install with: pip install google-generativeai"
            )
        
        genai.configure(api_key=Config.GEMINI_API_KEY)
        self.model = genai.GenerativeModel(Config.GEMINI_MODEL)
    
    def _create_analysis_prompt(self, repo_name: str, old_version: str,
                               new_version: str, release_notes: str,
                               commit_messages: List[str]) -> str:
        """
        Create analysis prompt for Gemini.
        
        Args:
            repo_name: Repository name.
            old_version: Previous version.
            new_version: New version.
            release_notes: Release notes if available.
            commit_messages: Commit messages if no release notes.
            
        Returns:
            Formatted prompt string.
        """
        prompt = f"""You are a blockchain infrastructure expert analyzing a version update for {repo_name}.

OLD VERSION: {old_version}
NEW VERSION: {new_version}

"""
        
        if release_notes:
            prompt += f"""RELEASE NOTES:
{release_notes}

"""
        
        if commit_messages:
            prompt += f"""COMMIT MESSAGES:
{chr(10).join(commit_messages[:20])}

"""
        
        prompt += """Analyze this update and provide a response in STRICT JSON format with these exact fields:

{
  "summary": "Brief summary of changes in 2-3 sentences",
  "mandatory_upgrade": true or false,
  "severity": "LOW" or "MEDIUM" or "HIGH" or "CRITICAL",
  "reasoning": "Why this severity and mandatory decision"
}

CRITICAL SEVERITY means: security vulnerabilities, hard forks, network-breaking changes, or consensus failures.
HIGH SEVERITY means: important bug fixes, performance issues, or features affecting network stability.
MEDIUM SEVERITY means: minor bug fixes, optimizations, or new non-critical features.
LOW SEVERITY means: documentation, refactoring, or cosmetic changes.

MANDATORY UPGRADE is true only if:
- Security vulnerability is fixed
- Hard fork or consensus change requires it
- Network will reject old version
- Critical bug affects operations

Respond ONLY with valid JSON. No markdown, no extra text, just the JSON object."""
        
        return prompt
    
    def _extract_json_from_response(self, response_text: str) -> Optional[Dict[str, Any]]:
        """
        Extract JSON from Gemini response, handling markdown code blocks.
        
        Args:
            response_text: Raw response from Gemini.
            
        Returns:
            Parsed JSON dictionary or None.
        """
        # Try to parse as-is first
        try:
            return json.loads(response_text.strip())
        except json.JSONDecodeError:
            pass
        
        # Try to extract JSON from markdown code block
        json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', 
                              response_text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass
        
        # Try to find JSON object in text
        json_match = re.search(r'\{[^{}]*"summary"[^{}]*\}', 
                              response_text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(0))
            except json.JSONDecodeError:
                pass
        
        return None
    
    def _validate_analysis(self, analysis: Dict[str, Any]) -> bool:
        """
        Validate analysis response structure.
        
        Args:
            analysis: Parsed analysis dictionary.
            
        Returns:
            True if valid, False otherwise.
        """
        required_fields = ["summary", "mandatory_upgrade", "severity", "reasoning"]
        
        if not all(field in analysis for field in required_fields):
            return False
        
        # Validate severity
        valid_severities = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
        if analysis["severity"] not in valid_severities:
            return False
        
        # Validate mandatory_upgrade is boolean
        if not isinstance(analysis["mandatory_upgrade"], bool):
            return False
        
        return True
    
    def analyze_version_change(self, repo_name: str, old_version: str,
                              new_version: str, release_notes: str = "",
                              commit_messages: List[str] = None) -> Dict[str, Any]:
        """
        Analyze version change using Gemini AI.
        
        Args:
            repo_name: Repository name.
            old_version: Previous version.
            new_version: New version.
            release_notes: Release notes if available.
            commit_messages: Commit messages if no release notes.
            
        Returns:
            Analysis result with summary, severity, and recommendation.
        """
        if commit_messages is None:
            commit_messages = []
        
        # Create prompt
        prompt = self._create_analysis_prompt(
            repo_name, old_version, new_version, 
            release_notes, commit_messages
        )
        
        try:
            # Generate response
            response = self.model.generate_content(prompt)
            response_text = response.text
            
            # Extract and parse JSON
            analysis = self._extract_json_from_response(response_text)
            
            if not analysis:
                # Fallback response if parsing fails
                return {
                    "summary": f"Update from {old_version} to {new_version}. "
                              f"Please review release notes manually.",
                    "mandatory_upgrade": False,
                    "severity": "MEDIUM",
                    "reasoning": "AI analysis failed to parse. Manual review recommended."
                }
            
            # Validate response
            if not self._validate_analysis(analysis):
                return {
                    "summary": f"Update from {old_version} to {new_version}. "
                              f"Please review release notes manually.",
                    "mandatory_upgrade": False,
                    "severity": "MEDIUM",
                    "reasoning": "AI response validation failed. Manual review recommended."
                }
            
            return analysis
            
        except Exception as e:
            print(f"Gemini API error: {e}")
            # Fallback response on error
            return {
                "summary": f"Update from {old_version} to {new_version}. "
                          f"AI analysis unavailable. Please review manually.",
                "mandatory_upgrade": False,
                "severity": "MEDIUM",
                "reasoning": f"AI analysis error: {str(e)}"
            }
    
    def should_send_alert(self, analysis: Dict[str, Any]) -> bool:
        """
        Determine if alert should be sent based on analysis.
        
        Args:
            analysis: Analysis result from analyze_version_change.
            
        Returns:
            True if alert should be sent.
        """
        # Send alert if mandatory upgrade OR severity is HIGH or CRITICAL
        if analysis.get("mandatory_upgrade"):
            return True
        
        severity = analysis.get("severity", "MEDIUM")
        return severity in ["HIGH", "CRITICAL"]
