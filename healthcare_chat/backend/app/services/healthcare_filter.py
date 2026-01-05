import re
from typing import List


class HealthcareFilter:
    """Filter to determine if a message is healthcare-related."""
    
    def __init__(self):
        # Healthcare-related keywords and patterns
        self.healthcare_keywords = [
            # Medical conditions
            "disease", "illness", "condition", "syndrome", "disorder",
            "infection", "virus", "bacteria", "cancer", "tumor",
            "diabetes", "hypertension", "asthma", "arthritis", "allergy", "allergies",
            
            # Symptoms
            "symptom", "symptoms", "pain", "ache", "fever", "cough", "cold", "flu",
            "headache", "headaches", "migraine", "nausea", "vomiting", "diarrhea",
            "fatigue", "tired", "dizzy", "dizziness", "swelling",
            "rash", "itching", "bleeding", "bruise", "sore",
            
            # Body parts
            "heart", "lung", "liver", "kidney", "brain", "stomach",
            "chest", "throat", "ear", "eye", "skin", "bone", "muscle",
            "joint", "blood", "nerve",
            
            # Medical terms
            "diagnosis", "treatment", "therapy", "medication", "medicine",
            "drug", "prescription", "dose", "dosage", "vaccine",
            "surgery", "procedure", "test", "screening", "checkup",
            
            # Healthcare professionals
            "doctor", "physician", "nurse", "specialist", "therapist",
            "surgeon", "dentist", "pharmacist", "psychiatrist",
            
            # Health topics
            "health", "healthy", "wellness", "nutrition", "diet",
            "exercise", "fitness", "weight", "sleep", "stress",
            "mental health", "anxiety", "depression", "therapy",
            "pregnancy", "prenatal", "pediatric", "geriatric",
            
            # Medical facilities
            "hospital", "clinic", "emergency", "urgent care",
            "pharmacy", "laboratory",
            
            # Insurance and healthcare system
            "insurance", "medicare", "medicaid", "healthcare",
            
            # First aid and safety
            "first aid", "cpr", "emergency", "injury", "wound",
            "burn", "fracture", "sprain", "poison",
            
            # Lifestyle and prevention
            "prevention", "preventive", "lifestyle", "habit",
            "smoking", "alcohol", "addiction", "recovery"
        ]
        
        # Compile regex pattern for efficient matching
        self.pattern = re.compile(
            r'\b(' + '|'.join(re.escape(kw) for kw in self.healthcare_keywords) + r')\b',
            re.IGNORECASE
        )
    
    def is_healthcare_related(self, message: str) -> bool:
        """
        Determine if a message is healthcare-related.
        Returns True if the message contains healthcare-related content.
        """
        # Check for keyword matches
        if self.pattern.search(message):
            return True
        
        # Additional patterns for common health questions
        health_question_patterns = [
            r'\b(how to|what is|what are|can i|should i|is it).*(treat|cure|heal|prevent|help with)\b',
            r'\b(feeling|feel)\s+(sick|unwell|ill|bad|worse|better)\b',
            r'\bside effects?\b',
            r'\bmedical (advice|help|question|condition)\b',
            r'\b(hurt|hurts|hurting)\b',
            r'\b(sick|unwell|ill)\b'
        ]
        
        for pattern in health_question_patterns:
            if re.search(pattern, message, re.IGNORECASE):
                return True
        
        return False
    
    def get_matched_keywords(self, message: str) -> List[str]:
        """Return list of healthcare keywords found in the message."""
        matches = self.pattern.findall(message)
        return list(set(match.lower() for match in matches))
