import joblib
import os
import numpy as np
from sklearn.pipeline import Pipeline, FeatureUnion
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.svm import LinearSVC
from sklearn.calibration import CalibratedClassifierCV
from sklearn.ensemble import VotingClassifier
from sklearn.model_selection import cross_val_score
from sklearn.base import BaseEstimator, TransformerMixin
import re
import pandas as pd
from model_loader import TextFeatureExtractor
    
# ── Set path to CSV datasets ───────────────────────────────────────────────────
DATASET_DIR = os.path.join(os.path.dirname(__file__), "..", "model dataset")

# Where the trained pipeline will be written (matches model_loader.py)
MODEL_DIR = os.path.join(os.path.dirname(__file__), "models")
MODEL_OUT_PATH = os.path.join(MODEL_DIR, "model.pkl")

# ── Training Data ──────────────────────────────────────────────────────────────
phishing_samples = [
    "http://secure-login-paypal.tk/verify-account",
    "http://amazon-account-suspended.ml/login",
    "http://apple-id-locked.gq/reset-password",
    "http://banking-secure-update.xyz/confirm",
    "http://paypal-security-alert.cf/verify",
    "http://microsoft-account-verify.ga/login",
    "http://192.168.1.1/bank/login",
    "http://10.0.0.1/secure/login",
    "http://secure.bank-login.update.account.info/verify",
    "http://appleid.apple.com.fake-login.tk/signin",
    "http://www.paypa1.com/security/verify",
    "http://login-amazon.account-suspended.net/verify",
    "http://secure-netflix-billing.xyz/update",
    "http://instagram-login-verify.ml/account",
    "http://facebook-security-check.tk/verify",
    "http://google-account-suspended.gq/restore",
    "http://bit.ly/free-iphone-click-now",
    "http://free-gift-card-amazon.xyz/claim",
    "http://congratulations-winner.ml/prize",
    "http://you-have-been-selected.tk/reward",
    "http://bank-secure-verify-account.update.login.info/confirm",
    "http://paypal-verify-account-now.ml/secure/login",
    "http://amazon-suspended-account.gq/verify",
    "http://apple-account-locked-verify.tk/restore",
    "http://microsoft-security-alert.xyz/verify",
    "http://secure-bank-verify.tk/login",
    "http://paypal-account-limited.ml/verify",
    "http://account-update-required.gq/confirm",
    "http://login-verify-secure.xyz/account",
    "http://banking-alert-secure.cf/update",
    "Dear Customer your account has been suspended click here to verify immediately",
    "URGENT your PayPal account is limited verify now to avoid permanent suspension",
    "Your bank account has been compromised update your password immediately",
    "Congratulations you have won $1000 gift card provide credit card details to claim",
    "Your Apple ID has been locked click here to unlock your account now",
    "Dear user your email will be deactivated verify your account within 24 hours",
    "WARNING suspicious login detected on your account click to secure immediately",
    "Your Netflix subscription has been cancelled update payment method now",
    "Dear valued customer your account verification is required click here",
    "You have won a lottery prize of $500000 send your bank details to claim",
    "ALERT your Amazon account has been compromised reset password immediately",
    "Your Microsoft account will be deleted verify your identity now",
    "Urgent action required your credit card has been charged click to dispute",
    "Dear customer we detected unusual activity on your account verify now",
    "Your package could not be delivered click here to reschedule delivery and pay fee",
    "You have a pending payment click here to complete transaction immediately",
    "Your account password has expired update now to continue using service",
    "We noticed a new sign in from unknown device verify now to secure account",
    "Your subscription will expire soon click here to renew avoid interruption",
    "IMPORTANT your account has been flagged for suspicious activity verify now",
    "click here to claim your reward free gift limited time offer act now",
    "your account will be deleted unless you verify within 24 hours urgent",
    "security breach detected on your account immediate action required click",
    "dear user please confirm your email address to avoid account suspension immediately",
    "you have been selected for exclusive offer claim your prize now free",
    "invoice number 8472 overdue payment required click to pay immediately urgent",
    "your credit card ending in 4521 has been charged click to dispute now",
    "new login from Russia detected click here to secure your account now",
    "congratulations your survey response has been selected claim prize now free",
    "IRS tax refund pending provide social security number to claim your refund",
    "Nigerian prince need your help transfer million dollars share profit beneficiary",
    "dear beneficiary you have inherited funds provide bank details to receive",
    "verify account suspended urgent login password reset click here now free",
    "winner congratulations prize claim free gift card click scam site",
    "suspicious activity detected verify identity immediately fake bank login",
    "account compromised reset password now fake bank reset",
    "limited account action required verify now paypal fake verify",
    "http://verify-account.tk Dear Customer click here verify bank account immediately",
    "http://login-secure.ml Your PayPal account is suspended verify now lose access",
    "http://account-update.xyz URGENT your credit card was charged click dispute now",
    "http://secure-banking.gq Dear valued customer update your password immediately",
    "http://apple-verify.cf Your Apple ID is locked click here to restore access now",
]

legitimate_samples = [
    "https://www.google.com",
    "https://www.github.com",
    "https://www.wikipedia.org",
    "https://www.stackoverflow.com",
    "https://www.microsoft.com",
    "https://www.apple.com",
    "https://www.amazon.com",
    "https://www.netflix.com",
    "https://www.linkedin.com",
    "https://www.twitter.com",
    "https://www.facebook.com",
    "https://www.instagram.com",
    "https://www.youtube.com",
    "https://www.reddit.com",
    "https://www.paypal.com",
    "https://docs.python.org/3/library/os.html",
    "https://developer.mozilla.org/en-US/docs/Web/JavaScript",
    "https://www.w3schools.com/html/html_intro.asp",
    "https://en.wikipedia.org/wiki/Phishing",
    "https://support.google.com/accounts/answer/185833",
    "https://github.com/user/repository",
    "https://www.coursera.org/learn/machine-learning",
    "https://www.dropbox.com/s/file/shared",
    "https://docs.google.com/document/edit",
    "https://zoom.us/j/meeting-id",
    "https://www.notion.so/workspace/page",
    "https://slack.com/app/channel/message",
    "https://www.spotify.com/playlist",
    "https://www.medium.com/article/title",
    "https://www.npmjs.com/package/express",
    "Hi team please find the meeting notes attached from yesterday project discussion",
    "Your order has been shipped and will arrive by Friday track your package",
    "Thank you for your purchase your receipt is attached for your records",
    "The weekly team standup is scheduled for Monday at 10am please confirm attendance",
    "Please review the attached document and provide feedback by end of week",
    "Hi there just following up on our conversation from last week about the project",
    "Your subscription has been renewed thank you for continuing with our service",
    "The quarterly report is ready for review please check the shared folder",
    "Reminder your appointment is scheduled for tomorrow at 2pm at our office",
    "Welcome to our newsletter here are this weeks top articles and updates",
    "Your password has been successfully changed if this was not you contact support",
    "Thank you for contacting customer support we will respond within 24 hours",
    "Your account statement for the month of March is now available to view",
    "The project deadline has been moved to next Friday please update your tasks",
    "Hi just wanted to share this interesting article about machine learning trends",
    "Your flight booking confirmation for March 15 is attached please review details",
    "The team lunch is confirmed for Thursday at noon at the Italian restaurant downtown",
    "Please complete the employee satisfaction survey by end of this month",
    "Your package has been delivered and left at the front door as requested",
    "Monthly security newsletter best practices for keeping your accounts safe online",
    "good morning team here is the agenda for todays all hands meeting",
    "please find attached the invoice for services rendered this month",
    "we are excited to announce the launch of our new product feature",
    "your feedback has been received thank you for helping us improve our service",
    "the office will be closed on Monday for the public holiday",
    "congratulations on your promotion well deserved looking forward to working together",
    "the code review has been approved please merge when ready",
    "reminder to submit your timesheet by end of day Friday",
    "your interview is scheduled for Wednesday at 3pm with our hiring team",
    "the server maintenance window is scheduled for Sunday 2am to 4am",
    "https://www.github.com welcome back here are your recent repositories",
    "https://docs.google.com your document has been shared with you by colleague",
    "https://zoom.us meeting starts in 10 minutes click to join the call",
    "https://www.linkedin.com you have a new connection request from John Smith",
    "meeting notes attached please review and share feedback with the team",
    "order shipped tracking number provided estimated delivery Friday afternoon",
    "welcome to the platform here is how to get started with your account setup",
    "your monthly statement is available login to view your transactions history",
    "thank you for registering please verify your email to complete signup process",
    "dear colleague please review the attached proposal and share your thoughts",
]

# ── Load CSV Datasets ──────────────────────────────────────────────────────────
print("\n=== Loading CSV Datasets ===")

# 1. phishing_email.csv
print("\n[1] Loading phishing_email.csv...")
try:
    pe = pd.read_csv(os.path.join(DATASET_DIR, "phishing_email.csv"), on_bad_lines='skip')
    if 'text_combined' in pe.columns and 'label' in pe.columns:
        phishing_samples.extend(pe[pe['label'] == 1]['text_combined'].dropna().head(5000).tolist())
        legitimate_samples.extend(pe[pe['label'] == 0]['text_combined'].dropna().head(5000).tolist())
        print(f"   ✓ Loaded {len(pe)} samples")
except Exception as e:
    print(f"   ⚠ Error: {e}")

# 2. Ling.csv
print("\n[2] Loading Ling.csv...")
try:
    ling = pd.read_csv(os.path.join(DATASET_DIR, "Ling.csv"), on_bad_lines='skip')
    if 'subject' in ling.columns and 'body' in ling.columns and 'label' in ling.columns:
        ling['text'] = ling['subject'].fillna('') + ' ' + ling['body'].fillna('')
        phishing_samples.extend(ling[ling['label'] == 1]['text'].dropna().head(3000).tolist())
        legitimate_samples.extend(ling[ling['label'] == 0]['text'].dropna().head(3000).tolist())
        print(f"   ✓ Loaded {len(ling)} samples")
except Exception as e:
    print(f"   ⚠ Error: {e}")

# 3. CEAS_08.csv
print("\n[3] Loading CEAS_08.csv...")
try:
    ceas = pd.read_csv(os.path.join(DATASET_DIR, "CEAS_08.csv"), on_bad_lines='skip')
    if 'subject' in ceas.columns and 'body' in ceas.columns and 'label' in ceas.columns:
        ceas['text'] = ceas['subject'].fillna('') + ' ' + ceas['body'].fillna('')
        phishing_samples.extend(ceas[ceas['label'] == 1]['text'].dropna().head(3000).tolist())
        legitimate_samples.extend(ceas[ceas['label'] == 0]['text'].dropna().head(3000).tolist())
        print(f"   ✓ Loaded {len(ceas)} samples")
except Exception as e:
    print(f"   ⚠ Error: {e}")

# 4. SpamAssassin.csv (LABELS REVERSED - 1=legitimate, 0=spam)
print("\n[4] Loading SpamAssassin.csv...")
try:
    spam = pd.read_csv(os.path.join(DATASET_DIR, "SpamAssasin.csv"), on_bad_lines='skip')
    if 'subject' in spam.columns and 'body' in spam.columns and 'label' in spam.columns:
        spam['text'] = spam['subject'].fillna('') + ' ' + spam['body'].fillna('')
        # Flip labels: 0 in SpamAssassin = spam/phishing (label 1 for us)
        phishing_samples.extend(spam[spam['label'] == 0]['text'].dropna().head(3000).tolist())
        legitimate_samples.extend(spam[spam['label'] == 1]['text'].dropna().head(3000).tolist())
        print(f"   ✓ Loaded {len(spam)} samples (labels flipped)")
except Exception as e:
    print(f"   ⚠ Error: {e}")

# 5. Nigerian_Fraud.csv
print("\n[5] Loading Nigerian_Fraud.csv...")
try:
    nigerian = pd.read_csv(os.path.join(DATASET_DIR, "Nigerian_Fraud.csv"), on_bad_lines='skip')
    if 'subject' in nigerian.columns and 'body' in nigerian.columns:
        nigerian['text'] = nigerian['subject'].fillna('') + ' ' + nigerian['body'].fillna('')
        phishing_samples.extend(nigerian['text'].dropna().head(2000).tolist())
        print(f"   ✓ Loaded {len(nigerian)} samples (all phishing)")
except Exception as e:
    print(f"   ⚠ Error: {e}")

# 6. Enron.csv
print("\n[6] Loading Enron.csv...")
try:
    enron = pd.read_csv(os.path.join(DATASET_DIR, "Enron.csv"), on_bad_lines='skip')
    if 'subject' in enron.columns and 'body' in enron.columns and 'label' in enron.columns:
        enron['text'] = enron['subject'].fillna('') + ' ' + enron['body'].fillna('')
        phishing_samples.extend(enron[enron['label'] == 1]['text'].dropna().head(3000).tolist())
        legitimate_samples.extend(enron[enron['label'] == 0]['text'].dropna().head(3000).tolist())
        print(f"   ✓ Loaded {len(enron)} samples")
except Exception as e:
    print(f"   ⚠ Error: {e}")

# 7. Nazario.csv
print("\n[7] Loading Nazario.csv...")
try:
    nazario = pd.read_csv(os.path.join(DATASET_DIR, "Nazario.csv"), on_bad_lines='skip')
    if 'subject' in nazario.columns and 'body' in nazario.columns and 'label' in nazario.columns:
        nazario['text'] = nazario['subject'].fillna('') + ' ' + nazario['body'].fillna('')
        phishing_samples.extend(nazario[nazario['label'] == 1]['text'].dropna().head(3000).tolist())
        legitimate_samples.extend(nazario[nazario['label'] == 0]['text'].dropna().head(3000).tolist())
        print(f"   ✓ Loaded {len(nazario)} samples")
    else:
        print(f"   ⚠ Columns not found. Available: {nazario.columns.tolist()}")
except Exception as e:
    print(f"   ⚠ Error: {e}")

# 8. phishing_site_urls.csv
print("\n[8] Loading phishing_site_urls.csv...")
try:
    urls = pd.read_csv(os.path.join(DATASET_DIR, "phishing_site_urls.csv"), on_bad_lines='skip')
    if 'URL' in urls.columns and 'Label' in urls.columns:
        phishing_samples.extend(urls[urls['Label'] == 'bad']['URL'].dropna().head(10000).tolist())
        legitimate_samples.extend(urls[urls['Label'] == 'good']['URL'].dropna().head(10000).tolist())
        print(f"   ✓ Loaded {len(urls)} samples")
except Exception as e:
    print(f"   ⚠ Error: {e}")

print("\n=== Dataset Loading Complete ===")

texts = phishing_samples + legitimate_samples
labels = [1] * len(phishing_samples) + [0] * len(legitimate_samples)

print(f"Total samples: {len(texts)}")
print(f"Phishing: {sum(labels)}, Legitimate: {len(labels) - sum(labels)}")

# ── Model with FeatureUnion ────────────────────────────────────────────────────
from sklearn.pipeline import Pipeline, FeatureUnion

feature_union = FeatureUnion([
    ('word_tfidf', TfidfVectorizer(
        ngram_range=(1, 3),
        max_features=6000,
        sublinear_tf=True,
        analyzer='word',
        token_pattern=r'\b[a-zA-Z0-9_.:/\-]+\b'
    )),
    ('char_tfidf', TfidfVectorizer(
        ngram_range=(2, 4),
        max_features=4000,
        sublinear_tf=True,
        analyzer='char_wb'
    )),
    ('custom_features', TextFeatureExtractor()),
])

lr = LogisticRegression(C=2.0, max_iter=1000, class_weight='balanced')
svc = CalibratedClassifierCV(LinearSVC(C=1.0, max_iter=2000, class_weight='balanced'))
rf = RandomForestClassifier(n_estimators=300, max_depth=15, class_weight='balanced', random_state=42)

voting_clf = VotingClassifier(
    estimators=[('lr', lr), ('svc', svc), ('rf', rf)],
    voting='soft'
)

pipeline = Pipeline([
    ('features', feature_union),
    ('clf', voting_clf)
])

# ── Cross Validation ───────────────────────────────────────────────────────────
print("\nRunning cross-validation...")
scores = cross_val_score(pipeline, texts, labels, cv=5, scoring='accuracy')
print(f"Cross-validation accuracy: {scores.mean():.3f} (+/- {scores.std():.3f})")

# ── Train ──────────────────────────────────────────────────────────────────────
pipeline.fit(texts, labels)

# ── Test ───────────────────────────────────────────────────────────────────────
test_cases = [
    ("http://secure-bank-verify.tk/login", 1),
    ("https://www.google.com", 0),
    ("Your account is suspended verify now urgent click here", 1),
    ("Hi team meeting notes attached please review", 0),
    ("http://paypal-account-limited.ml/verify", 1),
    ("https://github.com/user/repository", 0),
    ("Congratulations you won $1000 gift card claim now free", 1),
    ("Your order has been shipped delivery expected Friday", 0),
    ("http://192.168.1.1/bank/login", 1),
    ("https://www.microsoft.com/en-us/security", 0),
    ("URGENT your account will be deleted verify now click here", 1),
    ("Please find attached the quarterly report for your review", 0),
    ("http://login-verify-secure.xyz/account", 1),
    ("https://stackoverflow.com/questions/12345", 0),
    ("Dear beneficiary you have inherited funds provide bank details", 1),
    ("The team lunch is confirmed for Thursday at noon", 0),
]

print("\nTest predictions:")
correct = 0
for text, expected in test_cases:
    pred = pipeline.predict([text])[0]
    score = pipeline.predict_proba([text])[0][1]
    status = "✓" if pred == expected else "✗"
    label = "PHISHING" if pred == 1 else "LEGIT"
    print(f"  {status} [{score:.2f}] [{label}] {text[:60]}")
    if pred == expected:
        correct += 1

print(f"\nTest accuracy: {correct}/{len(test_cases)} ({correct/len(test_cases)*100:.0f}%)")

# ── Save ───────────────────────────────────────────────────────────────────────
os.makedirs(MODEL_DIR, exist_ok=True)
joblib.dump(pipeline, MODEL_OUT_PATH)
print(f"\nModel saved to: {MODEL_OUT_PATH}")