from flask import (
    Flask,
    render_template,
    request,
    redirect,
    session,
    make_response
)

import sqlite3
import pandas as pd
import joblib

# PDF LIBRARIES
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle
)

from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors


# FLASK APP
app = Flask(__name__)

app.secret_key = "smartenergysecret"


# LOAD ML MODEL
model = joblib.load('model.pkl')


# DATABASE CONNECTION
def get_db_connection():

    conn = sqlite3.connect('database.db')

    conn.row_factory = sqlite3.Row

    return conn


# HOME PAGE
@app.route('/')
def home():

    return render_template('index.html')


# SIGNUP
@app.route('/signup', methods=['GET', 'POST'])
def signup():

    if request.method == 'POST':

        username = request.form['username']

        email = request.form['email']

        password = request.form['password']

        conn = get_db_connection()

        conn.execute(
            '''
            INSERT INTO users
            (username, email, password)

            VALUES (?, ?, ?)
            ''',
            (username, email, password)
        )

        conn.commit()

        conn.close()

        return redirect('/login')

    return render_template('signup.html')


# LOGIN
@app.route('/login', methods=['GET', 'POST'])
def login():

    if request.method == 'POST':

        email = request.form['email']

        password = request.form['password']

        conn = get_db_connection()

        user = conn.execute(
            '''
            SELECT * FROM users
            WHERE email=? AND password=?
            ''',
            (email, password)
        ).fetchone()

        conn.close()

        if user:

            session['user_id'] = user['id']

            session['username'] = user['username']

            return redirect('/dashboard')

        else:

            return "Invalid Credentials"

    return render_template('login.html')


# DASHBOARD
@app.route('/dashboard')
def dashboard():

    if 'user_id' not in session:
        return redirect('/login')

    conn = get_db_connection()

    appliances = conn.execute(
        '''
        SELECT * FROM appliances
        WHERE user_id=?
        ''',
        (session['user_id'],)
    ).fetchall()

    conn.close()

    # TOTAL APPLIANCES
    total_appliances = len(appliances)

    # TOTAL UNITS
    total_units = sum(
        appliance['units']
        for appliance in appliances
    )

    # TOTAL BILL
    total_bill = sum(
        appliance['bill']
        for appliance in appliances
    )

    # CHART DATA
    appliance_names = [
        appliance['appliance_name']
        for appliance in appliances
    ]

    appliance_units = [
        appliance['units']
        for appliance in appliances
    ]

    # SMART RECOMMENDATIONS
    recommendations = []

    for appliance in appliances:

        # VERY HIGH USAGE
        if appliance['units'] > 10:

            recommendations.append(
                f"{appliance['appliance_name']} is consuming very high electricity."
            )

        # MODERATE USAGE
        elif appliance['units'] > 5:

            recommendations.append(
                f"Consider reducing usage time for {appliance['appliance_name']}."
            )

        # AC RECOMMENDATION
        if appliance['appliance_name'].lower() == 'ac':

            recommendations.append(
                "Use AC at 24°C for better energy efficiency."
            )

        # WASHING MACHINE RECOMMENDATION
        if appliance['appliance_name'].lower() == 'washing machine':

            recommendations.append(
                "Run washing machine during low tariff hours."
            )

    return render_template(

        'dashboard.html',

        username=session['username'],

        total_appliances=total_appliances,

        total_units=round(total_units, 2),

        total_bill=round(total_bill, 2),

        appliance_names=appliance_names,

        appliance_units=appliance_units,

        recommendations=recommendations
    )


# ADD APPLIANCE
@app.route('/add_appliance', methods=['GET', 'POST'])
def add_appliance():

    if 'user_id' not in session:
        return redirect('/login')

    if request.method == 'POST':

        appliance_name = request.form['appliance_name']

        power = float(request.form['power'])

        hours = float(request.form['hours'])

        # CALCULATE UNITS
        units = (power * hours) / 1000

        # ML INPUT
        input_data = pd.DataFrame(
            [[power, hours]],
            columns=['Power', 'Hours']
        )

        # PREDICT BILL
        prediction = model.predict(input_data)

        bill = round(prediction[0], 2)

        # SAVE TO DATABASE
        conn = get_db_connection()

        conn.execute(
            '''
            INSERT INTO appliances
            (
                user_id,
                appliance_name,
                power,
                hours,
                units,
                bill
            )

            VALUES (?, ?, ?, ?, ?, ?)
            ''',
            (
                session['user_id'],
                appliance_name,
                power,
                hours,
                units,
                bill
            )
        )

        conn.commit()

        conn.close()

        return redirect('/history')

    return render_template('add_appliance.html')


# HISTORY
@app.route('/history')
def history():

    if 'user_id' not in session:
        return redirect('/login')

    conn = get_db_connection()

    appliances = conn.execute(
        '''
        SELECT * FROM appliances
        WHERE user_id=?
        ''',
        (session['user_id'],)
    ).fetchall()

    conn.close()

    return render_template(
        'history.html',
        appliances=appliances
    )


# DOWNLOAD PDF REPORT
@app.route('/download_report')
def download_report():

    if 'user_id' not in session:
        return redirect('/login')

    conn = get_db_connection()

    appliances = conn.execute(
        '''
        SELECT * FROM appliances
        WHERE user_id=?
        ''',
        (session['user_id'],)
    ).fetchall()

    conn.close()

    # PDF FILE
    pdf = SimpleDocTemplate("energy_report.pdf")

    styles = getSampleStyleSheet()

    elements = []

    # TITLE
    title = Paragraph(
        "Smart Electricity Consumption Report",
        styles['Title']
    )

    elements.append(title)

    elements.append(Spacer(1, 20))

    # USERNAME
    username = Paragraph(
        f"User: {session['username']}",
        styles['Normal']
    )

    elements.append(username)

    elements.append(Spacer(1, 20))

    # TABLE DATA
    data = [
        ['Appliance', 'Power', 'Hours', 'Units', 'Bill']
    ]

    total_bill = 0

    for appliance in appliances:

        data.append([
            appliance['appliance_name'],
            appliance['power'],
            appliance['hours'],
            round(appliance['units'], 2),
            round(appliance['bill'], 2)
        ])

        total_bill += appliance['bill']

    # TABLE
    table = Table(data)

    table.setStyle(TableStyle([

        ('BACKGROUND', (0,0), (-1,0), colors.grey),

        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),

        ('ALIGN', (0,0), (-1,-1), 'CENTER'),

        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),

        ('BOTTOMPADDING', (0,0), (-1,0), 12),

        ('GRID', (0,0), (-1,-1), 1, colors.black)

    ]))

    elements.append(table)

    elements.append(Spacer(1, 20))

    # TOTAL BILL
    total = Paragraph(
        f"Total Estimated Bill: ₹ {round(total_bill, 2)}",
        styles['Heading2']
    )

    elements.append(total)

    # BUILD PDF
    pdf.build(elements)

    # RESPONSE
    response = make_response(
        open("energy_report.pdf", "rb").read()
    )

    response.headers['Content-Type'] = 'application/pdf'

    response.headers['Content-Disposition'] = \
        'attachment; filename=energy_report.pdf'

    return response

# EDIT APPLIANCE
@app.route('/edit_appliance/<int:id>', methods=['GET', 'POST'])
def edit_appliance(id):

    if 'user_id' not in session:
        return redirect('/login')

    conn = get_db_connection()

    appliance = conn.execute(
        '''
        SELECT * FROM appliances
        WHERE id=?
        ''',
        (id,)
    ).fetchone()

    if request.method == 'POST':

        appliance_name = request.form['appliance_name']

        power = float(request.form['power'])

        hours = float(request.form['hours'])

        units = (power * hours) / 1000

        input_data = pd.DataFrame(
            [[power, hours]],
            columns=['Power', 'Hours']
        )

        prediction = model.predict(input_data)

        bill = round(prediction[0], 2)

        conn.execute(
            '''
            UPDATE appliances

            SET appliance_name=?,
                power=?,
                hours=?,
                units=?,
                bill=?

            WHERE id=?
            ''',
            (
                appliance_name,
                power,
                hours,
                units,
                bill,
                id
            )
        )

        conn.commit()

        conn.close()

        return redirect('/history')

    conn.close()

    return render_template(
        'edit_appliance.html',
        appliance=appliance
    )
# DELETE APPLIANCE
@app.route('/delete_appliance/<int:id>')
def delete_appliance(id):

    # CHECK LOGIN
    if 'user_id' not in session:
        return redirect('/login')

    # DATABASE CONNECTION
    conn = get_db_connection()

    # DELETE RECORD
    conn.execute(
        '''
        DELETE FROM appliances
        WHERE id=?
        ''',
        (id,)
    )

    conn.commit()

    conn.close()

    # REDIRECT BACK
    return redirect('/history')
# LOGOUT
@app.route('/logout')
def logout():

    session.clear()

    return redirect('/')


# RUN APP
if __name__ == '__main__':

    app.run(debug=True)