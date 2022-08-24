from flask import Flask
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from aws import *
import time
import blobconverter
import boto3
import cv2
import io
import depthai as dai
import numpy as np
from datetime import date, datetime

app = Flask(__name__)
cors = CORS(app)

@app.route('/')
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

@app.errorhandler(404)
def error_404(e):
    return render_template("pages-misc-error.html"), 404

app.register_error_handler(404, error_404)  

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


@app.route('/connect_oak/', methods=['POST'])
def connect_oak():
    if request.method == 'POST':
        try:
            file = open(r'oak_files/main.py', 'r').read()
            exec(file)
        except:
            return render_template("pages-misc-error.html")

        return render_template("index.html")

      

if '__name__' == '__main__':
    app.run(debug=True)
