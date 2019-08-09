#!/usr/bin/python3
from flask import Flask, render_template, request, url_for, session, redirect, Response, Blueprint
from flask_mysqldb import MySQL
import MySQLdb.cursors
import mysql.connector as MYSQL
import time
import datetime
from tabulate import tabulate
from flask_socketio import SocketIO, emit


mo = time.strftime('%Y-%m') # Time for monthly price calc
mof = (mo + "%") # Time for monthly price calc formatted
dat = datetime.datetime.now()

app = Flask(__name__) #For user db
bcdb = Flask(__name__) #For barcode db
socketio = SocketIO(app) #For socketio

# MySQL connection details
app.secret_key = 'supersecretkey123'
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'admin'
app.config['MYSQL_PASSWORD'] = 'sqlpass'
app.config['MYSQL_DB'] = 'BC_USERS_DB'
# Init MySQL
mysql = MySQL(app)


@app.route('/login', methods=['GET', 'POST'])
def login(): 
    
    msg = ''
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        username = request.form['username']
        password = request.form['password']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM accounts WHERE username = %s AND password = %s', (username, password))
        account = cursor.fetchone()
        if account:
            session['loggedin'] = True
            session['id'] = account['id']
            session['username'] = account['username']
            return redirect(url_for('home'))
        else:
            msg= 'Incorrect username/password'
    return render_template('index.html', msg=msg)

#Logout function
@app.route('/logout')
def logout():
    session.pop('loggedin', None)
    session.pop('id', None)
    session.pop('username', None)
    return redirect(url_for('login'))

#Connection socket
@socketio.on('connect', namespace='/home')
def sock_connect():
    print("User Connected")
    
    
@socketio.on('form_submit', namespace='/home')
def item_submit(message):
    print(message)
    
    
#Disconnection socket  
@socketio.on('disconnect', namespace='/home')
def sock_disconnect():
    print("User Disconnected")

@app.route('/home', methods=['POST', 'GET'])
def home():
    if 'loggedin' in session: 
        
        #bclog = open('barcode.log', 'r')
        #bcode = bclog.read()
        
        #bc_db connection
        bcdb = MySQLdb.connect(
            host='localhost',
            database='bc_db',
            user='admin',
            password='sqlpass'
        )
        bcursor = bcdb.cursor()

        #Total DB items
        bcursor.execute("SELECT Price FROM bc_store")
        dbquery = bcursor.fetchall()
        totalP = 0
        for row in dbquery:
            totalP += row[0]
        db_price = str(totalP)
        db_items = len(dbquery) #Total items in DB


        #Monthly expense
        bcursor.execute("SELECT Price FROM bc_hist WHERE Date LIKE %s", (mof,))
        monthquery = bcursor.fetchall()
        month_items = len(monthquery)
        mprice = 0
        for row in monthquery:
            mprice += row[0]
        month_price = str(mprice)

        #Get barcode from scanner
        if request.method == 'POST':
            
            #Post from scanner
            if 'Bcode' in request.form:
                data = request.form['Bcode']
                print(data)
                print("Stuff happened")

                #Query DB for barcode
                bc = data
                bcursor.execute("SELECT * FROM bc_store WHERE Barcode=%s LIMIT 1", (bc,))
                result = bcursor.fetchall()

                #If barcode not in DB  
                if not result:
                    print("Not here")
                    socketio.emit('bcode_it', {'bcode': data}, namespace='/home')

                #If item exists in table
                else:
                    bc_result = []
                    for row in result:
                        bc_result.append(row)
                        #print(row)                
                        print("In table")
                        socketio.emit('bcode_nit', {'bcode': str(bc_result)}, namespace='/home')

            #Post for product
            if 'pname' in request.form and 'ptype' in request.form and 'pprice' in request.form:
                Pname = request.form['pname']
                Ptype = request.form['ptype']
                Price = request.form['pprice']

                print(Pname, Ptype, Price)  
        
        return render_template(
            'home.html', 
            db_items=db_items, 
            month_items=month_items,
            db_price=db_price,
            month_price=month_price
        )   

    else:
        return redirect(url_for('login'))

@app.route('/home/database')
def database():
    if 'loggedin' in session: 
        bcdb = MySQLdb.connect(
            host='localhost',
            database='bc_db',
            user='admin',
            password='sqlpass'
        )
        bcursor = bcdb.cursor()

        bcursor.execute("SELECT * FROM bc_store")
        query = bcursor.fetchall()
        
        db_full = (tabulate(query, headers=['id', 'Barcode', 'ProductName', 'ProductType', 'Price'], tablefmt='psql'))
        return render_template('database.html', db_full=db_full) 


@app.route('/')
def root():
    if 'loggedin' in session:
        return redirect('home')
    else:
        return redirect(url_for('login'))

if __name__ == "__main__":
    socketio.run(app, debug=True, host='0.0.0.0')