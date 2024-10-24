import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ForceReply, InputFile
from telegram.ext import ContextTypes, CallbackContext, ConversationHandler
from zabbix_api import (
    zabbix_login,
    search_host_by_name,
    get_problems,
    get_graphs,
    get_items,
    generate_graph_url
)

from datetime import datetime
import time
from io import BytesIO

severity_mapping = {
    4: 'High',
    3: 'Average',
    2: 'Warning',
    1: 'Information'
}


# Función para descargar la imagen del gráfico
def download_graph_image(url):
    response = requests.get(url)
    if response.status_code == 200:
        return BytesIO(response.content)
    else:
        raise Exception("Error al descargar la imagen del gráfico.")





severity_mapping = {
    4: 'High',
    3: 'Average',
    2: 'Warning',
    1: 'Information'
}

# Procesa la selección de problemas
async def process_problems(update: Update, context: CallbackContext, *search_terms):
    username = context.user_data.get('username')
    password = context.user_data.get('password')

    if not username or not password:
        await update.message.reply_text("Error: credenciales no encontradas.")
        return
    
    host_id = context.user_data.get('host_id')
    auth_token = await zabbix_login(username, password)

    if not auth_token:
        await update.callback_query.message.reply_text("Error en la autenticación de Zabbix.")
        return

    problems = []
    for term in search_terms:
        problems.extend(get_problems(auth_token, host_id, term))
    
    if not problems:
        await update.callback_query.message.reply_text(f"No se encontraron problemas relacionados con tu consulta.")
    else:
        for problem in problems:
            severity = int(problem.get('severity', 0))  
            severity_description = severity_mapping.get(severity, 'Unknown')  # Usa 'Unknown' si la severidad no está en el diccionario
            epoch_time = int(problem.get('clock', 0))
            readable_time = datetime.fromtimestamp(epoch_time).strftime('%Y-%m-%d %H:%M:%S')
            
            message = (f"Problema: {problem['name']}\n"
                       f"Severidad: {severity_description}\n"
                       f"Tiempo: {readable_time}")
            await update.callback_query.message.reply_text(message)


def download_image(url):
    headers = {
        'Cookie': 'zbx_session=eyJzZXNzaW9uaWQiOiJmNTcxNmQ3YzkxNmNhYjc5YTIxMTczMTM1MzI5MjQzNSIsInNlcnZlckNoZWNrUmVzdWx0Ijp0cnVlLCJzZXJ2ZXJDaGVja1RpbWUiOjE3MjY1OTE1NzUsInNpZ24iOiJjZjEwNzZkMzNkNDgwODQ2NjdkNGJlMjkwMzY5NmUyMmMyZTQxNTk3NzdkYjAzYTAyMGQ3NjFlNmU1MjA0MTliIn0%3D',  # Reemplaza con tu token de sesión
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()  # Lanza una excepción si ocurre un error HTTP

        if 'image' in response.headers.get('Content-Type', ''):
            return BytesIO(response.content)
        else:
            raise Exception("El contenido descargado no es una imagen.")
    
    except requests.RequestException as e:
        raise Exception(f"Error al descargar la imagen: {e}")



# Muestra las opciones principales
async def show_primary_options(update: Update, context: CallbackContext):
    keyboard = [
        [InlineKeyboardButton("Problemas", callback_data='problems')],
        [InlineKeyboardButton("Gráficas", callback_data='graphs')],
        #[InlineKeyboardButton("Últimos Datos", callback_data='latest_data')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    if update.callback_query:
        await update.callback_query.message.reply_text("¿Qué deseas consultar Problemas o Graficas?", reply_markup=reply_markup)


async def process_graphs(update: Update, context: CallbackContext, *search_terms):

    username = context.user_data.get('username')
    password = context.user_data.get('password')

    # Verificar si las credenciales están disponibles
    if not username or not password:
        await update.message.reply_text("Error: credenciales no encontradas.")
        return
    
    host_id = context.user_data.get('host_id')
    auth_token = await zabbix_login(username, password)

    if not auth_token:
        if update.callback_query:
            await update.callback_query.message.reply_text("Error en la autenticación de Zabbix.")
        else:
            await update.message.reply_text("Error en la autenticación de Zabbix.")
        return

    # Obtener la opción seleccionada por el usuario
    secondary_option = context.user_data.get('secondary_option')
    
    graphs = []
    items = []

    if secondary_option == 'general':
        # Buscar gráficos relacionados con 'ICMP'
        search_terms = ['ICMP']
        for term in search_terms:
            graphs.extend(get_graphs(auth_token, host_id, term))
            items.extend(get_items(auth_token, host_id, term))
        
    if secondary_option == 'energia':
        # Buscar gráficos relacionados con 'ICMP'
        search_terms = ['voltaje', 'correinte', 'temperatura', 'ac']
        for term in search_terms:
            graphs.extend(get_graphs(auth_token, host_id, term))
            items.extend(get_items(auth_token, host_id, term))

    elif secondary_option == 'interfaces':
        # Definir los nombres fijos para la primera fase de filtrado
        fixed_names = ['Network traffic', 'Bits sent', 'Bits received', 'Speed']

        # Inicializar listas para almacenar gráficos e ítems filtrados
        filtered_graphs = []
        filtered_items = []

        # Buscar todos los gráficos e ítems
        all_graphs = get_graphs(auth_token, host_id, filter_name=None)
        all_items = get_items(auth_token, host_id, filter_name=None)

        # Filtrar gráficos por nombres fijos
        for graph in all_graphs:
            if any(fixed_name.lower() in graph['name'].lower() for fixed_name in fixed_names):
                filtered_graphs.append(graph)

        # Filtrar ítems por nombres fijos
        for item in all_items:
            if any(fixed_name.lower() in item['name'].lower() for fixed_name in fixed_names):
                filtered_items.append(item)

        # Aplicar el segundo filtro con las palabras clave del usuario
        search_terms = ' '.join(search_terms).lower()  # Convertir términos de búsqueda a minúsculas
        graphs = [graph for graph in filtered_graphs if search_terms in graph['name'].lower()]
        items = [item for item in filtered_items if search_terms in item['name'].lower()]

    else:
        message_target = update.callback_query.message if update.callback_query else update.message
        await message_target.reply_text("Opción seleccionada no válida.")
        return

    # Preparar el destino del mensaje (callback_query o mensaje regular)
    message_target = update.callback_query.message if update.callback_query else update.message

    if not graphs and not items:
        await message_target.reply_text("No se encontraron gráficas o ítems que coincidan con tu consulta.")
        return

    # Generar botones para las gráficas e ítems
    keyboard = []

    for graph in graphs:
        keyboard.append([InlineKeyboardButton(graph['name'], callback_data=f"graph_{graph['graphid']}")])

    for item in items:
        keyboard.append([InlineKeyboardButton(item['name'], callback_data=f"item_{item['itemid']}")])

    reply_markup = InlineKeyboardMarkup(keyboard)
    await message_target.reply_text("Selecciona una gráfica o ítem para ver:", reply_markup=reply_markup)



