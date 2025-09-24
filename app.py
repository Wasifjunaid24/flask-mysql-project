from flask import Flask, render_template, redirect, request, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from forms import RegistrationForm, LoginForm, RecipeForm, CommentForm
from models import db, User, Recipe, Comment
from config import Config
from textblob import TextBlob
from werkzeug.utils import secure_filename
import pickle
import os

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Load ML model
with open('ml_model.pkl', 'rb') as f:
    vectorizer, model = pickle.load(f)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/index')
def index():
    search_query = request.args.get('search', '').strip()
    recipes = Recipe.query.filter(Recipe.title.ilike(f'%{search_query}%')).all() if search_query else Recipe.query.all()
    message = "No results found." if search_query and not recipes else None
    return render_template('index.html', recipes=recipes, message=message)

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, password=form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Account created!', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.password == form.password.data:
            login_user(user)
            flash('Logged in!', 'success')
            return redirect(url_for('home'))
        flash('Invalid credentials.', 'danger')
    return render_template('login.html', form=form)

@app.route('/submit_recipe', methods=['GET', 'POST'])
@login_required
def submit_recipe():
    form = RecipeForm()
    if form.validate_on_submit():
        title = form.title.data
        X = vectorizer.transform([title])
        predicted_category = model.predict(X)[0]

        # Image Upload Handling
        image_file = request.files.get('image')
        image_filename = None
        if image_file and image_file.filename != '':
            image_filename = secure_filename(image_file.filename)
            image_path = os.path.join(app.root_path, 'static/uploads', image_filename)
            image_file.save(image_path)

        recipe = Recipe(
            title=title,
            ingredients=form.ingredients.data,
            instructions=form.instructions.data,
            cooking_time=form.cooking_time.data,
            category=predicted_category,
            image=image_filename,
            user_id=current_user.id
        )
        db.session.add(recipe)
        db.session.commit()
        flash(f'Recipe submitted! Predicted Category: {predicted_category}', 'success')
        return redirect(url_for('index'))
    return render_template('submit_recipe.html', form=form)

@app.route('/admin')
@login_required
def admin_dashboard():
    if not current_user.is_admin:
        flash("Access denied.", "danger")
        return redirect(url_for('home'))
    users = User.query.all()
    recipes = Recipe.query.all()
    return render_template('admin_dashboard.html', users=users, recipes=recipes)

@app.route('/admin/delete_user/<int:user_id>', methods=['POST'])
@login_required
def delete_user(user_id):
    if not current_user.is_admin:
        flash("Access denied.", "danger")
        return redirect(url_for('home'))
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    flash('User deleted.', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/delete_recipe/<int:recipe_id>', methods=['POST'])
@login_required
def delete_recipe(recipe_id):
    if not current_user.is_admin:
        flash("Access denied.", "danger")
        return redirect(url_for('home'))
    recipe = Recipe.query.get_or_404(recipe_id)
    db.session.delete(recipe)
    db.session.commit()
    flash('Recipe deleted.', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out.', 'info')
    return redirect(url_for('home'))

@app.route('/recipe/<int:recipe_id>', methods=['GET', 'POST'])
def recipe_detail(recipe_id):
    recipe = Recipe.query.get_or_404(recipe_id)
    form = CommentForm()
    if form.validate_on_submit() and current_user.is_authenticated:
        sentiment = TextBlob(form.content.data).sentiment.polarity
        comment = Comment(content=form.content.data, recipe_id=recipe.id, user_id=current_user.id)
        db.session.add(comment)
        db.session.commit()
        flash(f'Comment added! Sentiment: {"Positive" if sentiment > 0 else "Negative" if sentiment < 0 else "Neutral"}', 'success')
        return redirect(url_for('recipe_detail', recipe_id=recipe.id))
    keywords = recipe.title.lower().split()
    recommended = [r for r in Recipe.query.filter(Recipe.id != recipe.id).all() if any(k in r.title.lower() for k in keywords)]
    return render_template('recipe_detail.html', recipe=recipe, form=form, comments=recipe.comments, recommended=recommended)

@app.route('/search_by_ingredients', methods=['GET', 'POST'])
def search_by_ingredients():
    recipes = []
    message = ""
    if request.method == 'POST':
        input_ingredients = request.form.get('ingredients').lower().split(',')
        input_ingredients = [i.strip() for i in input_ingredients]
        all_recipes = Recipe.query.all()
        for recipe in all_recipes:
            if all(ingredient in recipe.ingredients.lower() for ingredient in input_ingredients):
                recipes.append(recipe)
        if not recipes:
            message = "No recipes found matching all selected ingredients."
    return render_template('search_by_ingredients.html', recipes=recipes, message=message)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
