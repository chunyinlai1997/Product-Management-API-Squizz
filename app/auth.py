import os
import logging
from flask import Flask, Blueprint, request, jsonify
#from datetime import datetime
from . import session
from . import create_app
from datasources.iam import IAM
from datasources.database import Database
import app.main as main

logger = logging.getLogger(__name__)

base_url = os.environ.get('BASE_URL')

auth = Blueprint('auth', __name__)

db = Database()

def build_connection():
    #check with db, retrive api_org_key and api_org_pw
    org_id = session.get('org_id')
    api_org_key, api_org_pw = db.retrieve_api_key_pw(org_id)
    return IAM(base_url, org_id, api_org_key, api_org_pw)

def validate_login_session():
    login_session = session.get('login_session')
    org_id = session.get('org_id')

    if db.validate_session(login_session, org_id):
        return True
    else:
        return False

@auth.route('/login')
def login():
    if validate_login_session():
        return main.index()
    return "login page here", 200

@auth.route('/api/login', methods=['POST'])
def login_post():
    if validate_login_session():
        result = {'status': "success", 'data': {"session_id": session.get('login_session')}, "message": "LOGIN_EXIST"}
        return jsonify(result)

    data = request.get_json(silent=True)
    username = data.get('username')
    password = data.get('password')

    try:
        org_id = db.validate_username_password(username, password)
    except AttributeError:
        result = {'status': "failure", 'data': {"session_id": None}, "message": "LOGIN_WRONG"}
        return jsonify(result)

    if org_id is None:
        #wrong username or password
        result = {'status': "failure", 'data': {"session_id": None}, "message": "LOGIN_WRONG"}
        return jsonify(result)
    
    session['org_id'] = org_id
    connection = build_connection()
    session_id, status_code = connection.create_session()
    if status_code == "LOGIN_SUCCESS":
        session.permanent = True
        session['seesion_id'] = session_id
        session['login_session'] = session_id
        db.store_session(session_id, org_id)
        logger.info("You have create a new login session, session id:" + session_id)
        result = {'status': "success", 'data': {"session_id": session_id}, "message": "LOGIN_SUCCESS"}
        return jsonify(result)
    else:
        result = {'status': "failure", 'data': {"session_id": None}, "message": status_code}
        return jsonify(result) 

@auth.route('/api/logout', methods=['GET'])
def logout():
    login_session = session.get('login_session')
    if validate_login_session():
        db.remove_session(login_session)
        session.pop('login_session ', None)
        session.pop('session_id ', None)
        session.pop('org_id', None)
        logger.info("Your session has destroyed")
        result = {'status': "success", "message": "LOGOUT_SUCCESS"}
        return jsonify(result)
    else:
        result = {'status': "failure", "message": "LOGOUT_FAILURE"}
        return jsonify(result)