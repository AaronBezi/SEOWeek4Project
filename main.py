from flask import Flask, render_template, url_for, flash, redirect, request
# url_for allows us to find where this file is in our HTML (main.py) 
from flask_behind_proxy import FlaskBehindProxy
from forms import RegistrationForm
import git
import os
from dotenv import load_env()
load_dotenv()

app = Flask(__name__)                    # this gets the name of the file so Flask knows it's name
proxied = FlaskBehindProxy(app)          # handle codio redirection
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')

@app.route("/")
@app.route("/home")
def home():
    return render_template('home.html', subtitle='Home Page', text='This is the home page')

@app.route("/register", methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit(): # checks if entries are valid
        flash(f'Account created for {form.username.data}!', 'success')
        return redirect(url_for('home')) # if so - send to home page
    return render_template('register.html', title='Register', form=form)

@app.route("/update_server", methods=['POST'])
def webhook():
    if request.method == 'POST':
        repo = git.Repo('/home/seoproject2/SEOWeek4Project')
        origin = repo.remotes.origin
        origin.pull()
        return 'Updated PythonAnywhere successfully', 200
    else:
        return 'Wrong event type', 400
  
if __name__ == '__main__':               # this should always be at the end
    app.run(debug=True, host="0.0.0.0")
