import requests
import json
from datetime import datetime
import pytz
from telegram import Bot, Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, CallbackContext
import matplotlib.pyplot as plt
import numpy as np
from io import BytesIO
from datetime import datetime
import pytz


ZABBIX_URL = "http://10.144.2.194/zabbix/api_jsonrpc.php"

# Función para consultar problemas
def get_gigabit_problems(auth_token,host_type,tipo):
    if host_type=="Equipos Networking":
       group=50
    elif host_type=="Clientes":
         group=51
    elif host_type=="Rectificadores":
         group=53
    elif host_type=="Plantas":
         group=76
    elif host_type=="OLT":
         group=74
    elif host_type=="Switch":
         group=79   
    elif host_type=="Agregadores/Concentradores/PE":
         group=109       
    payload = {
        "jsonrpc": "2.0",
        "method": "problem.get",
        "params": {
            "output": "extend",
            "groupids": group,
            "selectAcknowledges": "extend",
            "selectTags": "extend",
            "search": {
                "name": tipo
            },
            "severities": [4],
            "recent": True,
            "sortfield": ["eventid"],
            "sortorder": "DESC"
        },
        "auth": auth_token,
        "id": 2
    }

    headers = {'Content-Type': 'application/json-rpc'}
    response = requests.post(ZABBIX_URL, json=payload, headers=headers)

    if response.status_code == 200:
        try:
            result = response.json().get('result', [])
            return result
        except ValueError:
            return []
    else:
        return []

# Función para obtener los detalles de un evento
def get_event_details(auth_token, eventid):
    payload = {
        "jsonrpc": "2.0",
        "method": "event.get",
        "params": {
            "output": "extend",
            "selectAcknowledges": "extend",
            "selectTags": "extend",
            "selectSuppressionData": "extend",
            "eventids": eventid,
            "selectHosts": ["hostid", "host"],
            "sortfield": ["clock", "eventid"],
            "sortorder": "DESC"
        },
        "auth": auth_token,
        "id": 3
    }

    headers = {'Content-Type': 'application/json-rpc'}
    response = requests.post(ZABBIX_URL, json=payload, headers=headers)

    if response.status_code == 200:
        try:
            event_details = response.json().get('result', [])
            return event_details
        except ValueError:
            return []
    else:
        return []

# Función para convertir el tiempo a la hora de Colombia
def convert_to_colombia_time(clock):
    colombia_tz = pytz.timezone('America/Bogota')
    utc_time = datetime.utcfromtimestamp(int(clock)).replace(tzinfo=pytz.utc)
    colombia_time = utc_time.astimezone(colombia_tz)
    
    # Formatear la hora para que no incluya la zona horaria
    return colombia_time.strftime("%Y-%m-%d %H:%M:%S")

def calculate_duration(start_time):
    # Asegúrate de que start_time sea un objeto datetime y tenga zona horaria
    if isinstance(start_time, str):
        # Si start_time es un string, lo convertimos a datetime
        start_time = datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S")

    # Aseguramos que start_time sea aware (con zona horaria)
    colombia_tz = pytz.timezone('America/Bogota')
    if start_time.tzinfo is None:  # Si start_time es naive, le asignamos la zona horaria
        start_time = colombia_tz.localize(start_time)

    # Obtener la hora actual en la zona horaria de Colombia
    current_time = datetime.now(pytz.timezone('America/Bogota'))

    # Ahora podemos restar las fechas
    duration = current_time - start_time

    total_days = duration.days
    months = total_days // 30
    days = total_days % 30
    hours, remainder = divmod(duration.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)

    duration_parts = []
    if months > 0:
        duration_parts.append(f"{months}m")
    if days > 0:
        duration_parts.append(f"{days}d")
    if hours > 0:
        duration_parts.append(f"{hours}h")
    if minutes > 0:
        duration_parts.append(f"{minutes}m")
    if seconds > 0:
        duration_parts.append(f"{seconds}s")
    if not duration_parts:
        duration_parts.append("0 segundo(s)")

    return " ".join(duration_parts)

# Función para procesar los eventos y mostrar los resultados
def process_events(auth_token, problems, department_filter=None):
    department_count = {}
    total_problems = 0

    for problem in problems:
        eventid = problem.get("eventid")
        if eventid:
            event_details = get_event_details(auth_token, eventid)
            for event in event_details:
                total_problems += 1
                if 'tags' in event:
                    for tag in event['tags']:
                        if tag['tag'] == 'Departamento':
                            department = tag['value']
                            department_count[department] = department_count.get(department, 0) + 1

    departments = list(department_count.keys()) + ["Mostrar todo"]
    department_msg = "Selecciona un departamento o 'Mostrar todo':"
    
    # Crear los botones de selección para los departamentos
    keyboard = [[InlineKeyboardButton(f"{department} ({department_count.get(department, 0)})", callback_data=department)] for department in department_count.keys()]
    keyboard.append([InlineKeyboardButton("Mostrar todo", callback_data="Mostrar todo")])
    
    return department_msg, InlineKeyboardMarkup(keyboard), department_count

# Manejador de comandos /start
async def start(update: Update, context: CallbackContext):
    await update.message.reply_text("¡Hola! Soy tu bot para consultar problemas de Zabbix. Usa /problemas para comenzar.")

# Manejador de comandos /problemas



def create_table_image(results):
    fig, ax = plt.subplots(figsize=(10, len(results) * 0.5))  # Ajusta el tamaño según el número de filas
    ax.axis('tight')
    ax.axis('off')

    # Definir las columnas de la tabla (en el orden que deseas)
    columns = ["Hora de inicio", "Host", "Problema", "Duración", "Departamento", "Municipio"]

    # Crear los datos para la tabla
    rows = [list(row) for row in results]

    # Crear la tabla
    table = ax.table(cellText=rows, colLabels=columns, loc='center', cellLoc='center', colColours=["#f5f5f5"] * len(columns))

    # Ajustar el tamaño de las celdas
    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.auto_set_column_width(col=list(range(len(columns))))

    # Guardar la imagen en un buffer
    img_buf = BytesIO()
    plt.savefig(img_buf, format='png')
    img_buf.seek(0)  # Reiniciar el puntero a la primera posición

    # Cerrar la figura para liberar recursos
    plt.close(fig)

    return img_buf

