from flask import Blueprint, redirect, request, jsonify, url_for
from app import auth
from . import session
from datasources.database import Database

main = Blueprint('main', __name__)

db = Database()

@main.route('/')
def index():
    return "index.html", 200

@main.route('/order')
def order_page():
    return "Order", 200

@main.route('/create_user') #WARNING NERVER RUN THIS
def create_user():
    db.create_user("user1", "squizz")
    return "ok", 200

@main.route('/retrieveproduct', methods=['GET'])
def retrieve_product():
    if not auth.validate_login_session():
        return redirect(url_for('auth.login'))
    connection = auth.build_connection()
    data_type = 3
    jsonResponse, jsonValues = connection.get_product_list(data_type)
    if jsonResponse:
        result = db.store_product(jsonValues)
        return jsonify(result)
    else:
        result = {'status': "error", 'data': 'null', 'Message': "Error while retrieving product from server"}
        return jsonify(result)

@main.route('/retrieveprice', methods=['GET'])
def retrieve_product_price():
    if not auth.validate_login_session():
        return redirect(url_for('auth.login'))
    connection = auth.build_connection()
    data_type = 37
    jsonResponse, jsonValues = connection.get_product_list(data_type)
    
    if jsonResponse:
        result = db.store_product_price(jsonValues)
        return jsonify(result)
    else:
        result = {'status': "error", 'data': 'null', 'Message': "Error while retrieving product price from server"}
        return jsonify(result)

@main.route('/api/price', methods=['POST'])
def get_barcode_product():
    if not auth.validate_login_session():
        return redirect(url_for('auth.login'))

    data = request.get_json(silent=True)
    barcode = data.get('barcode')
    result = db.get_barcode_value(barcode)
    return jsonify(result)

@main.route('/updateproduct', methods=['GET'])
def update_product():
    if not auth.validate_login_session():
        return redirect(url_for('auth.login'))
    connection = auth.build_connection()
    data_type = 3
    json_response, json_values = connection.get_product_list(data_type)
    
    if json_response:
        result = db.update_product(json_values)
        return jsonify(result)
    else:
        result = {'status': "error", 'data': 'null', 'Message': "Error while retrieving product from server"}
        return jsonify(result)

@main.route('/updateprice', methods=['GET'])
def update_product_price():
    if not auth.validate_login_session():
        return redirect(url_for('auth.login'))
    connection = auth.build_connection()
    data_type = 37
    json_response, json_values = connection.get_product_list(data_type)
    if json_response:
        result = db.update_product_price(json_values)
        return jsonify(result)
    else:
        result = {'status': "error", 'data': 'null', 'Message': "Error while retrieving product price from SQUIZZ server"}
        return jsonify(result)

@main.route('/api/purchase', methods=['post'])
def submit_purchase_order():
    if not auth.validate_login_session:
        return redirect(url_for('auth.login'))
    connection = auth.build_connection()
    data = request.get_json(silent=True)
    squizzRep, purchaseList = connection.submit_purchase(data)
    if squizzRep == 'SERVER_SUCCESS':
        result = db.purchase(data["sessionKey"], squizzRep, purchaseList)
        return jsonify(result)
    else:
        result = {'status': "error", 'data': 'null', 'Message': "Error while sending purchase to SQUIZZ server"}
        return jsonify(result)


@main.route('/api/history_order', methods=['post'])
def search_history_order():
    if not auth.validate_login_session:
        return redirect(url_for('auth.login'))
    connection = auth.build_connection()
    data = request.get_json(silent=True)
    try:
        result = db.history_order(data['session_id'], data['date_time'])
    except Exception as e:
        result = {'status': "failure", 'data': 'null', 'Message': "Wrong Session, please login again"}
        return jsonify(result)
    return jsonify(result)