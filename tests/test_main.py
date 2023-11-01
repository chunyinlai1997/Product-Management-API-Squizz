import json
import requests
from app import session
from datetime import datetime

s = requests.Session()
squizz_sessions = []
base_url = "http://127.0.0.1:5000/"

def test_login():
    url = 'api/login'
    headers = {"Content-Type": "application/json"}

    data = {"username": "user1", "password": "123456789"}
    response = s.post(base_url + url, data=json.dumps(data), headers=headers)
    json_response = json.loads(response.text)
    assert json_response['status'] == "failure"

    data = {"username": "user1", "password": "squizz"}
    response = s.post(base_url + url, data=json.dumps(data), headers=headers)
    json_response = json.loads(response.text)
    assert json_response['status'] == "success"
    content = json_response['data']
    squizz_sessions.append(content['session_id'])
    #print(json_response['session_id'])

def test_price():
    url = 'api/price'
    data = {"barcode": "9326243001194"}
    headers = {"Content-Type": "application/json"}
    response = s.post(base_url+url,data=json.dumps(data),headers=headers)
    json_response = json.loads(response.text)
    assert json_response['status'] == "success"

##CANT USE THIS AS IT STORES DATA IN DATABASE
# def test_retrieve_product():
#     base_url = "http://127.0.0.1:5000/"
#     url = 'retrieveproduct'
#     response = s.get(base_url + url)
#     json_response = json.loads(response.text)
#     print(json_response)
#     assert json_response['status'] == "success"

def test_history_order():
    url = 'api/history_order'
    headers = {"Content-Type": "application/json"}
    now = datetime.now()
    date = now.strftime("%Y/%m/%d %H:%M:%S")
    data = {'date_time':date}
    response = s.post(base_url + url, data=json.dumps(data), headers=headers)
    json_response = json.loads(response.text)
    assert json_response['status'] == "failure"

    data = {'session_id': squizz_sessions[0],'date_time':date}
    response = s.post(base_url + url, data=json.dumps(data), headers=headers)
    json_response = json.loads(response.text)
    assert json_response['status'] == "success"

def test_logout():
    url = 'api/logout'
    response = s.get(base_url + url)
    json_response = json.loads(response.text)
    assert json_response['status'] == "success"
    squizz_sessions.pop()