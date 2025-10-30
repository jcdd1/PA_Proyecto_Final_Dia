import os
from flask import Flask, render_template, jsonify, request
from flask_pymongo import PyMongo

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
    
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)