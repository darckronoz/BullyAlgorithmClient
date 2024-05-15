from flask import Flask, render_template, jsonify
from flask_socketio import SocketIO
from datetime import datetime
import time
import os
import time
import random
import threading
import requests

BASE_URL = "localhost"
MONITOR_PORT = ""

known_ports = []
current_leader = None
my_port = None
my_id = None
health_check_scheduler = None
selecting_leader  = False
enabled = True

app = Flask(__name__)
socketio = SocketIO(app)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/healthcheck', methods=['GET'])
def healthcheck():
    return '', 200

@app.route('/weight', methods=['GET'])
def get_weight():
    return str(my_id), 200

def init_health_check():
    health_check_thread = threading.Thread(target=check_leader_health, args=(BASE_URL,))
    health_check_thread.daemon = True
    health_check_thread.start()

def select_new_leader(): 
    global current_leader, my_port, known_ports, possible_leader, selecting_leader
    possible_leader = my_port
    selecting_leader = True
    sendlog("seleccionando nuevo lider", "")
    for port in known_ports:
        sendlog(f"analizando puerto {port}", "")
        if port != current_leader:
            node_id = get_node_id(BASE_URL+f":{port}/weight")
            sendlog(f"en puerto {port}, se obtuvo el id: {node_id}", "")
            if node_id > my_id:
                sendlog(f"el id: {node_id} es mayor a mi id: {my_id}, posible lider: {port}", "")
                possible_leader = port
            current_leader = possible_leader
            if current_leader == my_port:
                update_leadstatus()
                sendlog("soy el nuevo lider :D")
            else:
                sendlog(f"nuevo lider: {port}")
            selecting_leader = False
        else:
            sendlog(f"{port} es el lider caido, pasando al siguiente puerto", "")

def update_leadstatus():
    global my_port    
    target_url = f"{BASE_URL}:{MONITOR_PORT}/leadStatus"
    data = {
        "port": my_port,
        "leadStatus": True
    }
    response = requests.post(target_url, json=data)
    response.raise_for_status()  # Lanza una excepción si hay un error HTTP
    sendlog(f"Actualizando al monitor... {target_url}, enviando: {data}")
    if not response.status_code == 200:
        sendlog("Error al enviar mensaje al monitor. ", target_url)

def get_node_id(url):
    try:
        id = -1
        response = requests.get(url)
        if response.status_code == 200:
            id = int(response.text)
        return id
    except:
        return -1

def check_leader_health(url):
    while True:
        if not my_port==current_leader and not selecting_leader:
            try:
                response = requests.get(url+current_leader+"/healthcheck")
                if not response.status_code == 200:
                    sendlog(f"Health check failed at {url}. Status code: {response.status_code}", url)
                    select_new_leader()
            except requests.exceptions.RequestException as e:
                sendlog(f"Health check failed at {url}. Error: {e}", url)
                print(f"Health check failed at {url}. Error: {e}")
            
            time.sleep(random.randint(1, 4))

@socketio.on('connect')
def test_connect():
    print('Client connected')

@socketio.on('start_stream')
def start_stream():
    print('Starting stream')
    while True:
        socketio.emit('myport', str(my_port))
        if my_port==current_leader:
            socketio.emit('amilead', 'no soy 😞')
        else:
            socketio.emit('amilead', 'si soy 👑')
        socketio.emit('whoslead', 'El lider es '+str(current_leader)+'')
        time.sleep(1)

def sendlog(msg, ip):
    thetime = datetime.now()
    socketio.emit('log', '['+ thetime.strftime('%m/%d/%y %H:%M:%S') + '] ' + msg + ' ip: ' + ip)
    
def validate_numeric(value):
    try:
        int(value)
        return True
    except ValueError:
        return False

def assign_env_variables():
    global my_port, my_id, known_ports, current_leader

    my_port = "5000"#os.getenv('MY_PORT')
    my_weight = "2"#os.getenv('MY_WEIGHT')
    known_ports_str = "5000"#os.getenv('KNOWN_PORTS')

    if not all(map(validate_numeric, [my_port, my_weight])):
        print("Los valores de las variables de entorno deben ser numéricos.")
        exit(1)

    my_port = int(my_port)
    my_id = int(my_weight)
    known_ports = list(map(int, known_ports_str.split(', ')))

    if len(known_ports) <= 1:
        current_leader = my_port

if __name__ == '__main__':
    assign_env_variables()
    init_health_check()
    socketio.run(app)