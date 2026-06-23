# managers/mqtt_manager.py

import json
import paho.mqtt.client as mqtt
from config.settings import MQTT_BROKER, MQTT_PORT


class MQTTManager:
    def __init__(self, topic):
        self.topic = topic
        self.client = mqtt.Client()

        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message

        # Conectar al broker
        self.client.connect(MQTT_BROKER, MQTT_PORT, 60)

        self.callback = None

    def set_callback(self, callback_fn):
        """Se ejecutará cuando llegue un mensaje MQTT del topic."""
        self.callback = callback_fn

    def on_connect(self, client, userdata, flags, rc):
        print(f"[MQTT] Conectado a {MQTT_BROKER}:{MQTT_PORT} topic='{self.topic}'")
        self.client.subscribe(self.topic)

    def on_message(self, client, userdata, msg):
        try:
            payload = msg.payload.decode()
            data = json.loads(payload)
            if self.callback:
                self.callback(data)
        except Exception as e:
            print(f"[MQTT] Error al procesar mensaje: {e}")

    def listen_forever(self):
        self.client.loop_forever()
