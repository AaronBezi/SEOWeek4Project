from flask import Flask, render_template, url_for, flash, redirect, request
from flask_behind_proxy import FlaskBehindProxy
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from forms import RegistrationForm, LoginForm
from database.models import User,Notes,Notes_Summary
from database.database import db
from storage import allowed_file, upload_note_file
import git
import os
import subprocess
from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__)                    # this gets the name of the file so Flask knows it's name
proxied = FlaskBehindProxy(app)          # handle codio redirection

app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')

db.init_app(app)

with app.app_context():
    db.create_all()


login_manager = LoginManager()  # create the extension object
login_manager.login_view = 'login'  # indicates route to send to if they hit a page marked @login_required
login_manager.init_app(app)  # bind object to this app

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# @login_manager.user_loader       #loads User object into flask app.
# def load_user(user_id):
#     return db.session.get(User,int(user_id))

@app.route("/")
def home():
    # renders the index.html file from the templates folder
    return render_template('index.html')

@app.route("/register", methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit(): # checks if entries are valid
        hashed_password = generate_password_hash(form.password.data)
        user = User(username=form.username.data,email=form.email.data,
                    password = hashed_password)
        db.session.add(user) #add user into database
        db.session.commit()  #save changes to database
        flash(f'Account created for {form.username.data}!', 'success')
        return redirect(url_for('home')) # if so - send to home page
    return render_template('register.html', title='Register', form=form)

@app.route("/login", methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit(): # checks if entries are valid
        user = User.query.filter_by(email=form.email.data).first() # searches for user by email and returns that row of user information
        if user and check_password_hash(user.password, form.password.data): # verifies user exists and then checks if password matches.
            login_user(user)
            flash(f'Welcome back, {user.username}!', 'success')
            return redirect(url_for('home')) # if so - log in the user and send to home page
        
        flash(f'Invalid email or password.', 'error')

    return render_template('login.html', title='Sign In', form=form)

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route("/upload", methods=['POST'])
def upload():
    if not current_user.is_authenticated:
        return {"error": "User not logged in"}, 401
    
    file = request.files.get('file')
    if file is None or file.filename == '':
        return {'error': 'No file provided'}, 400
    
    if not allowed_file(file.filename):
        return {'error': 'Unsupported file format'}, 400
    
    storage_note_id,filepath = upload_note_file(file)
    Notes.create_Note(current_user.user_id,file.filename,filepath)      #saves note to database
    return {'storage_note_id': storage_note_id}, 200


@app.route("/update_server", methods=['POST'])
def webhook():
    if request.method == 'POST':
        repo = git.Repo('/home/seoproject2/SEOWeek4Project')
        origin = repo.remotes.origin
        origin.pull()
        # ensures that proper modules are installed after pulling new code
        venv_pip = '/home/seoproject2/.virtualenvs/studypool-venv/bin/pip'
        result = subprocess.run([venv_pip, 'install', '-r', 'requirements.txt'], cwd='/home/seoproject2/SEOWeek4Project')
        if result.returncode != 0:
            return 'pip install failed', 500
        os.utime('/var/www/seoproject2_pythonanywhere_com_wsgi.py', None)
        return 'Updated PythonAnywhere successfully', 200
    else:
        return 'Wrong event type', 400


if __name__ == '__main__':               # this should always be at the end
    app.run(debug=True, host="0.0.0.0", port=8080)









