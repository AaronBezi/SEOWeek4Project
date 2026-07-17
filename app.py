from flask import Flask, render_template, url_for, flash, redirect, request
from flask_behind_proxy import FlaskBehindProxy
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from forms import RegistrationForm, LoginForm, CreatePoolForm
from database.models import User,Notes,Notes_Summary, StudyGroup, GroupMembership, Message
from database.database import db
from storage import allowed_file, upload_note_file, get_note_file
from api.openAI_api import generate_summary
from pusher import Pusher
import git
import os
import subprocess
from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__)                    # this gets the name of the file so Flask knows it's name
proxied = FlaskBehindProxy(app)          # handle codio redirection

app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')

pusher_client = Pusher(
    app_id = os.getenv('PUSHER_APP_ID'),
    key = os.getenv('PUSHER_KEY'),
    secret = os.getenv('PUSHER_SECRET'),
    cluster = os.getenv('PUSHER_CLUSTER'),
    ssl = True
)

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
        if User.query.filter_by(username=form.username.data).first():
            form.username.errors.append('Username already taken.')
            return render_template('register.html', title='Register', form=form)
        if User.query.filter_by(email=form.email.data).first():
            form.email.errors.append('Email already registered.')
            return render_template('register.html', title='Register', form=form)
        hashed_password = generate_password_hash(form.password.data)
        user = User(username=form.username.data,email=form.email.data,
                    password = hashed_password)
        db.session.add(user) #add user into database
        db.session.commit()  #save changes to database
        login_user(user)  # logins the user so they don't need to log in after signup. 
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
    
    group_id = request.form.get('group_id') or None

    storage_note_id,filepath = upload_note_file(file)
    Notes.create_Note(current_user.user_id,file.filename,filepath,group_id)      #saves note to database
    return {'storage_note_id': storage_note_id}, 200


@app.route("/my_notes")
@login_required
def my_notes():
    notes = Notes.query.filter_by(user_id=current_user.user_id, group_id=None).all()
    my_pools = StudyGroup.query.join(GroupMembership, StudyGroup.group_id == GroupMembership.group_id) \
                                .filter(GroupMembership.user_id == current_user.user_id).all()
    
    note_urls = {note.notes_id: get_note_file(note.file_path) for note in notes}  # list comprehension practice: key: value for x in values

    return render_template('my_notes.html', title='My Notes', notes=notes, my_pools=my_pools, note_urls=note_urls)


@app.route("/create_pool", methods=['POST', 'GET'])
@login_required
def create_pool():
    form = CreatePoolForm()
    if form.validate_on_submit(): # checks if entries are valid
        pool = StudyGroup(group_name=form.group_name.data, created_by=current_user.user_id)
        db.session.add(pool)
        db.session.commit()  # commit so pool.group_id actually gets assigned. 

        membership = GroupMembership(group_id=pool.group_id, user_id=current_user.user_id)
        db.session.add(membership)
        db.session.commit()

        flash(f'Pool "{pool.group_name}" created!', 'success')
        return redirect(url_for('pool_space', pool_id=pool.group_id)) # if so - send to pool space.
    return render_template('create_pool.html', title='Create Pool', form=form)
    

@app.route("/pool_space/<int:pool_id>")
@login_required
def pool_space(pool_id):
    pool = StudyGroup.query.get_or_404(pool_id)

    membership = GroupMembership.query.filter_by(group_id=pool_id, user_id=current_user.user_id).first()
    if not membership:
        flash('Join this pool to view its space.', 'error')
        return redirect(url_for('join_pool'))
    
    members = User.query.join(GroupMembership, User.user_id == GroupMembership.user_id).filter(GroupMembership.group_id == pool_id).all()
    notes = Notes.query.filter_by(group_id=pool_id).all()  # a list of note objects 
    note_urls = {}  # key = note id, val = file path for that note id 
    for note in notes:  
        note_urls[note.notes_id] = get_note_file(note.file_path)

    return render_template('pool_space.html', title=pool.group_name, pool=pool, members=members, notes=notes, note_urls=note_urls)


@app.route("/join_pool")
@login_required
def join_pool():
    pools = db.session.query(StudyGroup, User.username).join(User, StudyGroup.created_by == User.user_id).all()
    my_membership_ids = {m.group_id for m in GroupMembership.query.filter_by(user_id=current_user.user_id).all()}
    return render_template('join_pool.html', title='Join a Pool', pools=pools, my_membership_ids=my_membership_ids)


@app.route("/join_pool/<int:pool_id>/join", methods=['POST'])
@login_required
def join_pool_action(pool_id):
    pool = StudyGroup.query.get_or_404(pool_id)
    existing = GroupMembership.query.filter_by(group_id=pool_id, user_id=current_user.user_id).first()
    if not existing:
        membership = GroupMembership(group_id=pool_id, user_id=current_user.user_id)
        db.session.add(membership)
        db.session.commit()
        flash(f'Joined "{pool.group_name}"!', 'success')
    return redirect(url_for('pool_space', pool_id=pool_id))


@app.route("/api/summarize", methods=['POST'])
def summarize():
    #query the users notes and summarize them one by one displaying them to the screen
    if not current_user.is_authenticated:
        return {'error': 'User not logged in'}, 401

    notes = Notes.query.filter_by(user_id=current_user.user_id).all()  # fetch all notes for this user
    if not notes:
        return {'error': 'No notes found to summarize'}, 400

    summaries = []
    
    for note in notes:
        result = generate_summary(note)
        if not result.get('success'):
            return {"success": False,'error': result.get('error', 'Could not generate summary')}, 500
        summaries.append({"note_name":note.note_name, "summary": result['summary']})
    
    return {"success": True, "summary": summaries},200
    # notes_text = [note.note_name for note in notes]  # collect note names as text to summarize

    # if not result.get('success'):
    #     return {'error': result.get('error', 'Could not generate summary')}, 500

    # return {'success': True, 'summary': result['summary']}, 200





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








