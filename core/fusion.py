from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

# Initialize the ML Analyzer once
analyzer = SentimentIntensityAnalyzer()

def calculate_wellness_fusion(facial_emotion, text_input):
    """
    Upgraded: Uses VADER Machine Learning with a High-Priority Veto 
    for grief and loss to prevent 'Smiling through pain' errors.
    """
    text_input = text_input.lower()
    
    # --- 🚀 1. THE VETO LIST (High Priority over Face) ---
    # We check these FIRST. If matched, we exit before doing any averaging.
    grief_words = ['passed away', 'died', 'death', 'lost my', 'funeral', 'gone']
    urgent_words = ['pain', 'hurts', 'emergency', 'help', 'fell', 'dizzy']

    if any(word in text_input for word in urgent_words):
        return 15, "CRITICAL (Physical Distress Alert)"
    
    if any(word in text_input for word in grief_words):
        # Even if the face is 'happy', this tragic news sets the score to 25
        return 25, "WARNING (Significant Emotional Loss)"

    # --- 2. ML SENTIMENT ANALYSIS ---
    # 'compound' score ranges from -1 (very negative) to 1 (very positive)
    sentiment_scores = analyzer.polarity_scores(text_input)
    compound_score = sentiment_scores['compound']
    
    # Convert ML score (-1 to 1) to a 0-100 scale
    # Calculation: (Score + 1) * 50
    text_wellness = (compound_score + 1) * 50

    # --- 3. FACIAL EMOTION MAPPING ---
    face_map = {
        "happy": 95, 
        "neutral": 70, 
        "surprise": 80,
        "sad": 30, 
        "fear": 25, 
        "angry": 20
    }
    face_score = face_map.get(facial_emotion.lower(), 70)

    # --- 4. FUSION WEIGHTING ---
    # We trust the ML Text Analysis 70% and the Face 30%
    final_score = (text_wellness * 0.7) + (face_score * 0.3)
    
    # --- 5. DETERMINING LABEL ---
    if compound_score <= -0.5:
        label = "Warning (Highly Negative Sentiment)"
    elif facial_emotion in ['sad', 'fear'] and compound_score > 0.1:
        label = "Discordant (Masked Sadness)"
    elif compound_score > 0.5:
        label = "Harmony (Genuine Positive)"
    else:
        label = "Stable (Neutral/Balanced)"

    return int(final_score), label

def generate_daily_hashtags(user_text):
    """
    Helper function to generate tags for the digital diary.
    """
    tags = ["#DailyLog"]
    text = user_text.lower()
    if "friend" in text: tags.append("#Friendship")
    if "walk" in text: tags.append("#Activity")
    if "food" in text or "cook" in text: tags.append("#Cooking")
    return tags[:3]