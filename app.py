from flask import Flask, render_template, url_for, flash, redirect, request, jsonify
from flask_behind_proxy import FlaskBehindProxy
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from forms import RegistrationForm, LoginForm, CreatePoolForm, JoinPoolForm
from database.models import User, Notes, Notes_Summary, StudyGroup, GroupMembership, Message
from database.database import db
from storage import allowed_file, upload_note_file, get_note_file, delete_note_file
from api.openAI_api import generate_summary, generate_quiz_from_summary
from api.recommendations.rec_queries import search_books
from pusher import Pusher
import secrets
import git
import os
import subprocess
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)  # this gets the name of the file so Flask knows its name
proxied = FlaskBehindProxy(app)  # handle codio redirection

app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')

# Initialize Pusher for real-time chat spaces
pusher_client = Pusher(
    app_id=os.getenv('PUSHER_APP_ID'),
    key=os.getenv('PUSHER_KEY'),
    secret=os.getenv('PUSHER_SECRET'),
    cluster=os.getenv('PUSHER_CLUSTER'),
    ssl=True
)

db.init_app(app)

with app.app_context():
    db.create_all()

login_manager = LoginManager()  # create the extension object
login_manager.login_view = 'login'  # indicates route to send to if they hit a page marked @login_required
login_manager.init_app(app)  # bind object to this app


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


@app.route("/")
def home():
    # renders the index.html file from the templates folder
    return render_template('index.html')


@app.route("/register", methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():  # checks if entries are valid
        if User.query.filter_by(username=form.username.data).first():
            form.username.errors.append('Username already taken.')
            return render_template('register.html', title='Register', form=form)
        if User.query.filter_by(email=form.email.data).first():
            form.email.errors.append('Email already registered.')
            return render_template('register.html', title='Register', form=form)
        hashed_password = generate_password_hash(form.password.data)
        user = User(username=form.username.data, email=form.email.data, password=hashed_password)
        db.session.add(user)  # add user into database
        db.session.commit()  # save changes to database
        login_user(user)  # logins the user so they don't need to log in after signup.
        flash(f'Account created for {form.username.data}!', 'success')

        return redirect(url_for('home'))  # if so - send to home page
    return render_template('register.html', title='Register', form=form)


@app.route("/login", methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():  # checks if entries are valid
        user = User.query.filter_by(email=form.email.data).first()
        if user and check_password_hash(user.password, form.password.data):
            login_user(user)
            flash(f'Welcome back, {user.username}!', 'success')
            return redirect(url_for('home'))

        flash('Invalid email or password.', 'error')

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

    group_id = request.form.get('group_id')
    if group_id == "0":
        group_id = None

    storage_note_id, filepath = upload_note_file(file)
    Notes.create_Note(current_user.user_id, file.filename, filepath, group_id)  # saves note to database
    return {'storage_note_id': storage_note_id}, 200


@app.route("/my_notes")
@login_required
def my_notes():
    notes = Notes.query.filter_by(user_id=current_user.user_id, group_id=None).all()
    my_pools = StudyGroup.query.join(GroupMembership, StudyGroup.group_id == GroupMembership.group_id) \
        .filter(GroupMembership.user_id == current_user.user_id).all()

    note_urls = {note.notes_id: get_note_file(note.file_path) for note in notes}

    return render_template('my_notes.html', title='My Notes', notes=notes, my_pools=my_pools, note_urls=note_urls)


@app.route("/notes/<int:note_id>/delete", methods=['POST'])
@login_required
def delete_note(note_id):
    note = Notes.query.get_or_404(note_id)
    pool = StudyGroup.query.get(note.group_id) if note.group_id else None

    # Allow deletion if user owns the note or is the creator of the hosting pool
    if (pool and current_user.user_id == pool.created_by) or current_user.user_id == note.user_id:
        delete_note_file(note.file_path)
        db.session.delete(note)
        db.session.commit()
        flash('Note deleted successfully.', 'success')
    else:
        return {'error': 'You are not authorized to delete this document'}, 403

    return redirect(request.referrer or url_for('my_notes'))


@app.route("/create_pool", methods=['POST', 'GET'])
@login_required
def create_pool():
    form = CreatePoolForm()
    if form.validate_on_submit():
        pool = StudyGroup(group_name=form.group_name.data, created_by=current_user.user_id, is_private=form.is_private.data)
        if pool.is_private:
            pool.invite_code = secrets.token_urlsafe(6)
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
    note_urls = {note.notes_id: get_note_file(note.file_path) for note in notes}

    chat_messages = Message.get_pool_messages(pool_id)

    my_pools = StudyGroup.query.join(GroupMembership, StudyGroup.group_id == GroupMembership.group_id) \
        .filter(GroupMembership.user_id == current_user.user_id).all()

    return render_template(
        'pool_space.html',
        title=pool.group_name,
        pool=pool,
        members=members,
        notes=notes,
        note_urls=note_urls,
        chat_messages=chat_messages,
        my_pools=my_pools,
        pusher_key=os.getenv('PUSHER_KEY'),
        pusher_cluster=os.getenv('PUSHER_CLUSTER')
    )


@app.route("/join_pool")
@login_required
def join_pool():
    form = JoinPoolForm()
    pools = db.session.query(StudyGroup, User.username).join(User, StudyGroup.created_by == User.user_id).all()
    my_membership_ids = {m.group_id for m in GroupMembership.query.filter_by(user_id=current_user.user_id).all()}
    return render_template('join_pool.html', title='Join a Pool', pools=pools, my_membership_ids=my_membership_ids, form=form)


@app.route("/join_pool/<int:pool_id>/join", methods=['POST'])
@login_required
def join_pool_action(pool_id):
    form = JoinPoolForm()
    pool = StudyGroup.query.get_or_404(pool_id)
    existing = GroupMembership.query.filter_by(group_id=pool_id, user_id=current_user.user_id).first()

    if existing:
        return redirect(url_for('pool_space', pool_id=pool_id))

    if pool.is_private:
        if not form.validate_on_submit() or form.code.data != pool.invite_code:
            flash('Invalid or missing invite code for this private pool.', 'error')
            return redirect(url_for('join_pool'))

    membership = GroupMembership(group_id=pool_id, user_id=current_user.user_id)
    db.session.add(membership)
    db.session.commit()
    flash(f'Joined "{pool.group_name}"!', 'success')
    return redirect(url_for('pool_space', pool_id=pool_id))


@app.route("/pool_space/<int:pool_id>/message", methods=['POST'])
@login_required
def send_message(pool_id):
    membership = GroupMembership.query.filter_by(group_id=pool_id, user_id=current_user.user_id).first()
    if not membership:
        return {'error': 'You are not a member of this pool'}, 403

    text = request.form.get('text', '').strip()
    if not text:
        return {'error': 'Empty message'}, 400

    if len(text) > 1000:
        return {'error': 'Message too long'}, 400

    message = Message.create_message(pool_id, current_user.user_id, text)

    pusher_client.trigger(f'pool-{pool_id}', 'new-message', {
        'username': current_user.username,
        'text': message.text,
        'time_sent': message.time_sent.strftime('%I:%M %p')
    })

    return {'success': True}, 200


@app.route("/api/summarize", methods=['POST'])
def summarize():
    #update to summarize the recently uploaded note(faster summaries instead of summarizing every)
    if not current_user.is_authenticated:
        return jsonify({'error': 'User not logged in'}), 401

    data = request.get_json(silent=True) or {}
    group_id = data.get('group_id')

    if group_id and str(group_id) != "0":
        notes = Notes.query.filter_by(group_id=group_id).order_by(Notes.time_uploaded.desc()).first()
    else:
        notes = Notes.query.filter_by(user_id=current_user.user_id, group_id=None).order_by(Notes.time_uploaded.desc()).first()

    if not notes:
        return jsonify({'success': False, 'error': 'No notes found to summarize'}), 400
    
    #checks for any existing entries already adds them to an array and returns instead of generating another api call
    existing_entries = []
    existing = Notes_Summary.query.filter_by(from_notes_id=notes.notes_id).first()
    if existing:
        existing_entries.append({"note_name":existing.note_name, "summary":existing.summary_text})
        return jsonify({"success": True, "summary": existing_entries}), 200
    

    summaries = []
    #for note in notes:
    result = generate_summary(notes)
    if not result.get('success'):
        return jsonify({"success": False, 'error': result.get('error', 'Could not generate summary')}), 500
    summaries.append({"note_name": notes.note_name, "summary": result['summary']})
    summary_note = Notes_Summary(from_notes_id=notes.notes_id,from_user_id=current_user.user_id,note_name=notes.note_name,summary_text=result['summary'],group_id=notes.group_id)
    db.session.add(summary_note)
    db.session.commit()

    return jsonify({"success": True, "summary": summaries}), 200




@app.route("/recommendations")
@login_required
def recommendations_page():
    return render_template('recommendations.html', title='Source Search')


@app.route("/api/recommendations", methods=['POST'])
def recommendations():
    if not current_user.is_authenticated:
        return jsonify({'success': False, 'error': 'User not logged in'}), 401

    data = request.get_json(silent=True) or {}
    group_id = data.get('group_id')

    if group_id and str(group_id) != "0":
        notes = Notes.query.filter_by(group_id=group_id).all()
    else:
        notes = Notes.query.filter_by(user_id=current_user.user_id, group_id=None).all()

    if not notes:
        return jsonify({
            "success": False,
            "error": "No notes found to generate recommendations. Please upload a document first."
        }), 400

    note_names = [note.note_name for note in notes if note.note_name]
    query = " ".join(note_names)

    if not query.strip():
        query = "textbook study guide"

    rec_results = search_books(query)

    if not rec_results.get("success"):
        return jsonify({
            "success": False,
            "error": rec_results.get("error", "Could not retrieve book recommendations.")
        }), 400

    return jsonify({
        "success": True,
        "recommendations": rec_results['books']
    }), 200


@app.route("/api/generate_quiz", methods=['POST'])
def generate_quiz():
    if not current_user.is_authenticated:
        return jsonify({'error': 'User not logged in'}), 401

    data = request.get_json(silent=True) or {}
    group_id = data.get('group_id')

    if group_id and str(group_id) != "0":
        notes = Notes.query.filter_by(group_id=group_id).all()
    else:
        notes = Notes.query.filter_by(user_id=current_user.user_id, group_id=None).all()

    if not notes:
        return jsonify({"success": False, "error": "No notes found to generate quiz"}), 400

    summaries_text = ""

    for note in notes:
        result = generate_summary(note)
        if result.get('success'):
            summaries_text += f"\nDocument Name ({note.note_name}):\n{result['summary']}\n"

    if not summaries_text.strip():
        return jsonify({"success": False, "error": "Could not generate summary for quiz"}), 400

    quiz_result = generate_quiz_from_summary(summaries_text)

    if not quiz_result.get('success'):
        return jsonify({"success": False, "error": quiz_result.get('error')}), 500

    raw_data = quiz_result.get("quiz_data", {})
    quiz_questions = raw_data.get("quiz", [])

    return jsonify({"success": True, "quiz": quiz_questions}), 200


@app.route("/pool/<int:pool_id>/quiz")
def pool_quiz(pool_id):
    if not current_user.is_authenticated:
        return redirect(url_for('login'))

    my_pools = StudyGroup.query.join(GroupMembership, StudyGroup.group_id == GroupMembership.group_id) \
        .filter(GroupMembership.user_id == current_user.user_id).all()

    if pool_id == 0:
        pool = {
            "group_id": 0,
            "group_name": "Personal Notes"
        }
        return render_template('quiz.html', pool=pool, my_pools=my_pools)

    pool = StudyGroup.query.get_or_404(pool_id)
    return render_template('quiz.html', pool=pool, my_pools=my_pools)


@app.route("/update_server", methods=['POST'])
def webhook():
    if request.method == 'POST':
        repo = git.Repo('/home/seoproject2/SEOWeek4Project')
        origin = repo.remotes.origin
        origin.pull()
        venv_pip = '/home/seoproject2/.virtualenvs/studypool-venv/bin/pip'
        result = subprocess.run([venv_pip, 'install', '-r', 'requirements.txt'], cwd='/home/seoproject2/SEOWeek4Project')
        if result.returncode != 0:
            return 'pip install failed', 500
        os.utime('/var/www/seoproject2_pythonanywhere_com_wsgi.py', None)
        return 'Updated PythonAnywhere successfully', 200
    else:
        return 'Wrong event type', 400


if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=8080)