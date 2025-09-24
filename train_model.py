import pickle
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB

# Improved & Balanced Training Data
titles = [
    "Chocolate Cake", "Vanilla Ice Cream", "Fruit Salad", "Brownie", "Kunafa",
    "Grilled Chicken", "Tandoori Chicken", "Beef Steak", "Chicken Wrap", "Pasta Alfredo",
    "Veggie Burger", "Cheesy Fries", "French Fries", "Sandwich", "Spring Rolls"
]

categories = [
    "Dessert", "Dessert", "Snack", "Dessert", "Dessert",
    "Main Course", "Main Course", "Main Course", "Main Course", "Main Course",
    "Snack", "Snack", "Snack", "Snack", "Snack"
]

# TF-IDF Vectorizer is better than CountVectorizer for small text
vectorizer = TfidfVectorizer(ngram_range=(1, 2))
X = vectorizer.fit_transform(titles)

# Train Naive Bayes model
model = MultinomialNB()
model.fit(X, categories)

# Save model & vectorizer
with open('ml_model.pkl', 'wb') as f:
    pickle.dump((vectorizer, model), f)

print("✅ Improved model trained and saved as ml_model.pkl")
