import numpy as np
import pickle
import spacy
from enum import Enum
from typing import List, Dict, Tuple, Optional, Union
from dataclasses import dataclass
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.svm import LinearSVC
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report

# Using the Enum we defined earlier
class SpeakerIntent(Enum):
    """Classification categories for speaker intent in utterances."""
    INFORMATION_SEEKING = 1
    INFORMATION_GIVING = 2
    DIRECTIVE = 3
    COMMISSIVE = 4
    EXPRESSIVE = 5
    DECLARATION = 6
    PHATIC = 7
    CLARIFICATION = 8
    CONFIRMATION_SEEKING = 9
    META_COMMUNICATION = 10


@dataclass
class ContextualUtterance:
    """Represents an utterance with its context."""
    text: str
    context: List[str]
    intent: Optional[SpeakerIntent] = None


class IntentClassifier:
    """A lightweight CPU-efficient intent classifier that uses context."""
    
    def __init__(self, model_type: str = 'svm'):
        """
        Initialize the intent classifier.
        
        Args:
            model_type: The type of model to use ('svm' or 'logreg')
        """
        # Load spaCy's small English model for efficient text processing
        self.nlp = spacy.load('en_core_web_sm')
        
        # Choose the model based on type
        if model_type == 'logreg':
            model = LogisticRegression(C=1, max_iter=1000)
        else:  # Default to SVM
            model = LinearSVC(C=1)
        
        # Create a pipeline with TF-IDF vectorizer and the classifier
        self.pipeline = Pipeline([
            ('tfidf', TfidfVectorizer(ngram_range=(1, 2), max_features=5000)),
            ('clf', model)
        ])
        
        self.trained = False
        self.intent_mapping = {intent: i for i, intent in enumerate(SpeakerIntent)}
        self.reverse_intent_mapping = {i: intent for i, intent in enumerate(SpeakerIntent)}
        
    def _preprocess_text(self, text: str) -> str:
        """
        Preprocess text by removing stopwords and lemmatizing.
        
        Args:
            text: The text to preprocess
            
        Returns:
            The preprocessed text
        """
        doc = self.nlp(text)
        return " ".join([token.lemma_ for token in doc 
                         if not token.is_stop and not token.is_punct])
    
    def _combine_context(self, utterance: ContextualUtterance) -> str:
        """
        Combine the utterance text with its context.
        
        Args:
            utterance: The utterance with context
            
        Returns:
            A single string combining utterance and context
        """
        # Add more weight to the current utterance by repeating it
        combined = utterance.text + " " + utterance.text
        
        # Add context with decreasing weights (more recent context is more important)
        for i, ctx in enumerate(reversed(utterance.context)):
            weight = max(1, 3 - i)  # Give more weight to recent context
            combined += " " + " ".join([ctx] * weight)
            
        return self._preprocess_text(combined)
    
    def train(self, utterances: List[ContextualUtterance], test_size: float = 0.2) -> Dict:
        """
        Train the intent classifier.
        
        Args:
            utterances: List of utterances with context and intent labels
            test_size: Proportion of data to use for testing
            
        Returns:
            A dictionary with training metrics
        """
        # Prepare the data
        X = [self._combine_context(u) for u in utterances]
        y = [self.intent_mapping[u.intent] for u in utterances]
        
        # Split into training and testing sets
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=42, stratify=y
        )
        
        # Train the model
        self.pipeline.fit(X_train, y_train)
        self.trained = True
        
        # Evaluate the model
        y_pred = self.pipeline.predict(X_test)
        report = classification_report(y_test, y_pred, output_dict=True)
        
        return report
    
    def predict(self, utterance: Union[str, ContextualUtterance]) -> SpeakerIntent:
        """
        Predict the intent of an utterance.
        
        Args:
            utterance: Either a string or a ContextualUtterance
            
        Returns:
            The predicted intent
        """
        if not self.trained:
            raise ValueError("The model has not been trained yet")
        
        if isinstance(utterance, str):
            processed = self._preprocess_text(utterance)
        else:
            processed = self._combine_context(utterance)
        
        # Make the prediction
        intent_idx = self.pipeline.predict([processed])[0]
        return self.reverse_intent_mapping[intent_idx]
    
    def predict_proba(self, utterance: Union[str, ContextualUtterance]) -> Dict[SpeakerIntent, float]:
        """
        Get probability estimates for each intent.
        
        Args:
            utterance: Either a string or a ContextualUtterance
            
        Returns:
            Dictionary mapping intents to their probabilities
        """
        if not self.trained:
            raise ValueError("The model has not been trained yet")
        
        if not hasattr(self.pipeline.named_steps['clf'], 'predict_proba'):
            raise ValueError("The current model does not support probability estimates")
        
        if isinstance(utterance, str):
            processed = self._preprocess_text(utterance)
        else:
            processed = self._combine_context(utterance)
        
        # Get probability estimates
        proba = self.pipeline.predict_proba([processed])[0]
        return {self.reverse_intent_mapping[i]: p for i, p in enumerate(proba)}
    
    def save_model(self, path: str) -> None:
        """
        Save the trained model to disk.
        
        Args:
            path: Path to save the model to
        """
        if not self.trained:
            raise ValueError("The model has not been trained yet")
            
        with open(path, 'wb') as f:
            pickle.dump(self.pipeline, f)
    
    def load_model(self, path: str) -> None:
        """
        Load a trained model from disk.
        
        Args:
            path: Path to load the model from
        """
        with open(path, 'rb') as f:
            self.pipeline = pickle.load(f)
        self.trained = True


# Example usage
def example():
    # Create some example data
    training_data = [
        ContextualUtterance(
            text="What is the weather like today?",
            context=[],
            intent=SpeakerIntent.INFORMATION_SEEKING
        ),
        ContextualUtterance(
            text="Tell me about natural language processing.",
            context=[],
            intent=SpeakerIntent.INFORMATION_SEEKING
        ),
        ContextualUtterance(
            text="The capital of France is Paris.",
            context=[],
            intent=SpeakerIntent.INFORMATION_GIVING
        ),
        ContextualUtterance(
            text="Please open the door.",
            context=[],
            intent=SpeakerIntent.DIRECTIVE
        ),
        ContextualUtterance(
            text="I'll get that done by tomorrow.",
            context=[],
            intent=SpeakerIntent.COMMISSIVE
        ),
        ContextualUtterance(
            text="I'm feeling really happy today!",
            context=[],
            intent=SpeakerIntent.EXPRESSIVE
        ),
        ContextualUtterance(
            text="I now pronounce you husband and wife.",
            context=[],
            intent=SpeakerIntent.DECLARATION
        ),
        ContextualUtterance(
            text="How's it going?",
            context=[],
            intent=SpeakerIntent.PHATIC
        ),
        ContextualUtterance(
            text="What do you mean by that?",
            context=["The process is quite complex."],
            intent=SpeakerIntent.CLARIFICATION
        ),
        ContextualUtterance(
            text="Is that right?",
            context=["The meeting is at 3 PM."],
            intent=SpeakerIntent.CONFIRMATION_SEEKING
        ),
        ContextualUtterance(
            text="Let's change the subject.",
            context=["The weather has been terrible lately."],
            intent=SpeakerIntent.META_COMMUNICATION
        ),
    ]
    
    # Create more examples by adding variations
    more_examples = []
    for utterance in training_data:
        # Add a few variations for each example
        if utterance.intent == SpeakerIntent.INFORMATION_SEEKING:
            more_examples.extend([
                ContextualUtterance(
                    text="Can you tell me how to get to the station?",
                    context=[],
                    intent=SpeakerIntent.INFORMATION_SEEKING
                ),
                ContextualUtterance(
                    text="Where is the nearest restaurant?",
                    context=[],
                    intent=SpeakerIntent.INFORMATION_SEEKING
                ),
            ])
        elif utterance.intent == SpeakerIntent.DIRECTIVE:
            more_examples.extend([
                ContextualUtterance(
                    text="Could you help me with this?",
                    context=[],
                    intent=SpeakerIntent.DIRECTIVE
                ),
                ContextualUtterance(
                    text="Send me the report by email.",
                    context=[],
                    intent=SpeakerIntent.DIRECTIVE
                ),
            ])
    
    # Combine the original examples with the new ones
    all_examples = training_data + more_examples
    
    # Create and train the classifier
    classifier = IntentClassifier(model_type='logreg')
    metrics = classifier.train(all_examples)
    
    print("Training metrics:")
    for intent, metrics_dict in metrics.items():
        if intent in ['macro avg', 'weighted avg']:
            print(f"{intent}: f1-score={metrics_dict['f1-score']:.2f}")
    
    # Test the classifier with some examples
    test_utterances = [
        "What time does the store close?",  # INFORMATION_SEEKING
        "I'll deliver the package tomorrow.",  # COMMISSIVE
        "Nice to meet you!",  # PHATIC
        "Please explain that again.",  # CLARIFICATION
    ]
    
    print("\nTest predictions:")
    for utterance in test_utterances:
        intent = classifier.predict(utterance)
        print(f"'{utterance}' -> {intent.name}")
    
    # Test with context
    context_utterance = ContextualUtterance(
        text="Did you mean the red one?",
        context=["I need a new shirt.", "The blue one looks nice."],
        intent=None
    )
    
    intent = classifier.predict(context_utterance)
    print(f"\nWith context: '{context_utterance.text}' -> {intent.name}")
    
    # Save and load the model
    classifier.save_model("intent_classifier.pkl")
    new_classifier = IntentClassifier()
    new_classifier.load_model("intent_classifier.pkl")
    
    # Verify the loaded model works
    reload_intent = new_classifier.predict(test_utterances[0])
    print(f"\nAfter reload: '{test_utterances[0]}' -> {reload_intent.name}")


if __name__ == "__main__":
    example()