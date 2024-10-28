import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputFile
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler, CallbackContext
from io import BytesIO
from datetime import datetime
import time
import io
import asyncio

# Credenciales de Zabbix y Telegram
TELEGRAM_TOKEN = '7319075472:AAGHNFfervCfH3lt5mblsMoDgjtNQwydlwo'
ZABBIX_URL = "http://10.144.2.194/zabbix/api_jsonrpc.php"
ZABBIX_USER = "AztBot"
ZABBIX_PASSWORD = "Temporal123*2024"

SECURITY_KEY = 'azt'
# Función para autenticarse en Zabbix
def zabbix_login():
    payload = {
        "jsonrpc": "2.0",
        "method": "user.login",
        "params": {
            "username": ZABBIX_USER,
            "password": ZABBIX_PASSWORD
        },
        "id": 1,
        "auth": None
    }
    headers = {'Content-Type': 'application/json-rpc'}
    response = requests.post(ZABBIX_URL, json=payload, headers=headers)
    return response.json().get('result')

# Función para buscar hosts por nombre
async def search_host_by_name(auth_token, host_name):
    payload = {
        "jsonrpc": "2.0",
        "method": "host.get",
        "params": {
            "output": ["hostid", "name"],
            "search": {"name": host_name}
        },
        "id": 2,
        "auth": auth_token
    }
    headers = {'Content-Type': 'application/json-rpc'}
    response = requests.post(ZABBIX_URL, json=payload, headers=headers)
    return response.json().get('result', [])

# Función para obtener problemas en un host específico
def get_problems(auth_token, host_id, filter_name):
    payload = {
        "jsonrpc": "2.0",
        "method": "problem.get",
        "params": {
            "output": "extend",
            "hostids": host_id,
            "time_from": int(time.time() - 12 * 3600),  # Últimas 12 horas
            "recent": True,
            "search": {"name": filter_name},
            "sortfield": ["eventid"],
            "sortorder": "DESC"
        },
        "id": 3,
        "auth": auth_token
    }
    headers = {'Content-Type': 'application/json-rpc'}
    response = requests.post(ZABBIX_URL, json=payload, headers=headers)
    return response.json().get('result', [])

# Función para obtener gráficas en un host específico
def get_graphs(auth_token, host_id, filter_name):
    payload = {
        "jsonrpc": "2.0",
        "method": "graph.get",
        "params": {
            "output": ["graphid", "name"],
            "hostids": host_id,
            "search": {"name": filter_name},
        },
        "id": 4,
        "auth": auth_token
    }
    headers = {'Content-Type': 'application/json-rpc'}
    response = requests.post(ZABBIX_URL, json=payload, headers=headers)
    return response.json().get('result', [])

# Función para obtener ítems por host con un filtro
def get_items(auth_token, host_id, filter_name):
    payload = {
        "jsonrpc": "2.0",
        "method": "item.get",
        "params": {
            "output": ["itemid", "name"],
            "hostids": host_id,
            "search": {"name": filter_name},
        },
        "id": 5,
        "auth": auth_token
    }
    headers = {'Content-Type': 'application/json-rpc'}
    response = requests.post(ZABBIX_URL, json=payload, headers=headers)
    return response.json().get('result', [])

# Función para generar la URL de la gráfica o del elemento
def generate_graph_url(graph_id=None, item_id=None, chart_type="chart.php"):
    base_url = f"http://10.144.2.194/zabbix/{chart_type}"
    if graph_id:
        # URL para gráficos
        url = f"{base_url}?graphid={graph_id}&from=now-12h&to=now&height=201&width=1188&profileIdx=web.charts.filter"
        return url
    elif item_id:
        # URL para elementos
        url = f"{base_url}?itemids[]={item_id}&from=now-12h&to=now&height=201&width=1188&profileIdx=web.charts.filter"
        return url
    else:
        raise ValueError("Debe proporcionar un graph_id o un item_id.")
    
# Función para descargar la imagen del gráfico
def download_graph_image(url):
    response = requests.get(url)
    if response.status_code == 200:
        return BytesIO(response.content)
    else:
        raise Exception("Error al descargar la imagen del gráfico.")

# Muestra opciones después de la selección principal
async def show_secondary_options(update: Update, context: CallbackContext):
    keyboard = [
        [InlineKeyboardButton("Interfaces", callback_data='interfaces')],
        [InlineKeyboardButton("General", callback_data='general')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    if update.callback_query:
        await update.callback_query.message.reply_text("Selecciona los tipos de datos que deseas consultar:", reply_markup=reply_markup)

# Maneja la selección del host
async def handle_host_selection(update: Update, context: CallbackContext):
    if update.callback_query:
        query = update.callback_query
        host_id = query.data
        context.user_data['host_id'] = host_id
        await show_primary_options(update, context)

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

# Maneja la selección de las opciones principales
async def handle_primary_option_selection(update: Update, context: CallbackContext):
    if update.callback_query:
        query = update.callback_query
        option = query.data
        context.user_data['selected_option'] = option
        await show_secondary_options(update, context)

# Maneja la selección de las subcategorías (Interfaces o General)
async def handle_secondary_option_selection(update: Update, context: CallbackContext):
    if update.callback_query:
        query = update.callback_query
        secondary_option = query.data
        context.user_data['secondary_option'] = secondary_option

        if context.user_data['selected_option'] == 'problems':
            if secondary_option == 'interfaces':
                await query.message.reply_text('Buscando problemas relacionados con "Interface"...')
                await process_problems(update, context, 'link down', 'saturated')
            elif secondary_option == 'general':
                await query.message.reply_text('Buscando problemas relacionados con "ICMP"...')
                await process_problems(update, context, 'Unavailable by ICMP ping')
        elif context.user_data['selected_option'] == 'graphs':
            if secondary_option == 'interfaces':
                await query.message.reply_text('Por favor, ingresa una palabra clave de lainterfaz que deseas ver para optimizar la busqueda:')
                return  
            elif secondary_option == 'general':
                await query.message.reply_text('Buscando gráficas relacionadas con "ICMP"...')
                await process_graphs(update, context, 'ICMP')

severity_mapping = {
    4: 'High',
    3: 'Average',
    2: 'Warning',
    1: 'Information'
}

# Procesa la selección de problemas
async def process_problems(update: Update, context: CallbackContext, *search_terms):
    host_id = context.user_data.get('host_id')
    auth_token = zabbix_login()

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
            severity = int(problem.get('severity', 0))  # Asegúrate de que es un entero
            severity_description = severity_mapping.get(severity, 'Unknown')  # Usa 'Unknown' si la severidad no está en el diccionario
            epoch_time = int(problem.get('clock', 0))
            readable_time = datetime.fromtimestamp(epoch_time).strftime('%Y-%m-%d %H:%M:%S')
            
            message = (f"Problema: {problem['name']}\n"
                       f"Severidad: {severity_description}\n"
                       f"Tiempo: {readable_time}")
            await update.callback_query.message.reply_text(message)

async def process_graphs(update: Update, context: CallbackContext, *search_terms):
    host_id = context.user_data.get('host_id')
    auth_token = zabbix_login()

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

    # Enviar las imágenes de los gráficos filtrados
    for graph in graphs:
        if "Network traffic" in graph['name'] in graph['name']:
            url = generate_graph_url(graph_id=graph['graphid'], chart_type="chart2.php")
        else:
            url = generate_graph_url(graph_id=graph['graphid'])
        try:
            image = download_image(url)
            await message_target.reply_photo(photo=image, caption=graph['name'])
        except Exception as e:
            await message_target.reply_text(f"Error al descargar la imagen para el gráfico: {graph['name']} - {e}")

    # Enviar las imágenes de los ítems filtrados
    for item in items:
        if "Network Traffic" in item['name'] in item['name']:
            url = generate_graph_url(item_id=item['itemid'], chart_type="chart2.php")
        else:
            url = generate_graph_url(item_id=item['itemid'])
        try:
            image = download_image(url)
            await message_target.reply_photo(photo=image, caption=item['name'])
        except Exception as e:
            await message_target.reply_text(f"Error al descargar la imagen para el ítem: {item['name']} - {e}")

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
      
# Procesa el mensaje de texto para filtrar gráficas por palabra clave
async def handle_text_message(update: Update, context: CallbackContext):
    # Verifica si se está esperando la clave de seguridad
    if 'waiting_for_key' in context.user_data and context.user_data['waiting_for_key']:
        # Verifica la clave de seguridad
        if update.message.text == SECURITY_KEY:
            context.user_data['waiting_for_key'] = False  # La clave fue ingresada correctamente
            
            # Crear un teclado con las opciones
            keyboard = [
                [InlineKeyboardButton("Buscar Hosts", callback_data='search_hosts')],
                [InlineKeyboardButton("Buscar Gráficas", callback_data='search_graphs')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text("Clave correcta. Por favor, elige una opción:", reply_markup=reply_markup)
        else:
            await update.message.reply_text("Clave incorrecta. Inténtalo de nuevo.")
        return
    
    # Manejo de búsqueda de gráficas
    if 'waiting_for_graph_keyword' in context.user_data and context.user_data['waiting_for_graph_keyword']:
        keyword = update.message.text
        auth_token = zabbix_login()

        # Mensaje de carga mientras se busca
        loading_message = await update.message.reply_text("Cargando, por favor espera...")

        try:
            # Buscar gráficas según la palabra clave ingresada
            graphs = await asyncio.wait_for(search_graphs_by_keyword(auth_token, keyword), timeout=10)
            
            # Muestra solo las primeras cinco gráficas
            displayed_graphs = graphs[:5]

            if displayed_graphs:
                keyboard = [[InlineKeyboardButton(graph['name'], callback_data=graph['graphid'])] for graph in displayed_graphs]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await loading_message.edit_text("Aquí están las gráficas encontradas:\n\n¿Es el resultado que esperabas? (sí/no)", reply_markup=reply_markup)
                
                # Guarda el estado de la búsqueda
                context.user_data['graphs'] = graphs  # Guarda todas las gráficas encontradas
                context.user_data['last_graphs_displayed'] = displayed_graphs  # Guarda las gráficas que se mostraron
                context.user_data['waiting_for_graph_confirmation'] = True  # Indica que se está esperando confirmación
            else:
                await loading_message.edit_text("No se encontraron gráficas que coincidan con esa palabra clave.")
        except asyncio.TimeoutError:
            await loading_message.edit_text("El tiempo de espera fue demasiado. Intenta de nuevo.")
            return

        return

    # Manejo de respuesta de confirmación sobre gráficas
    if 'waiting_for_graph_confirmation' in context.user_data and context.user_data['waiting_for_graph_confirmation']:
        response = update.message.text.lower()

        if response == "sí":
            # Pregunta cuántas más desea ver
            await update.message.reply_text("¿Cuántas más deseas ver?")
            context.user_data['waiting_for_more_graphs_count'] = True  # Espera la cantidad de gráficas
        elif response == "no":
            await update.message.reply_text("Entendido. Si deseas buscar más gráficas, por favor ingresa una nueva palabra clave.")
            context.user_data['waiting_for_graph_keyword'] = True  # Listo para buscar otra vez
            return
        else:
            await update.message.reply_text("Por favor, responde con 'sí' o 'no'.")
        return

    # Manejo de la respuesta sobre cuántas más se desean ver
    if 'waiting_for_more_graphs_count' in context.user_data and context.user_data['waiting_for_more_graphs_count']:
        try:
            count = int(update.message.text)  # Espera que el usuario introduzca un número
            all_graphs = context.user_data['graphs']
            additional_graphs = all_graphs[5:5 + count]  # Muestra más gráficas

            if additional_graphs:
                keyboard = [[InlineKeyboardButton(graph['name'], callback_data=graph['graphid'])] for graph in additional_graphs]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await update.message.reply_text("Aquí tienes más gráficas:", reply_markup=reply_markup)
            else:
                await update.message.reply_text("No hay más gráficas disponibles.")
        except ValueError:
            await update.message.reply_text("Por favor, introduce un número válido.")
        return

    # Aquí puedes manejar la selección del menú
    if update.message.text in ['Buscar Hosts', 'Buscar Gráficas']:
        if update.message.text == 'Buscar Hosts':
            await update.message.reply_text("Por favor, introduce el nombre del host que deseas consultar:")
            context.user_data['waiting_for_host_name'] = True  # Indica que se está esperando el nombre del host
        elif update.message.text == 'Buscar Gráficas':
            await update.message.reply_text("Por favor, ingresa una palabra clave para buscar gráficas:")
            context.user_data['waiting_for_graph_keyword'] = True  # Indica que se está esperando la palabra clave para gráficas
        return

    # Si no se está esperando clave ni opciones del menú
    auth_token = zabbix_login()
    if not auth_token:
        await update.message.reply_text("Error en la autenticación de Zabbix.")
        return

    host_name = update.message.text

    # Mensaje de carga mientras se busca el host
    loading_message = await update.message.reply_text("Cargando, por favor espera...")

    try:
        hosts = await asyncio.wait_for(search_host_by_name(auth_token, host_name), timeout=10)

        if not hosts:
            await loading_message.edit_text("No se encontraron hosts que coincidan con ese nombre.")
            return

        keyboard = [[InlineKeyboardButton(host['name'], callback_data=host['hostid'])] for host in hosts]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await loading_message.edit_text("Selecciona un host:", reply_markup=reply_markup)
    except asyncio.TimeoutError:
        await loading_message.edit_text("El tiempo de espera fue demasiado. Intenta de nuevo.")

# Función para buscar gráficas por palabra clave
async def search_graphs_by_keyword(auth_token, keyword):
    payload = {
        "jsonrpc": "2.0",
        "method": "graph.get",
        "params": {
            "output": ["graphid", "name"],
            "search": {"name": keyword},
        },
        "id": 4,
        "auth": auth_token
    }
    headers = {'Content-Type': 'application/json-rpc'}
    response = requests.post(ZABBIX_URL, json=payload, headers=headers)
    return response.json().get('result', [])

# Función de inicio que limpia el estado
async def start(update: Update, context: CallbackContext):
    context.user_data.clear()  # Limpia los datos del contexto para reiniciar el flujo
    context.user_data['waiting_for_key'] = True  # Indica que se está esperando la clave de seguridad
    await update.message.reply_text("Hola soy el asistente de Red de Azteca Comunicaciones, por favor ingrese la clave de seguridad para certificar que perteneces a nuestra compañía:")

#Funcion para manejar el menú principal
async def handle_main_menu_selection(update: Update, context: CallbackContext):
    if update.callback_query:
        query = update.callback_query
        option = query.data
        
        if option == 'search_hosts':
            await query.message.reply_text("Por favor, introduce el nombre del host que deseas consultar:")
            context.user_data['waiting_for_host_name'] = True  # Indica que se está esperando el nombre del host
        elif option == 'search_graphs':
            await query.message.reply_text("Por favor, ingresa una palabra clave para buscar gráficas:")
            context.user_data['waiting_for_graph_keyword'] = True  # Indica que se está esperando la palabra clave para gráficas

#Manejador para regresar al menu
async def handle_menu(update: Update, context: CallbackContext):
    # Crear un teclado con las opciones
    keyboard = [
        [InlineKeyboardButton("Buscar Hosts", callback_data='search_hosts')],
        [InlineKeyboardButton("Buscar Gráficas", callback_data='search_graphs')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Por favor, elige una opción:", reply_markup=reply_markup)



# Crear la aplicación del bot
def main():
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    # Definir manejadores
    application.add_handler(CommandHandler('start', start))
    # Añadir el manejador para el comando /menu
    application.add_handler(CommandHandler("menu", handle_menu))
    application.add_handler(CallbackQueryHandler(handle_main_menu_selection, pattern='^(search_hosts|search_graphs)$'))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_message))
    application.add_handler(CallbackQueryHandler(handle_host_selection, pattern=r'^\d+$'))
    application.add_handler(CallbackQueryHandler(handle_primary_option_selection, pattern=r'^(problems|graphs)$'))#|latest_data)$'))
    application.add_handler(CallbackQueryHandler(handle_secondary_option_selection, pattern=r'^(interfaces|general)$'))

    # Ejecutar el bot
    application.run_polling()

if __name__ == '__main__':
    main()