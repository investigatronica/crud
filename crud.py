from flask import Flask, render_template, request, redirect, url_for, flash,session
# from flask_mysqldb import MySQL
from flaskext.mysql import MySQL
from flask_session import Session
import os, pymysql
from functools import wraps
from tempfile import mkdtemp
from werkzeug.security import check_password_hash, generate_password_hash
import simplejson as json

# initializations
app = Flask(__name__)

mysql_flask = MySQL(app
            ,prefix="mysql1"
            ,host="172.18.0.1"
            ,user=os.getenv("FLASK_MYSQL_USER")
            ,password=os.getenv("FLASK_MYSQL_PASSWORD")
            ,db=os.getenv("FLASK_MYSQL_DB")
            ,autocommit=True)

mysql_temp = MySQL(app
            ,prefix="mysql1"
            ,host="172.18.0.1"
            ,user=os.getenv("FLASK_MYSQL_USER")
            ,password=os.getenv("FLASK_MYSQL_PASSWORD")
            ,db=os.getenv("FLASK_MYSQL_DB_TEMP")
            ,autocommit=True
            ,cursorclass=pymysql.cursors.DictCursor)

# settings
app.secret_key = os.getenv("FLASK_SECRET_KEY")
# Configure session to use filesystem (instead of signed cookies)
# app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)


# print(app.config)
# routes

def login_required(f):
    """
    Decorate routes to require login.
    https://flask.palletsprojects.com/en/1.1.x/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
@login_required
def index():
    cur = mysql_flask.get_db().cursor()
    cur.execute('SELECT * FROM contacts')
    data = cur.fetchall()
    cur.close()
    return render_template('index.html', contacts = data, activo=True)

@app.route('/add_contact', methods=['POST'])
@login_required
def add_contact():
    if request.method == 'POST':
        fullname = request.form['fullname']
        phone = request.form['phone']
        email = request.form['email']
        cur = mysql_flask.get_db().cursor()
        cur.execute("INSERT INTO contacts (fullname, phone, email) VALUES (%s,%s,%s)", (fullname, phone, email))
        mysql.connection.commit()
        flash('Contact Added successfully')
        return redirect(url_for('index'))

@app.route('/edit/<id>', methods = ['POST', 'GET'])
@login_required
def get_contact(id):
    cur = mysql_flask.get_db().cursor()
    cur.execute('SELECT * FROM contacts WHERE id = %s', (id))
    data = cur.fetchall()
    cur.close()
    print(data[0])
    return render_template('edit-contact.html', contact = data[0], activo=True)

@app.route("/login", methods=["GET", "POST"])
def login():
    """login user"""
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return "must provide username"

        # Ensure password was submitted
        elif not request.form.get("password"):
            return "must provide password"

        cur = mysql_flask.get_db().cursor()
        cur.execute("SELECT * FROM user WHERE username LIKE %s", (request.form.get("username"),))
        rows=cur.fetchone()
        # print(rows)
        if(rows):
            if (check_password_hash('pbkdf2:sha256:10000$' + rows[3],request.form.get("password"))):
                print("ok")
                session["user_id"]=request.form.get("username")
                return redirect(url_for('index'))
            else:
                flash('Bad username or password')
                return redirect(url_for('login'))


    else:
        return render_template('login.html')

@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")

@app.route('/update/<id>', methods=['POST'])
@login_required
def update_contact(id):
    if request.method == 'POST':
        fullname = request.form['fullname']
        phone = request.form['phone']
        email = request.form['email']
        cur = mysql_flask.get_db().cursor()
        cur.execute("""
            UPDATE contacts
            SET fullname = %s,
                email = %s,
                phone = %s
            WHERE id = %s
        """, (fullname, email, phone, id))
        flash('Contact Updated Successfully')
        # mysql.connection.commit()
        return redirect(url_for('index'))

@app.route('/delete/<string:id>', methods = ['POST','GET'])
@login_required
def delete_contact(id):
    cur = mysql_flask.get_db().cursor()
    cur.execute('DELETE FROM contacts WHERE id = {0}'.format(id))
    mysql.connection.commit()
    flash('Contact Removed Successfully')
    return redirect(url_for('index'))

@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return "must provide username"

        # Ensure password was submitted
        elif not request.form.get("password"):
            return "must provide password"

        passhash=generate_password_hash(request.form.get("password"), method='pbkdf2:sha256:10000', salt_length=16)
        cur = mysql_flask.get_db().cursor()
        cur.execute("INSERT INTO user (username, password) VALUES (%s,%s)", (request.form.get("username"), passhash[20:]))
        flash('User Added successfully')
        return redirect(url_for('index'))

    else:
        return render_template('register.html')

@app.route('/temp')
@login_required
def temperatura():
    cur = mysql_temp.get_db().cursor()
    cur.execute('SELECT temp_ext, temp_int, temp_nuevo1 FROM datos ORDER BY id DESC LIMIT 1')
    data = json.dumps(cur.fetchone(), use_decimal=True)
    cur.close()
    # print(data)
    return data


# starting the app
if __name__ == "__main__":
    app.run(port=5000, debug=True,host='0.0.0.0')
