import joblib
import os
import numpy as np
from sklearn.base import BaseEstimator, TransformerMixin
import re

# ── Custom Feature Extractor (MUST BE HERE for model loading) ───────────────────
class TextFeatureExtractor(BaseEstimator, TransformerMixin):
    def fit(self, X, y=None): return self
    def transform(self, X):
        features = []
        for text in X:
            t = text.lower()
            f = [
                # URL features
                1 if re.search(r'https?://\d+\.\d+\.\d+\.\d+', t) else 0,  # IP in URL
                1 if any(tld in t for tld in ['.tk', '.ml', '.gq', '.xyz', '.top', '.cf', '.ga']) else 0,
                len(re.findall(r'https?://([^/]+)', t)[0].split('.')) - 1 if re.search(r'https?://', t) else 0,
                1 if t.startswith('http://') else 0,
                min(len(t) / 100.0, 3.0),
                t.count('-'),
                t.count('@'),
                t.count('%'),
                # Phishing keywords
                sum(1 for w in ['verify', 'suspend', 'urgent', 'login', 'account', 'click', 'free',
                                'winner', 'update', 'confirm', 'banking', 'alert', 'limited',
                                'password', 'secure', 'reset', 'compromised', 'immediately',
                                'expires', 'locked', 'blocked', 'claim', 'prize', 'congratulations',
                                'selected', 'reward', 'gift', 'lucky', 'won', 'inheritance',
                                'beneficiary', 'transfer', 'nigeria', 'prince'] if w in t),
                # Legitimate indicators
                1 if t.startswith('https://') else 0,
                sum(1 for w in ['meeting', 'attached', 'report', 'schedule', 'team',
                                'project', 'review', 'invoice', 'delivered', 'receipt',
                                'newsletter', 'update', 'agenda', 'reminder', 'feedback'] if w in t),
                # Suspicious patterns
                1 if re.search(r'\b(l0gin|paypa1|g00gle|amaz0n|rn[il]cr0soft)\b', t) else 0,
                t.count('!'),
                t.count('$'),
            ]
            features.append(f)
        return np.array(features)

_BASE_DIR = os.path.dirname(__file__)
_MODEL_CANDIDATES = [
    os.path.join(_BASE_DIR, "models", "model.pkl"),
    os.path.join(_BASE_DIR, "model.pkl"),
]

def load_model():
    last_err = None
    for path in _MODEL_CANDIDATES:
        try:
            if os.path.exists(path):
                return joblib.load(path)
        except Exception as e:
            last_err = e

    if last_err:
        raise RuntimeError(
            "Failed to load model from candidates: " + ", ".join(_MODEL_CANDIDATES)
        ) from last_err

    raise FileNotFoundError(
        "Model file not found. Expected one of: " + ", ".join(_MODEL_CANDIDATES)
    )