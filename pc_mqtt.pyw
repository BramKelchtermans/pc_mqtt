import paho.mqtt.client as mqtt
import paho.mqtt.publish as publish
import wmi 
import threading
import time, pythoncom
import os 
import json

config = {} 


#############################
#### MQTT Settings ##########
#############################
mqtt_broker = "192.168.178.10"
mqtt_username = "mqtt"
mqtt_password = "mqtt_broker"

mqtt_topic = "computer_bram"

# On connect to MQTT broker
def on_connect(client, userdata, flags, rc):
    print("Connected with result code " + str(rc))

# On message from MQTT broker
def on_message(client, userdata, message):
    payload = str(message.payload.decode("utf-8"))

    if message.topic == mqtt_topic  + "/management/power":
        handle_power_management(payload)
    if "games" in message.topic:
        handle_game_msg(message.topic, payload)

# Get temperature by device name(eg. CPU Core)
def get_temp(name):
    w = wmi.WMI(namespace="root\OpenHardwareMonitor")
    temperature_infos = w.Sensor()
    for sensor in temperature_infos:
        if sensor.SensorType==u'Temperature' and sensor.Name == name:
            return sensor.Value
    return 0

# Get disk load by device name (eg. C - Used Space)
def get_load(name):
    w = wmi.WMI(namespace="root\OpenHardwareMonitor")
    sensors = w.Sensor()
    for sensor in sensors:
        if sensor.Name == name:
            return(sensor.Value)

# Publish device stats to MQTT broker (adjust this according needs)
def publish_stats():
    computer_stats = config['computer_stats']

    # Publish device temps
    for d in computer_stats['device_temps']:
        temp = get_temp(d['device_name'])
        publish.single(mqtt_topic + d['device_topic'], "{:.2f}".format(temp), hostname=mqtt_broker)

    # Publish disk loads
    for d in computer_stats['drive_loads']:
        temp = get_load(d['drive_letter'] + " - Used Space")
        publish.single(mqtt_topic + d['drive_topic'], "{:.2f}".format(temp), hostname=mqtt_broker)

    # Publish device status
    publish.single(mqtt_topic + "/power_status", "ON", hostname=mqtt_broker)
def get_game_process(g):
    running_processes = get_running_processes()
    game_exec = get_exec_from_path(g['path'])
    for p in running_processes:
        if p.Name == game_exec:
            return p
    return None 

def publish_game_status():
    games = config['games']
    

    for g in games:
        topic = mqtt_topic + "/games/" + g['id'] + "/state"
        payload = "Not playing";
        if get_game_process(g) is not None: 
            payload = "Playing"
        
        
        publish.single(topic, payload, hostname=mqtt_broker)

def get_running_processes():
    f = wmi.WMI()
    running_processes = f.Win32_Process()
    return running_processes

def get_exec_from_path(path):
    parts = path.split('\\')
    return parts[len(parts) - 1]

def start_sensor_thread():
    pythoncom.CoInitialize()
    while True:
        publish_stats()

        publish_game_status()

        time.sleep(5)

def handle_power_management(payload):
    x = json.loads(payload)
    if x["mode"] == "OFF":
        publish.single(mqtt_topic + "power_status", "OFF", hostname=mqtt_broker)
        os.system("shutdown /s /t 1")


def handle_game_msg(topic, payload):
    sub_topics = topic.split('/')

    game_id = sub_topics[2]
    game_topic = sub_topics[3]
    games = config['games']

    if game_topic == 'cmd': 
        for g in games:
            if g['id'] == game_id:
                exec_game_cmd(g, payload)

        
def exec_game_cmd(game_obj, payload):
    if payload == "START":
        os.system('"' + game_obj['path'] + '"')
    if payload == "STOP":
        process = get_game_process(game_obj)
        if process is not None:
            process.Terminate()
    publish_game_status()


def get_config():
    with open("config.json", "r") as f:
        j = json.load(f)
    global config
    config = j

def read_settings():
    global mqtt_broker, mqtt_username, mqtt_password, mqtt_topic
    settings = config['mqtt_settings']

    mqtt_broker = settings['broker']
    mqtt_password = settings['password']
    mqtt_username = settings['username']
    mqtt_topic = settings['topic']
    
def start_hardware_monitor():
    exec_path = os.path.dirname(os.path.realpath(__file__)) + "\\OpenHardwareMonitor\\OpenHardwareMonitor.exe"
    os.system(exec_path)


def main():
    client = mqtt.Client()

    client.on_connect = on_connect
    client.on_message = on_message

    client.connect(mqtt_broker, 1883,60)

    client.subscribe(mqtt_topic + "/management/#")
    client.subscribe(mqtt_topic +"/games/#")

    sensor_thread = threading.Thread(target=start_sensor_thread)
    sensor_thread.daemon = True
    sensor_thread.start()

    client.loop_forever()

    sensor_thread.join()

if __name__ == "__main__":
    start_hardware_monitor()

    get_config() 

    read_settings()

    main()