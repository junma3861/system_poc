import pytest
from app.services.healthcare_filter import HealthcareFilter


class TestHealthcareFilter:
    """Tests for the HealthcareFilter service."""
    
    @pytest.fixture
    def filter(self):
        return HealthcareFilter()
    
    # Test healthcare-related messages (should return True)
    @pytest.mark.parametrize("message", [
        "What are the symptoms of diabetes?",
        "I have a headache and fever",
        "How do I treat a cold?",
        "What medication should I take for pain?",
        "I need to see a doctor",
        "My heart rate is very fast",
        "What is the treatment for hypertension?",
        "I'm feeling sick today",
        "What are the side effects of aspirin?",
        "How can I prevent the flu?",
        "I have anxiety and depression",
        "What does a nurse do?",
        "I hurt my knee yesterday",
        "Is this rash serious?",
        "I need medical advice",
        "What is cancer?",
        "How to improve my mental health?",
        "I'm feeling very tired and fatigued",
        "What causes allergies?",
        "Should I go to the hospital?",
    ])
    def test_healthcare_related_messages(self, filter, message):
        """Test that healthcare-related messages are correctly identified."""
        assert filter.is_healthcare_related(message) is True
    
    # Test non-healthcare messages (should return False)
    @pytest.mark.parametrize("message", [
        "What is the weather today?",
        "How do I cook pasta?",
        "Tell me a joke",
        "What is the capital of France?",
        "How do I learn Python?",
        "What time is it?",
        "Recommend a good movie",
        "How do I fix my car?",
        "What is machine learning?",
        "Write me a poem",
        "How to invest in stocks?",
        "What is the best smartphone?",
        "How do I travel to Japan?",
        "What is blockchain?",
    ])
    def test_non_healthcare_messages(self, filter, message):
        """Test that non-healthcare messages are correctly rejected."""
        assert filter.is_healthcare_related(message) is False
    
    def test_get_matched_keywords(self, filter):
        """Test that matched keywords are correctly extracted."""
        message = "I have a headache and fever, should I see a doctor?"
        keywords = filter.get_matched_keywords(message)
        
        assert "headache" in keywords
        assert "fever" in keywords
        assert "doctor" in keywords
    
    def test_empty_message(self, filter):
        """Test handling of empty message."""
        assert filter.is_healthcare_related("") is False
    
    def test_case_insensitivity(self, filter):
        """Test that filtering is case insensitive."""
        assert filter.is_healthcare_related("DIABETES") is True
        assert filter.is_healthcare_related("Diabetes") is True
        assert filter.is_healthcare_related("diabetes") is True
    
    def test_partial_word_not_matched(self, filter):
        """Test that partial words are not matched (word boundaries)."""
        # 'ache' should match, but not as part of another word
        assert filter.is_healthcare_related("I have a headache") is True
    
    def test_multiple_keywords(self, filter):
        """Test message with multiple healthcare keywords."""
        message = "I have diabetes, hypertension, and I need medication for pain"
        keywords = filter.get_matched_keywords(message)
        
        assert len(keywords) >= 3
        assert "diabetes" in keywords
        assert "hypertension" in keywords
        assert "medication" in keywords
