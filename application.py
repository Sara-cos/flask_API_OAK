from flask import Flask
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from aws import emp_dictionary_fetch
import logging
import time
import blobconverter
import boto3
import cv2
import io
import depthai as dai
import numpy as np
from datetime import date, datetime

AWSAccessKeyId = 'AKIAZTBLXFPX3NJHL73W'
AWSSecretKey = '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'


ddb_client = boto3.client(
    'dynamodb',
    region_name='ap-south-1',
    aws_access_key_id = AWSAccessKeyId,
    aws_secret_access_key = AWSSecretKey,
)

ddb_resource = boto3.resource(
    'dynamodb',
    region_name ='ap-south-1',
    aws_access_key_id = AWSAccessKeyId,
    aws_secret_access_key = AWSSecretKey,
)

s3_client = boto3.client(
    's3',
    region_name='ap-south-1',
    aws_access_key_id = AWSAccessKeyId,
    aws_secret_access_key = AWSSecretKey,
)

s3_resource = boto3.resource(
    's3',
    region_name = 'ap-south-1',
    aws_access_key_id = AWSAccessKeyId,
    aws_secret_access_key = AWSSecretKey,
)


TABLE_NAME = "face_recog_db"
EMP_TABLE = "emp_db"

table_emp = ddb_resource.Table(EMP_TABLE)
table = ddb_resource.Table(TABLE_NAME)

s3_bucket = s3_resource.Bucket(name="divineai-npzfiles")


##### Fetching dynammo db details

dates_dict = {}
id_dict = {}
raw_dict = {}
dict_ = {}


def emp_dictionary_fetch() -> dict:
    """
    Sends a dict with date as the keys
    """

    response = table.scan()
    items_list = response['Items']

    for i in range(len(items_list)):
        date = items_list[i]["DATE_KEY"]
        id = items_list[i]["ID_KEY"]

        if date in dates_dict:
            dates_dict[date][items_list[i]["ID_KEY"]] = items_list[i]
        else:
            dates_dict[date] = {}
            dates_dict[date][items_list[i]["ID_KEY"]] = items_list[i]

        if id in id_dict:
            id_dict[id][date] = items_list[i]
        else:
            id_dict[id] = {}
            id_dict[id][date] = items_list[i]


    dict_["ID"] = id_dict
    dict_["DATE"] = dates_dict
    dict_["DATA"] = items_list

    return dict_
    
#####

application = app = Flask(__name__)
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


@app.route('/raw_data/', methods=['GET','POST'])
def raw_data():
    if request.method == 'GET':
        emp_dict = emp_dictionary_fetch()
        emp_dict = emp_dict["DATA"]
        return jsonify(emp_dict)
        

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
    application.run(debug=True)
