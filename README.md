# pc_mqtt
Python script that enables MQTT Interaction with a Windows PC.

What is possible:
- Turn off device (turning on can be done by WOL)
- Reading device temperatures got from WMI (OpenHardwareMonitor)
- Reading disk loads got from WMI

# Installation
## Configuration 
Look at the config file included in this repo for an example, should be intuitive. 
### MQTT Broker
Fill in your credentials for the MQTT broker and give your device a topic (eg. computer_downstairs).
### Games
Adding games can be done by providing a 
- Game ID: Could be anything, used to form game topic
- Friendly Name: Can be empty, used for clarity
- Executable path: Path to the executable of the program/game
### Computer stats 
There are two types of stats that can be published to the MQTT broker/hassio: device temperatures and disk loads. The device names can be fetched from OpenHardwareMonitor. The topics can be arbitrary

## Home Assistant Configuration
You can add your computer to your Home Assistant and control it from there. Below some examples for hassio
### Computer switch
This switch turns the computer on by sending a Wake On LAN package. The status is fetched by pinging the device. Turning off the device is done by sending a MQTT packet to the program. Change COMPUTER_TOPIC to your device topic.

```YAML
- platform: template
  switches:
    computer_switch:
      friendly_name: Computer
      value_template: "{{ is_state('binary_sensor.computer_status', 'on') }}"
      turn_on:
        service: wake_on_lan.send_magic_packet
        data:
          mac: 'XX:XX:XX:XX:XX:XX'
      turn_off:
        service: mqtt.publish
        data:
          topic: COMPUTER_TOPIC/management/power
          payload: '{ "mode": "OFF"}'
```

### Game Switch
Start playing your game or terminate the process by using this switch template for your games (change COMPUTER_TOPIC and GAME_ID according to your data):
```YAML
- platform: mqtt
  name: "Rocket League"
  state_topic: "COMPUTER_TOPIC/games/GAME_ID/state"
  command_topic: "COMPUTER_TOPIC/games/GAME_ID/cmd"
  payload_on: "START"
  payload_off: "STOP"
  state_on: "Playing"
  state_off: "Not playing"
```

### Computer stats sensors
The script can upload both device temperature and disk loads. To import these sensors in Home Assistant, use the following template (Change COMPUTER_TOPIC to your device topic):
```YAML
  - platform: mqtt
    state_topic: "COMPUTER_TOPIC/cpu_temp"
    name: "CPU temperature"
    unit_of_measurement: "°C"
    qos: 1
  - platform: mqtt
    state_topic: "COMPUTER_TOPIC/c_load"
    name: "C Load"
    unit_of_measurement: "%"
    qos: 1
```