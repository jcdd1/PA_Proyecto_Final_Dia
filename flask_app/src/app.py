import os
from flask import Flask, render_template, jsonify, request
from flask_pymongo import PyMongo
from datetime import datetime
import json
from bson.objectid import ObjectId

from dotenv import load_dotenv


# Definimos la ruta al archivo .env
dotenv_path = os.path.join(os.path.dirname(__file__), '.env')

load_dotenv(dotenv_path)


app = Flask(__name__)

mongo_uri = os.environ.get('MONGO_URI')

if not mongo_uri:
    print("Error: La variable de entorno MONGO_URI no está configurada.")


print(f"Intentando conectar a MongoDB...")
app.config["MONGO_URI"] = mongo_uri

try:
    mongo = PyMongo(app)
    
    sensor1_collection = mongo.db.sensor1 
    print("Conexión a MongoDB y colección 'sensor1' establecida.")

    sensor1_collection.find_one()
    print("Prueba de lectura a la colección 'sensor1' exitosa.")
except Exception as e:
    print(f"Error al conectar o interactuar con MongoDB: {e}")
    mongo = None
    sensor1_collection = None

@app.route('/')
def ruta():
    return 'Mi primer hola mundo'


@app.route('/index')
def index():
    return render_template('index.html')

@app.route('/agregar_dato_prueba')
def agregar_dato_prueba():
    """
    Ruta de prueba para MANDAR (insertar) un dato de ejemplo
    en la colección 'sensor1'.
    """
    if sensor1_collection is not None:
        try:
            
            dato_sensor = {"sensor": "temperatura_prueba", "valor": 30.1, "unidad": "C"}
            # Insertamos el dato en la colección 'sensor1'
            result = sensor1_collection.insert_one(dato_sensor)
            return jsonify({
                "mensaje": "Dato de prueba agregado exitosamente a 'sensor1'",
                "id": str(result.inserted_id)
            })
        except Exception as e:
            return jsonify({"error": f"Error al insertar en la base de datos: {e}"}), 500
    else:
        return jsonify({"error": "La conexión a la base de datos no está establecida."}), 500
    

@app.route('/receive_sensor_data', methods=['POST'])
def receive_sensor_data():
    if sensor1_collection is None:
        
        return jsonify({"error": "La conexión a la base de datos no está establecida."}), 503

    try:
        # Obtener los datos JSON
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No se proporcionó un payload JSON"}), 400

        
        sensor_type = data.get('sensor_type')
        value = data.get('value')
        unit = data.get('unit', 'N/A') 

        if sensor_type is None or value is None:
            return jsonify({"error": "Faltan campos obligatorios: 'sensor_type' o 'value'"}), 400

        
        doc_to_insert = {
            "sensor": sensor_type,
            "valor": value,
            "unidad": unit,
            "timestamp": datetime.now() 
        }

        
        result = sensor1_collection.insert_one(doc_to_insert)


        return jsonify({
            "status": "success",
            "message": "Dato de sensor recibido y guardado exitosamente.",
            "id_mongo": str(result.inserted_id),
            "data_received": doc_to_insert
        }), 201
    except Exception as e:
        print(f"Error al procesar los datos del sensor: {e}")
        return jsonify({"status": "error", "message": f"Error interno del servidor: {e}"}), 500
    
@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

# 1. RUTA DE SALUD (Health Check)
@app.route('/', methods=['GET', 'POST'])
def root_path():
    """El plugin llama a esta ruta para probar la conexión."""
    # Simplemente devolvemos 200 OK.
    return 'OK', 200

# 2. RUTA DE BÚSQUEDA (Search)
@app.route('/search', methods=['POST'])
def search():
    """
    El plugin llama a esta ruta para obtener una lista de métricas disponibles.
    Devolvemos una lista de strings con las series que podemos ofrecer.
    """
    # Como solo ofrecemos una serie de la colección sensor1, la nombramos:
    return jsonify(["sensor1_temperatures"]), 200

# 3. RUTA DE CONSULTA (Query)
@app.route('/query', methods=['POST'])
def query():
    """
    Ruta principal de consulta. Grafana envía el rango de tiempo y las métricas solicitadas.
    """
    # En este punto, Grafana POSTea el JSON con el rango de tiempo (range) 
    # y las métricas seleccionadas (targets).
    
    # 1. Obtenemos los datos de MongoDB
    if sensor1_collection is None:
        return jsonify({"error": "La conexión a la base de datos no está establecida."}), 503

    try:
        # Aquí puedes usar request.get_json() para obtener el rango de tiempo de Grafana
        # y filtrar la consulta, pero por simplicidad, obtenemos los últimos 1000.
        data_cursor = sensor1_collection.find().sort("timestamp", -1).limit(1000)
        
        # 2. Formateamos los datos para que Grafana los entienda.
        # El plugin JSON API Datasource espera un array de objetos JSON para las series de tiempo.
        # ESTRUCTURA DE RESPUESTA ESPERADA: 
        # [
        #   { "target": "sensor1_temperatures", "datapoints": [[value, timestamp_ms], ...] }
        # ]
        
        # Esto requiere una estructura de datos diferente a la ruta /api/data.
        # Aquí convertimos los datos al formato de 'datapoints' (array de arrays).
        datapoints = []
        for document in data_cursor:
            # Convertimos el objeto datetime a timestamp UNIX en milisegundos (ms)
            timestamp_ms = int(document["timestamp"].timestamp() * 1000)
            datapoints.append([document["valor"], timestamp_ms])
            
        # 3. Creamos la respuesta final
        response = [
            {
                # El target debe coincidir con el devuelto en la ruta /search
                "target": "sensor1_temperatures", 
                "datapoints": datapoints
            }
        ]

        return jsonify(response)

    except Exception as e:
        print(f"Error al procesar la consulta de Grafana: {e}")
        return jsonify({"status": "error", "message": f"Error interno del servidor: {e}"}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)