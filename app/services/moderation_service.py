from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch


class ModerationService:
    """
    Central service for malicious / toxic content detection in Hackmates.
    Uses unitary/toxic-bert (Transformer-based text classification model).
    """

    # Model name from Hugging Face
    MODEL_NAME = "unitary/toxic-bert"

    # Labels in the exact order the model was trained on
    LABELS = [
        "toxic",
        "severe_toxic",
        "obscene",
        "threat",
        "insult",
        "identity_hate"
    ]

    TOXIC_THRESHOLD = 0.7
    THREAT_THRESHOLD = 0.5
    IDENTITY_HATE_THRESHOLD = 0.4

    tokenizer = None
    model = None

    @classmethod
    def get_models(cls):
        if cls.tokenizer is None or cls.model is None:
            try:
                cls.tokenizer = AutoTokenizer.from_pretrained(cls.MODEL_NAME)
                cls.model = AutoModelForSequenceClassification.from_pretrained(cls.MODEL_NAME)
                cls.model.eval()
            except OSError as e:
                import logging
                logging.error(f"Failed to load moderation model: {e}")
        return cls.tokenizer, cls.model

    @staticmethod
    def analyze_text(text: str) -> dict:
        """
        Runs the ML model on input text and returns toxicity scores.
        """

        tokenizer, model = ModerationService.get_models()
        if not tokenizer or not model:
            return {label: 0.0 for label in ModerationService.LABELS}

        # Convert text → tokens the model understands
        inputs = tokenizer(
            text,
            return_tensors="pt",   # PyTorch tensors
            truncation=True,       # Cut long text safely
            max_length=512         # BERT max limit
        )

        # Disable gradient calculation (faster + safer)
        with torch.no_grad():
            outputs = model(**inputs)

        # Convert raw logits → probabilities (0 to 1)
        scores = torch.sigmoid(outputs.logits)[0]

        # Map probabilities to readable labels
        return {
            ModerationService.LABELS[i]: float(scores[i])
            for i in range(len(ModerationService.LABELS))
        }

    @staticmethod
    def is_allowed(scores: dict) -> bool:
        """
        Business logic layer: decides whether content is allowed or not.
        """

        #  Platform safety thresholds (can be tuned)
        if scores.get("toxic", 0) > ModerationService.TOXIC_THRESHOLD:
            return False

        if scores.get("threat", 0) > ModerationService.THREAT_THRESHOLD:
            return False

        if scores.get("identity_hate", 0) > ModerationService.IDENTITY_HATE_THRESHOLD:
            return False

        return True
