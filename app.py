from flask import Flask, render_template, url_for, flash, redirect, request
from flask_behind_proxy import FlaskBehindProxy
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from forms import RegistrationForm, LoginForm, CreatePoolForm
from database.models import User, Notes, Notes_Summary, StudyGroup, GroupMembership
from database.database import db
from storage import allowed_file, upload_note_file, get_note_file
from api.openAI_api import generate_summary
import git
import os
import subprocess
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)  # This gets the name of the file so Flask knows its name
proxied = FlaskBehindProxy(app)  # Handle Codio redirection

app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')

db.init_app(app)

with app.app_context():
    db.create_all()

login_manager = LoginManager()  # Create the extension object
login_manager.login_view = 'login'  # Indicates route to send to if they hit a page marked @login_required
login_manager.init_app(app)  # Bind object to this app


# --- ANTI-CACHING ENHANCEMENT FOR LOCAL DEV ---
@app.after_request
def add_header(response):
    """Instructs the browser to drop past versions and fetch fresh code updates."""
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route("/")
def home():
    return render_template('index.html')


@app.route("/register", methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        if User.query.filter_by(username=form.username.data).first():
            form.username.errors.append('Username already taken.')
            return render_template('register.html', title='Register', form=form)
        if User.query.filter_by(email=form.email.data).first():
            form.email.errors.append('Email already registered.')
            return render_template('register.html', title='Register', form=form)
        hashed_password = generate_password_hash(form.password.data)
        user = User(username=form.username.data, email=form.email.data, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        login_user(user)
        flash(f'Account created for {form.username.data}!', 'success')
        return redirect(url_for('home'))
    return render_template('register.html', title='Register', form=form)


@app.route("/login", methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and check_password_hash(user.password, form.password.data):
            login_user(user)
            flash(f'Welcome back, {user.username}!', 'success')
            return redirect(url_for('home'))
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

    storage_note_id, filepath = upload_note_file(file)
    Notes.create_Note(current_user.user_id, file.filename, filepath, group_id)
    return {'storage_note_id': storage_note_id}, 200


@app.route("/my_notes")
@login_required
def my_notes():
    notes = Notes.query.filter_by(user_id=current_user.user_id, group_id=None).all()
    my_pools = StudyGroup.query.join(GroupMembership, StudyGroup.group_id == GroupMembership.group_id) \
        .filter(GroupMembership.user_id == current_user.user_id).all()
    note_urls = {note.notes_id: get_note_file(note.file_path) for note in notes}
    return render_template('my_notes.html', title='My Notes', notes=notes, my_pools=my_pools, note_urls=note_urls)


@app.route("/create_pool", methods=['POST', 'GET'])
@login_required
def create_pool():
    form = CreatePoolForm()
    if form.validate_on_submit():
        pool = StudyGroup(group_name=form.group_name.data, created_by=current_user.user_id)
        db.session.add(pool)
        db.session.commit()

        membership = GroupMembership(group_id=pool.group_id, user_id=current_user.user_id)
        db.session.add(membership)
        db.session.commit()

        flash(f'Pool "{pool.group_name}" created!', 'success')
        return redirect(url_for('pool_space', pool_id=pool.group_id))
    return render_template('create_pool.html', title='Create Pool', form=form)


@app.route("/pool_space/<int:pool_id>")
@login_required
def pool_space(pool_id):
    pool = StudyGroup.query.get_or_404(pool_id)
    membership = GroupMembership.query.filter_by(group_id=pool_id, user_id=current_user.user_id).first()
    if not membership:
        flash('Join this pool to view its space.', 'error')
        return redirect(url_for('join_pool'))

    members = User.query.join(GroupMembership, User.user_id == GroupMembership.user_id).filter(
        GroupMembership.group_id == pool_id).all()
    notes = Notes.query.filter_by(group_id=pool_id).all()
    note_urls = {}
    for note in notes:
        note_urls[note.notes_id] = get_note_file(note.file_path)

    return render_template('pool_space.html', title=pool.group_name, pool=pool, members=members, notes=notes,
                           note_urls=note_urls)


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
    if not current_user.is_authenticated:
        return {'error': 'User not logged in'}, 401

    data = request.get_json() or {}
    group_id = data.get('group_id')

    if group_id:
        # isolates notes to only the study pool user is currently viewing
        notes = Notes.query.filter_by(user_id=current_user.user_id, group_id=group_id).all()
    else:
        # for private dashboard space
        notes = Notes.query.filter_by(user_id=current_user.user_id, group_id=None).all()

    if not notes:
        return {'error': 'No notes found to summarize in this workspace'}, 400

    summaries = []
    for note in notes:
        result = generate_summary(note)
        if not result.get('success'):
            return {"success": False, 'error': result.get('error', 'Could not generate summary')}, 500
        summaries.append({"note_name": note.note_name, "summary": result['summary']})

    return {"success": True, "summary": summaries}, 200


@app.route("/update_server", methods=['POST'])
def webhook():
    if request.method == 'POST':
        repo = git.Repo('/home/seoproject2/SEOWeek4Project')
        origin = repo.remotes.origin
        origin.pull()

        venv_pip = '/home/seoproject2/.virtualenvs/studypool-venv/bin/pip'
        result = subprocess.run([venv_pip, 'install', '-r', 'requirements.txt'],
                                cwd='/home/seoproject2/SEOWeek4Project')
        if result.returncode != 0:
            return 'pip install failed', 500
        os.utime('/var/www/seoproject2_pythonanywhere_com_wsgi.py', None)
        return 'Updated PythonAnywhere successfully', 200
    else:
        return 'Wrong event type', 400


if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=8080)