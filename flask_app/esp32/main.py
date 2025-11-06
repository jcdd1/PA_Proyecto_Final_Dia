import ujson
import urequests
import time
import network
import random

# ONFIGURACIÓN 
WIFI_SSID = 'Wokwi-GUEST'
WIFI_PASS = ''

SERVER_URL = 'https://pa-proyecto-final-dia.onrender.com/receive_sensor_data/'


def connect_wifi():
    
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        print(f'Conectando a red: {WIFI_SSID}')
        wlan.connect(WIFI_SSID, WIFI_PASS)
        timeout = 10
        while not wlan.isconnected() and timeout > 0:
            time.sleep(1)
            print('.')
            timeout -= 1
        
        if wlan.isconnected():
            print('WiFi Conectado')
            print('Configuración de red:', wlan.ifconfig())
        else:
            print('Error de conexión WiFi.')
            return None
    return wlan

def read_simulated_data(sensor_type):
    """Simula la lectura de datos del sensor."""
    if sensor_type == "Temperature":
        # Temperatura entre 20.0 y 35.9
        value = random.uniform(20.0, 36.0)
        return round(value, 1), "C"
    elif sensor_type == "Humidity":
        # Humedad entre 40.0 y 70.9
        value = random.uniform(40.0, 71.0)
        return round(value, 1), "%"
    return None, None

def send_data(sensor_type):
    value, unit = read_simulated_data(sensor_type)
    if value is None:
        print(f"Error: Tipo de sensor desconocido: {sensor_type}")
        return

    payload_data = {
        "sensor_type": sensor_type,
        "value": value,
        "unit": unit
    }
    
    # Serializar el payload a JSON
    json_payload = ujson.dumps(payload_data)
    
    print("\n--- Enviando Datos ---")
    print(f"Payload JSON: {json_payload}")

    try:
        # Definir los encabezados (importante para Flask)
        headers = {'Content-Type': 'application/json'}
        
        # Realizar la petición POST
        response = urequests.post(
            SERVER_URL, 
            data=json_payload, 
            headers=headers
        )

        # Manejar la respuesta
        if response.status_code == 201:
            print(f"[{sensor_type}] ÉXITO: Código 201. Dato guardado en MongoDB.")
        else:
            print(f"ERROR: Código de respuesta HTTP: {response.status_code}")
            # Mostrar la respuesta completa para debugging
            print(f"Respuesta del Servidor: {response.text}")

        response.close() # Cierra la conexión

    except Exception as e:
        print(f"ERROR al realizar la petición HTTP: {e}")


def main():
    
    # Conectar a Wi-Fi una vez
    if connect_wifi():
        while True:
           
            send_data("Temperature")
            time.sleep(2)
            send_data("Humidity")

            # Esperar 15 segundos antes de la siguiente ronda de envíos
            print("\nEsperando 15 segundos...")
            time.sleep(15)

if __name__ == '__main__':
    main()