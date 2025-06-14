from flask import Flask, render_template, request, redirect, url_for, flash
from flask_mysqldb import MySQL
from werkzeug.security import generate_password_hash, check_password_hash
from flask import session

app = Flask(__name__)
app.secret_key = 'Ronit@2004' 
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'ronit@2004'
app.config['MYSQL_DB'] = 'airbnb'

mysql = MySQL(app)

@app.route('/')
def index():
    name = session.get('name') 
    role=session.get('role')
    return render_template('index.html', name=name,role=role)
@app.route('/login')
def login_signup():
    return render_template('login_signup.html')
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        if not email or not password:
            flash('Please enter both email and password.', 'danger')
            return redirect(url_for('login'))

        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM users WHERE email = %s", (email,))
        user = cur.fetchone()
        cur.close()

        if user:
            stored_password_hash = user[2]  # Table: id=0, email=1, password_hash=2
            if check_password_hash(stored_password_hash, password):
                session['name'] = user[4]
                session['email'] = user[1]
                session['role'] = user[3]
                flash('Login successful!', 'success')
                return redirect(url_for('index'))
            else:
                flash('Incorrect password!', 'danger')
                return redirect(url_for('login'))
        else:
            flash('Email not registered. Please signup first.', 'warning')
            return redirect(url_for('login'))

    return render_template('login.html')
@app.route('/signup', methods=['POST'])
def signup():
    name=request.form.get('name')
    email = request.form.get('email')
    password = request.form.get('password')
    role = request.form.get('role')  
    if not email or not password or not role:
        flash('Please fill all fields.', 'danger')
        return redirect(url_for('login_signup'))

    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM users WHERE email = %s", (email,))
    existing_user = cur.fetchone()

    if existing_user:
        flash('Email already registered. Please login.', 'danger')
        cur.close()
        return redirect(url_for('login_signup'))


    password_hash = generate_password_hash(password)
    cur.execute(
    "INSERT INTO users (name, email, password_hash, role) VALUES (%s, %s, %s, %s)",
    (name, email, password_hash, role)
)
    mysql.connection.commit()
    cur.close()

    flash('Signup successful! Please login.', 'success')
    return redirect(url_for('login_signup'))
@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))

@app.route('/my_bookings')
def my_bookings():
    if 'email' not in session:
        return redirect(url_for('login'))

    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM bookings WHERE user_email = %s", (session['email'],))
    bookings = cur.fetchall()
    cur.close()

    # Example data mapping (adjust if needed)
    formatted_bookings = []
    for b in bookings:
        formatted_bookings.append({
            'villa_name': b[1],
            'location': b[2],
            'checkin_date': b[3],
            'checkout_date': b[4],
            'price': b[5]
        })

    return render_template("my_booking.html", name=session['name'], bookings=formatted_bookings)


@app.route('/dashboard')
def dashboard():
    if 'email' not in session or session['role'] != 'owner':
        return redirect(url_for('index'))

    owner_email = session['email']
    cur = mysql.connection.cursor()

    # Show only bookings for villas owned by this owner
    cur.execute("""
        SELECT b.villa_name, b.user_email, b.checkin_date, b.checkout_date, b.price
        FROM bookings b
        JOIN villas v ON b.villa_name = v.name
        WHERE v.owner_email = %s
    """, (owner_email,))
    
    bookings = cur.fetchall()
    cur.close()

    return render_template("dashboard.html", name=session['name'], bookings=bookings)

@app.route('/villas_list', methods=['GET', 'POST'])
def villas_list():
    if request.method == 'POST':
        location = request.form['location']
        checkin = request.form['checkin']
        checkout = request.form['checkout']

        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM villas WHERE location LIKE %s", ("%" + location + "%",))
        villas = cur.fetchall()
        cur.close()

        return render_template('villas_list.html',
                               location=location,
                               checkin=checkin,
                               checkout=checkout,
                               villas=villas)
    return redirect(url_for('index'))

@app.route('/villa/<int:villa_id>')
def villa_details(villa_id):
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM villas WHERE id = %s", (villa_id,))
    villa = cur.fetchone()
    cur.close()
    return render_template('villa_details.html', villa=villa)

@app.route('/add_villa', methods=['GET', 'POST'])
def add_villa():
    if 'email' not in session or session['role'] != 'owner':
        return redirect(url_for('login'))

    if request.method == 'POST':
        name = request.form['name']
        location = request.form['location']
        price = request.form['price']
        description = request.form['description']
        image_url = request.form['image_url']
        owner_email = session['email']

        cur = mysql.connection.cursor()
        cur.execute("""
            INSERT INTO villas (name, location, price, description, image_url, owner_email)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (name, location, price, description, image_url, owner_email))
        mysql.connection.commit()
        cur.close()

        flash("Villa added successfully!", "success")
        return redirect(url_for('dashboard'))

    return render_template("add_villa.html")


if __name__ == '__main__':
    app.run(debug=True)
