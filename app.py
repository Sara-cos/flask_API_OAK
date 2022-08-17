from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from aws import *

app = Flask(__name__)
cors = CORS(app)

@app.route('/index/')
def index():
    return render_template("index.html")

@app.route('/tables/')
def tables():
    return render_template("tables-basic.html")

@app.route('/account/')
def account():
    return render_template("pages-account-settings-account.html")

@app.route('/login/')
def auth_login():
    return render_template("auth-login-basic.html")

@app.route('/register/')
def auth_register():
    return render_template("auth-register-basic.html")

@app.route('/forgot_password/')
def auth_forgot_password():
    return render_template("auth-forgot-password-basic.html")

@app.route('/error_404/')
def error_404():
    return render_template("pages-misc-error.html")

@app.route('/misc_error/')
def misc_error():
    return render_template("pages-misc-under-maintenance.html")



@app.route('/date_data/',methods=['GET','POST'])
def date_data():
    if request.method == 'GET':  
        emp_dict = emp_dictionary_fetch()
        emp_dict = emp_dict["DATE"]
        return jsonify(emp_dict)

@app.route('/id_data/',methods=['GET','POST'])
def id_data():
    if request.method == 'GET':  
        emp_dict = emp_dictionary_fetch()
        emp_dict = emp_dict["ID"]
        return jsonify(emp_dict)
        

if '__name__' == '__main__':
    app.run(debug=True)