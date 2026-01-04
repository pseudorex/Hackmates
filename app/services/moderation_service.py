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

    # Load tokenizer and model ONCE (important for production)
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    model = AutoModelForSequenceClassification.from_pretrained(MODEL_NAME)

    # Set model to inference mode
    model.eval()

    @staticmethod
    def analyze_text(text: str) -> dict:
        """
        Runs the ML model on input text and returns toxicity scores.
        """

        # Convert text → tokens the model understands
        inputs = ModerationService.tokenizer(
            text,
            return_tensors="pt",   # PyTorch tensors
            truncation=True,       # Cut long text safely
            max_length=512         # BERT max limit
        )

        # Disable gradient calculation (faster + safer)
        with torch.no_grad():
            outputs = ModerationService.model(**inputs)

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
        if scores["toxic"] > 0.7:
            return False

        if scores["threat"] > 0.5:
            return False

        if scores["identity_hate"] > 0.4:
            return False

        return True
