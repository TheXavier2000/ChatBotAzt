from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ForceReply
from telegram.ext import ContextTypes, CallbackContext, ConversationHandler
from zabbix_api import (
    zabbix_login, 
    get_problems, 
    get_graphs, 
    get_items, 
    generate_graph_url, 
    search_host_by_name
)
from utils import (
    download_graph_image, 
    show_primary_options, 
    process_problems, 
    download_image, 
    process_graphs
)
from states import (
    USERNAME, 
    PASSWORD, 
    AREA_SELECTION, 
    HOST_SELECTION, 
    PRIMARY_OPTION_SELECTION, 
    SECONDARY_OPTION_SELECTION, 
    GRAPH_ITEM_SELECTION
)
user_credentials = {}  # Un diccionario para guardar tokens de autenticación de los usuarios

# Comando /start para iniciar la conversación
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.effective_user
    await update.message.reply_text(
        f"Hola {user.first_name}, por favor ingresa tu nombre de usuario.",
        reply_markup=ForceReply(selective=True),
    )
    return USERNAME

async def handle_username(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    username = update.message.text
    context.user_data['username'] = username  # Guardar el nombre de usuario
    await update.message.reply_text("Por favor ingresa tu contraseña.")
    return PASSWORD

# Manejo de la contraseña y validación
async def handle_password(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    password = update.message.text
    username = context.user_data.get('username')

    try:
        auth_token = await zabbix_login(username, password)  # Función de autenticación
        
        user_id = update.effective_user.id
        user_credentials[user_id] = {'auth_token': auth_token}  # Guardar token

        context.user_data['auth_token'] = auth_token  # Guardar token en context
        context.user_data['password'] = password  # Guardar el password
        context.user_data['username'] = username 

        # Enviar mensaje con botones "Red" y "Fuerza y Control"
        keyboard = [
            [InlineKeyboardButton("Red", callback_data='red')],
            [InlineKeyboardButton("Fuerza y Control", callback_data='fuerza_y_control')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("Autenticación exitosa. Selecciona el tipo de equipo que deseas consultar:", reply_markup=reply_markup)
        
        return AREA_SELECTION
    
    except Exception as e:
        await update.message.reply_text(f"Error: {str(e)}. Intenta de nuevo.")
        return ConversationHandler.END  # Termina la conversación

async def handle_area_selection(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    area = query.data

    context.user_data['area'] = area

    if area == 'red':
        await query.message.reply_text("Seleccionaste el área Red")
    elif area == 'fuerza_y_control':
        await query.message.reply_text("Seleccionaste el área Fuerza y control")
    else:
        await query.message.reply_text("Área no válida")
        return

    # Continuar el flujo solicitando el nombre del host
    await query.message.reply_text("Ingrese el nombre del host que deseas evaluar:")
    return HOST_SELECTION

# Maneja la selección del host
async def handle_host_selection(update: Update, context: CallbackContext):
    # Verifica si el update viene de un mensaje de texto o de un CallbackQuery
    if update.message:
        host_name = update.message.text.strip()  # Obtener y limpiar el texto ingresado
    else:
        await update.callback_query.answer("No se recibió texto válido.")
        return

    auth_token = context.user_data.get('auth_token')

    if not auth_token:
        await update.message.reply_text("Error: no estás autenticado.")
        return

    matched_hosts = search_host_by_name(auth_token, host_name)

    if matched_hosts:
        keyboard = [
            [InlineKeyboardButton(host['name'], callback_data=f"host_{host['hostid']}")] for host in matched_hosts
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("Hosts encontrados:", reply_markup=reply_markup)
    else:
        await update.message.reply_text("No se encontraron hosts que coincidan.")


# Maneja la selección de las opciones principales
async def handle_primary_option_selection(update: Update, context: CallbackContext) -> None:
    if update.callback_query:
        query = update.callback_query
        option = query.data
        context.user_data['selected_option'] = option
        await show_secondary_options(update, context)  # Función que debe definir opciones secundarias

# Maneja la selección de las subcategorías (Interfaces o General)
async def handle_secondary_option_selection(update: Update, context: CallbackContext) -> None:
    username = context.user_data.get('username')
    password = context.user_data.get('password')

    if update.callback_query:
        query = update.callback_query
        secondary_option = query.data
        context.user_data['secondary_option'] = secondary_option

        # Aquí va la lógica específica para manejar opciones según el área
        if context.user_data['area'] == 'red':
            if context.user_data['selected_option'] == 'problems':            
                if secondary_option == 'interfaces':
                    await query.message.reply_text('Buscando problemas relacionados con "Interface"...')
                    await process_problems(update, context, 'link down', 'saturated')
                elif secondary_option == 'general':
                    await query.message.reply_text('Buscando problemas relacionados con "ICMP"...')
                    await process_problems(update, context, 'Unavailable by ICMP ping')
            elif context.user_data['selected_option'] == 'graphs':
                if secondary_option == 'interfaces':
                    await query.message.reply_text('Por favor, ingresa una palabra clave de la interfaz que deseas ver para optimizar la búsqueda:')
                    return  
                elif secondary_option == 'general':
                    await query.message.reply_text('Buscando gráficas relacionadas con "ICMP"...')
                    await process_graphs(update, context, 'ICMP')

        elif context.user_data['area'] == 'fuerza_y_control':
            if context.user_data['selected_option'] == 'problems':            
                if secondary_option == 'energia':
                    await query.message.reply_text('Buscando problemas relacionados con "Energia"...')
                    await process_problems(update, context, 'voltaje', 'descarga', 'corriente', 'falla ac')
                elif secondary_option == 'general':
                    await query.message.reply_text('Buscando problemas relacionados con "ICMP"...')
                    await process_problems(update, context, 'ICMP')
                elif secondary_option == 'sensores':
                    await query.message.reply_text('Buscando problemas relacionados con "Sensores"...')
                    await process_problems(update, context, 'temperatura', 'puerta abierta')
            elif context.user_data['selected_option'] == 'graphs':
                if secondary_option == 'energia':
                    await query.message.reply_text('Buscando gráficas relacionadas con "Energia"...')
                    await process_graphs(update, context, 'voltaje', 'temperatura', 'corriente', 'ac') 
                elif secondary_option == 'general':
                    await query.message.reply_text('Buscando gráficas relacionadas con "ICMP"...')
                    await process_graphs(update, context, 'ICMP')

# Muestra opciones después de la selección principal
async def show_secondary_options(update: Update, context: CallbackContext):
    if context.user_data['area'] == 'red':
        keyboard = [
            [InlineKeyboardButton("Interfaces", callback_data='interfaces')],
            [InlineKeyboardButton("General", callback_data='general')]
        ]
    elif context.user_data['area'] == 'fuerza_y_control':
        if context.user_data['selected_option'] == 'problems':
            keyboard = [
                [InlineKeyboardButton("Energia", callback_data='energia')],
                [InlineKeyboardButton("General", callback_data='general')],
                [InlineKeyboardButton("Sensores", callback_data='sensores')]
            ]
        elif context.user_data['selected_option'] == 'graphs':
            keyboard = [
                [InlineKeyboardButton("Energia", callback_data='energia')],
                [InlineKeyboardButton("General", callback_data='general')]
            ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    if update.callback_query:
        await update.callback_query.message.reply_text("Selecciona los tipos de datos que deseas consultar:", reply_markup=reply_markup)


# Maneja la selección de una gráfica o ítem y envía la imagen correspondiente
async def handle_graph_item_selection(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    data = query.data

    username = context.user_data.get('username')
    password = context.user_data.get('password')

    if not username or not password:
        await query.message.reply_text("Error: credenciales no encontradas.")
        return

    auth_token = await zabbix_login(username, password)
    if not auth_token:
        await query.message.reply_text("Error en la autenticación de Zabbix.")
        return

    # Obtener el host_id almacenado
    host_id = context.user_data.get('host_id')

    # Identifica el tipo de selección
    if data.startswith("graph_"):
        graph_id = data.split("_")[1]
        graph = get_graphs(auth_token, host_id, filter_name=None)
        graph = next((g for g in graph if g['graphid'] == graph_id), None)

        if graph:
            if "Network traffic" in graph['name']:
                url = generate_graph_url(graph_id=graph_id, chart_type="chart2.php")
            else:
                url = generate_graph_url(graph_id=graph_id)
            try:
                image = download_image(url)
                await query.message.reply_photo(photo=image, caption=graph['name'])
            except Exception as e:
                await query.message.reply_text(f"Error al descargar la imagen para la gráfica: {graph['name']} - {e}")
        else:
            await query.message.reply_text("No se encontró la gráfica seleccionada.")

    elif data.startswith("item_"):
        item_id = data.split("_")[1]
        item = get_items(auth_token, host_id, filter_name=None)
        item = next((i for i in item if i['itemid'] == item_id), None)

        if item:
            if "Network Traffic" in item['name']:
                url = generate_graph_url(item_id=item_id, chart_type="chart2.php")
            else:
                url = generate_graph_url(item_id=item_id)
            try:
                image = download_image(url)
                await query.message.reply_photo(photo=image, caption=item['name'])
            except Exception as e:
                await query.message.reply_text(f"Error al descargar la imagen para el ítem: {item['name']} - {e}")
        else:
            await query.message.reply_text("No se encontró el ítem seleccionado.")


