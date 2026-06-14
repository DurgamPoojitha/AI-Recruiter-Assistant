import re
from typing import Dict, Any

class PIIService:
    def redact_text(self, text: str) -> str:
        if not text:
            return text
            
        # Redact emails
        text = re.sub(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+', '[REDACTED EMAIL]', text)
        
        # Redact phone numbers (simple regex for formats like 123-456-7890 or (123) 456-7890 or +1 123 456 7890)
        text = re.sub(r'(\+?\d{1,3}[\s-]?)?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}', '[REDACTED PHONE]', text)
        
        return text

    def redact_candidate_details(self, candidate: Dict[str, Any]) -> Dict[str, Any]:
        """
        Redacts personal info from a candidate dictionary for unbiased screening.
        """
        redacted = candidate.copy()
        
        # Replace Name
        if 'name' in redacted:
            redacted['name'] = f"Candidate {redacted.get('id', 'Anonymous')}"
            
        # Replace direct PII fields
        if 'email' in redacted:
            redacted['email'] = '[REDACTED]'
            
        if 'phone' in redacted:
            redacted['phone'] = '[REDACTED]'
            
        # Optional: redacting university names to avoid academic bias, but typically names/emails are sufficient MVP.
        
        return redacted

def get_pii_service() -> PIIService:
    return PIIService()
