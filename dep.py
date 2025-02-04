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
def get_gigabit_problems(auth_token,host_type,tipo,severity):
    if host_type=="Equipos Networking":
       group=["79", "74", "109","66","67","73","70","81","110"]
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
            "severities": severity,
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
            filtered_result = [event for event in result if event.get('name') != "Puerta Abierta"]
            return filtered_result
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



# Función para generar una tabla con matplotlib y devolverla como imagen
import matplotlib.pyplot as plt
from io import BytesIO

def create_table_image(results, selected_option):
    # Definir las columnas de la tabla según la opción seleccionada
    if selected_option == "Nodos caídos":
     columns = ["Hora de inicio", "Host", "Problema", "Duración", "Departamento", "Municipio", "Tk", "Equipo"]
    else:
     columns = ["Hora de inicio", "Host", "Problema", "Duración", "Departamento", "Municipio", "Tk"]

       # Si selected_option no tiene valor, usa el else
    if not selected_option:
     columns = ["Hora de inicio", "Host", "Problema", "Duración", "Departamento", "Municipio", "Tk"]

    # Crear los datos para la tabla
    rows = [row[:3] + row[4:] for row in results]

    # Si la opción seleccionada es "Nodos caídos" y hay que añadir la columna "Equipo"
    if selected_option == "Nodos caídos":
        for row in rows:
            # Asignamos un valor para la columna "Equipo" según el Host (o el valor correspondiente)
            if len(row) == len(columns) - 1:  # Si la fila tiene 8 columnas (sin "Equipo")
                equipo = "Desconocido"  # Valor por defecto
                if row[1].startswith('AC'):  # Esto es solo un ejemplo, puedes ajustar la lógica
                    equipo = "Switch"
                elif row[1].startswith('GP'):
                    equipo = "OLT"
                else:
                    equipo = "Agregador"
                row.append(equipo)  # Añadir la columna "Equipo" a la fila

    # Ajustar el tamaño de la figura según el número de filas y el número de columnas
    fig, ax = plt.subplots(figsize=(len(rows) * 0.15, len(columns) * 0.5))  # Ajusta el tamaño según el número de filas y columnas
    ax.axis('tight')
    ax.axis('off')

    # Verificar que las filas tengan el número adecuado de columnas
    for i, row in enumerate(rows):
        if len(row) != len(columns):
            print(f"Advertencia: La fila {i} tiene {len(row)} columnas, pero se esperaban {len(columns)}")
            # Si la fila tiene menos columnas, agregar valores vacíos
            while len(row) < len(columns):
                row.append("")  # Agregar una columna vacía si falta alguna
            # Si la fila tiene más columnas, truncar las filas
            if len(row) > len(columns):
                row = row[:len(columns)]
            rows[i] = row  # Actualizar la fila

    # Crear la tabla
    table = ax.table(cellText=rows, colLabels=columns, loc='center', cellLoc='center', colColours=["#f5f5f5"] * len(columns))

    # Ajustar el tamaño de las celdas
    table.auto_set_font_size(False)
    table.set_fontsize(8)  # Reducir el tamaño de la fuente para adaptarse mejor

    # Ajustar el ancho de las columnas (puedes cambiar estos valores según el contenido)
    column_widths = [0.2, 0.2, 0.3, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2] if selected_option == "Nodos caídos" else [0.2, 0.2, 0.3, 0.2, 0.2, 0.2, 0.2, 0.2]
    for i, width in enumerate(column_widths):
        table.auto_set_column_width(col=[i])  # Establecer el ancho para cada columna de forma individual

    # Ajustar el espacio entre las celdas y la figura para evitar el corte
    plt.subplots_adjust(left=0.05, right=0.95, top=0.95, bottom=0.05)

    # Guardar la imagen en un buffer
    img_buf = BytesIO()
    plt.savefig(img_buf, format='png', bbox_inches='tight')  # Ajustar la figura de forma ajustada
    img_buf.seek(0)  # Reiniciar el puntero a la primera posición

    # Cerrar la figura para liberar recursos
    plt.close(fig)

    return img_buf



# Función para generar una tabla con matplotlib y devolverla como imagen
def create_table_image_incidents(results):
    # Definir las columnas de la tabla (en el orden que deseas)
    columns = ["Tiempo inicio medida", "Zona", "Host","PLR %", "Departamento", "Municipio"]

    # Ajustar el tamaño de la figura según el número de filas y el número de columnas
    fig, ax = plt.subplots(figsize=(len(results) * 0.15, len(columns) * 0.5))  # Ajusta el tamaño según el número de filas y columnas
    ax.axis('tight')
    ax.axis('off')

    # Crear los datos para la tabla
    rows = [list(row) for row in results]

    # Crear la tabla
    table = ax.table(cellText=rows, colLabels=columns, loc='center', cellLoc='center', colColours=["#f5f5f5"] * len(columns))

    # Ajustar el tamaño de las celdas
    table.auto_set_font_size(False)
    table.set_fontsize(8)  # Reducir el tamaño de la fuente para adaptarse mejor

    # Ajustar el ancho de las columnas (con valores más grandes o pequeños según sea necesario)
    column_widths = [0.2, 0.2, 0.3, 0.2,0.2, 0.2, 0.2,0.2]  # Ajusta estos valores según el contenido
    for i, width in enumerate(column_widths):
        table.auto_set_column_width(col=[i])  # Establecer el ancho para cada columna de forma individual

    # Ajustar el espacio entre las celdas y la figura para evitar el corte
    plt.subplots_adjust(left=0.05, right=0.95, top=0.95, bottom=0.05)

    # Guardar la imagen en un buffer
    img_buf = BytesIO()
    plt.savefig(img_buf, format='png', bbox_inches='tight')  # Ajustar la figura de forma ajustada
    img_buf.seek(0)  # Reiniciar el puntero a la primera posición

    # Cerrar la figura para liberar recursos
    plt.close(fig)

    return img_buf
