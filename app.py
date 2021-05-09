from flask import Flask, render_template, request, redirect, url_for, session
from flask_mysqldb import MySQL
import MySQLdb.cursors
import re
#from sendemail import sendmail,sendgridmail
import smtplib
from chatterbot import ChatBot
from chatterbot.trainers import ChatterBotCorpusTrainer


app = Flask(__name__)

english_bot = ChatBot("Chatterbot", storage_adapter="chatterbot.storage.SQLStorageAdapter")
trainer = ChatterBotCorpusTrainer(english_bot)
trainer.train("chatterbot.corpus.english")


app.secret_key = 'a'

app.config['MYSQL_HOST'] = 'remotemysql.com'
app.config['MYSQL_USER'] = 'GTAZsgxG6i'
app.config['MYSQL_PASSWORD'] = 'KTj9UYcstK'
app.config['MYSQL_DB'] = 'GTAZsgxG6i'
mysql = MySQL(app)

@app.route("/chatbot")
def chatbot():
    return render_template("chatbot.html")

@app.route("/get")
def get_bot_response():
    userText = request.args.get('msg')
    return str(english_bot.get_response(userText))


@app.route("/")
def home():
    cursor = mysql.connection.cursor()
    cursor.execute('select title, count(*) as no_of_jobs from jobs group by title')
    Type_of_Jobs = cursor.fetchall()
    print("Type of Jobs = ",Type_of_Jobs)
    return render_template('index.html',Type_of_Jobs = Type_of_Jobs)

@app.route('/register', methods =['GET', 'POST'])
def register():
    msg = ''
    if request.method == 'POST' :
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        

        cursor = mysql.connection.cursor()
        cursor.execute('SELECT * FROM UserDetail WHERE username = % s', (username, ))
        account = cursor.fetchone()
        print(account)
        if account:
            msg = 'Account already exists !'
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            msg = 'Invalid email address !'
        elif not re.match(r'[A-Za-z0-9]+', username):
            msg = 'name must contain only characters and numbers !'
        else:
            cursor.execute('INSERT INTO UserDetail(user_id, UserName, emailid, Password )VALUES (NULL, % s, % s, % s)', (username, email,password))
            mysql.connection.commit()
            msg = 'You have successfully registered !'
            TEXT = "Hello "+username + ",\n\n"+ """Thanks for applying registring at smartinterns """ 
            message  = 'Subject: {}\n\n{}'.format("smartinterns Carrers", TEXT)
            #sendmail(TEXT,email)
            #sendgridmail(email,TEXT)
    elif request.method == 'POST':
        msg = 'Please fill out the form !'
        
    return render_template('register.html', msg = msg)

@app.route('/login',methods =['GET', 'POST'])
def login():
    global userid
    msg = ''
   
  
    if request.method == 'POST' :
        username = request.form['username']
        password = request.form['password']
        cursor = mysql.connection.cursor()
        cursor.execute('SELECT user_id,UserName,emailid FROM UserDetail WHERE UserName = % s AND password = % s', (username, password ),)
        account = cursor.fetchone()
        print (account)
        if account:
            session['loggedin'] = True
            session['id'] = account[0]
            session['username'] = username
            userid=  account[0]
            session['username'] = account[1]
            msg = 'Logged in successfully !'
            
            msg = 'Logged in successfully !'
            return render_template('dashboard.html', msg = msg)
        else:
            msg = 'Incorrect username / password !'
    return render_template('login.html', msg = msg)

@app.route('/job_listing',methods =['GET', 'POST'])
def job_listing():
    cursor = mysql.connection.cursor()
    fields = {}
    for field in request.args:
            if len(request.args.get(field))>0:
                fields[field]=request.args.get(field)
    print(fields)
    title = request.args.get('title')
    if len(fields)>0 and fields['title'] != None and fields['title'] == 'All':
        fields.pop('title')
        
    query = 'select title, jobdesc, basicpay, jobs.location, postdate, job_type, ename, jobid  from jobs inner join employer on jobs.eid = employer.eid '
    if title != None:
        if title != 'All' :
            session['title'] = title
            fields['title']=title
        else:
            session['title'] = title
    elif session.get('title') is not None and session['title'] != None:
        title = session['title']
        if title != 'All' :
            session['title'] = title
            fields['title']=title
        else:
            session['title'] = title
    
    sortQuery = ""
    whereQuery = ""
    values=[]
    for item in fields.items():
        print(item)
        if item[0] == 'sortfield':
            sortQuery = " order by " + sortfield
            if item[1] == 'basicpay':
                sortQuery += " desc"
        else:
            if item[0] == 'location':
                whereQuery += 'jobs.' + item[0] + ' = %s and '
            else:
                whereQuery += item[0] + ' = %s and '
            values.append(item[1])
    
    if len(whereQuery) > 0:
        query += ' where ' + whereQuery[:len(whereQuery)-5]
    if len(sortQuery) > 0 :
        query += sortQuery
    
    print(query)
    print(tuple(values))
    if len(values) > 0:
        cursor.execute(query,tuple(values))
    else:
        cursor.execute(query)
    
    Jobs = cursor.fetchall()

    cursor.execute('select distinct title from jobs')
    category = cursor.fetchall()
    
    cursor.execute('select distinct job_type from jobs')
    job_type = cursor.fetchall()
    
    cursor.execute('select distinct location from jobs')
    location = cursor.fetchall()
    
    cursor.execute('select min(basicpay),max(basicpay) from jobs')
    min_salary, max_salary = cursor.fetchone()
    print(min_salary,max_salary)
    return render_template('job_listing.html',Jobs = Jobs, no_of_jobs = len(Jobs), category = category,job_type = job_type, location = location,min_salary=min_salary,max_salary=max_salary)

@app.route('/logout')    
def logout():
   session.pop('loggedin', None)
   session.pop('id', None)
   session.pop('username', None)
   return render_template('index.html')
   
@app.route('/dashboard')
def dash():
    cursor = mysql.connection.cursor()

    user_id = session['id']
    print(user_id)
    cursor.execute('select * from JobDetail where user_id = %s',(user_id,))
    Jobs = cursor.fetchall()

    return render_template('dashboard.html',Jobs = Jobs) 

@app.route('/about')
def about():
    return render_template('about.html') 

@app.route('/job_details')
def job_details():
    return render_template('job_details.html') 

@app.route('/contact')
def contact():
    return render_template('contact.html') 


@app.route('/apply',methods =['GET', 'POST'])
def apply():
     msg = ''
     if request.method == 'POST' :
         username = request.form['username']
         email = request.form['email']
         
         qualification= request.form['qualification']
         skills = request.form['skills']
         jobs = request.form['s']
         cursor = mysql.connection.cursor()
         print("user id = " ,session['id'])
         cursor.execute('SELECT * FROM JobDetail WHERE user_id = % s', (session['id'], ))
         account = cursor.fetchone()
         print(account)
         if account:
            msg = 'there is only 1 job position! for you'
            return render_template('apply.html', msg = msg)

         
         
         
         cursor = mysql.connection.cursor()
         cursor.execute('INSERT INTO JobDetail(user_id,UserName, email,qualification,skills,jobs) VALUES (% s, % s, % s, % s,% s, % s)', (session['id'],username, email,qualification,skills,jobs))
         mysql.connection.commit()
         msg = 'You have successfully applied for job !'
         session['loggedin'] = True
         TEXT = "Hello " + username +",a new appliaction for job position" +jobs+"is requested"
         
         #sendmail(TEXT,"sandeep@thesmartbridge.com")
         #sendgridmail(email,TEXT)
         
         
         
     elif request.method == 'POST':
         msg = 'Please fill out the form !'
     return render_template('apply.html', msg = msg)
     
if __name__ == "__main__":
  app.run(host='0.0.0.0',port=5000,debug=True)