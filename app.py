from flask import Flask, render_template, redirect, url_for

app=Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/signup')
def signup():
    return render_template('signup.html')

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/ride_request') 
def ride_request(): 
    return render_template('ride_request.html')

if __name__=='__main__':
    app.run(debug=True)

#Mlungisi