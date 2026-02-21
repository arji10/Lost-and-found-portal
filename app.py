from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import pandas as pd
import os
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-999')
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'database.db')
app.config['UPLOAD_FOLDER'] = os.path.join(basedir, 'static', 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

db = SQLAlchemy(app)

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Login Manager Setup
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# --- Database Models ---

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), default='user') # 'admin' or 'user'

class Item(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50))
    image = db.Column(db.String(200))
    location = db.Column(db.String(100), nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    contact = db.Column(db.String(100), nullable=False)
    reporter_name = db.Column(db.String(100), nullable=False) # Changed from posted_by FK
    type = db.Column(db.String(10), nullable=False)  # 'lost' or 'found'
    status = db.Column(db.String(20), default='available')  # 'available' or 'returned'

# --- Helper Functions ---

def get_matches(lost_item_desc):
    found_items = Item.query.filter_by(type='found', status='available').all()
    if not found_items:
        return []
    
    descriptions = [item.description for item in found_items]
    descriptions.append(lost_item_desc)
    
    vectorizer = TfidfVectorizer(stop_words='english')
    tfidf_matrix = vectorizer.fit_transform(descriptions)
    
    # Compare the last item (lost) with all previous (found)
    cosine_sim = cosine_similarity(tfidf_matrix[-1], tfidf_matrix[:-1])[0]
    
    results = []
    for i, score in enumerate(cosine_sim):
        if score > 0.1:  # Threshold
            results.append({
                'item': found_items[i],
                'similarity': round(score * 100, 2)
            })
    
    # Sort by similarity and return top 3
    results = sorted(results, key=lambda x: x['similarity'], reverse=True)
    return results[:3]

# --- Routes ---

@app.route('/')
def index():
    recent_found = Item.query.filter_by(type='found', status='available').order_by(Item.date.desc()).limit(6).all()
    return render_template('index.html', recent_found=recent_found)

@app.route('/post-lost', methods=['GET', 'POST'])
def post_lost():
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        location = request.form.get('location')
        date_str = request.form.get('date')
        contact = request.form.get('contact')
        reporter_name = request.form.get('reporter_name')
        
        file = request.files.get('image')
        filename = None
        if file:
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        
        new_item = Item(
            title=title,
            description=description,
            location=location,
            date=datetime.strptime(date_str, '%Y-%m-%d') if date_str else datetime.utcnow(),
            contact=contact,
            reporter_name=reporter_name,
            image=filename,
            type='lost'
        )
        db.session.add(new_item)
        db.session.commit()
        
        # Trigger Smart Matching
        matches = get_matches(description)
        return render_template('matches.html', matches=matches)
        
    return render_template('post_lost.html')

@app.route('/post-found', methods=['GET', 'POST'])
def post_found():
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        location = request.form.get('location')
        date_str = request.form.get('date')
        contact = request.form.get('contact')
        reporter_name = request.form.get('reporter_name')
        is_admin_desk = request.form.get('submitted_to_admin') == 'on'
        
        file = request.files.get('image')
        filename = None
        if file:
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        
        new_item = Item(
            title=title,
            description=description,
            location=location,
            date=datetime.strptime(date_str, '%Y-%m-%d') if date_str else datetime.utcnow(),
            contact=contact,
            reporter_name=reporter_name,
            image=filename,
            type='found'
        )
        if is_admin_desk:
            new_item.category = 'admin_desk'
            
        db.session.add(new_item)
        db.session.commit()
        flash('Found item posted successfully!', 'success')
        return redirect(url_for('browse'))
        
    return render_template('post_found.html')

@app.route('/browse')
def browse():
    query = request.args.get('q', '')
    if query:
        items = Item.query.filter(
            (Item.title.contains(query)) | (Item.location.contains(query))
        ).order_by(Item.date.desc()).all()
    else:
        items = Item.query.order_by(Item.date.desc()).all()
    return render_template('browse.html', items=items, query=query)

# --- Authentication Routes ---

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()
        print(f"DEBUG: Login try for {email}. Found={bool(user)}", flush=True)
        
        if not user:
            # Check if any user exists at all
            user_count = User.query.count()
            print(f"DEBUG: Total users in DB: {user_count}", flush=True)
            flash(f'No account found with email: {email}', 'warning')
        elif not check_password_hash(user.password, password):
            flash('Incorrect password. Please try again.', 'danger')
        elif user.role != 'admin':
            flash('Access denied. This area is for administrators only.', 'danger')
        else:
            login_user(user)
            flash(f'Welcome back, {user.name}!', 'success')
            return redirect(url_for('admin_panel'))
            
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/admin')
@login_required
def admin_panel():
    items = Item.query.order_by(Item.date.desc()).all()
    return render_template('admin.html', items=items)

@app.route('/admin/delete/<int:item_id>')
@login_required
def delete_item(item_id):
    item = Item.query.get_or_404(item_id)
    db.session.delete(item)
    db.session.commit()
    flash('Item deleted successfully', 'success')
    return redirect(url_for('admin_panel'))

@app.route('/admin/return/<int:item_id>')
@login_required
def mark_returned(item_id):
    item = Item.query.get_or_404(item_id)
    item.status = 'returned'
    db.session.commit()
    flash('Item marked as returned', 'info')
    return redirect(url_for('admin_panel'))

# Initialize Database & Auto-Seed Admin
with app.app_context():
    db.create_all()
    # Check if admin exists specifically by email
    admin_check = User.query.filter_by(email='admin@example.com').first()
    if not admin_check:
        print("SEEDING: Creating default admin account...", flush=True)
        admin = User(
            name="Admin User",
            email="admin@example.com",
            password=generate_password_hash("admin123", method='pbkdf2:sha256'),
            role="admin"
        )
        db.session.add(admin)
        db.session.commit()
        print("SEEDING: Admin created: admin@example.com / admin123", flush=True)
    else:
        print(f"SEEDING: Admin already exists ({admin_check.email})", flush=True)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5001))
    app.run(debug=True, host='0.0.0.0', port=port)
