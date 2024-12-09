from telegram import Update, ForceReply, ReplyKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from auth import zabbix_login
from search import search_host_by_name
from problems import get_problems
from problems import get_graphs
from problems import get_inter1
from problems import get_inter2
from problems import get_inter3
from problems import get_inter_cliente
from problems import generate_graph_url
from problems import download_image
import requests
from telegram.ext import CallbackContext
from telegram import ForceReply
import json

USERNAME, PASSWORD, CHOICE, NEW_SEARCH, HOST_TYPE, HOST_NAME, SELECTED_HOST,GRAPH_CHOICE,GRAPH_CHOICE2,GRAPH_CHOICE3,GRAPH_CHOICE4 = range(11)

# Definir los estados de la conversación
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.effective_user
    await update.message.reply_text(
        f"¡Hola {user.first_name}! Soy AzTI-NOC🤖 tu asistente para consultas de datos sobre hosts. 🖥️\n\n"
        "Conmigo, puedes:\n\n"
        "📊 Generar gráficas sobre el rendimiento de tus equipos.\n"
        "🔍 Consultar información detallada sobre hosts específicos.\n"
        "⚠️ Identificar y analizar problemas detectados.\n\n"
        "Para comenzar a usar el Bot por favor ingresa tu nombre de usuario y tu contraseña ¡Estoy listo para ayudarte! ✅"
    )
    reply_markup=ForceReply(selective=True),
    return USERNAME

async def handle_username(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    username = update.message.text
    context.user_data['username'] = username  # Guardar el nombre de usuario

    await update.message.reply_text("Por favor ingresa tu contraseña en zabbix.",reply_markup=ForceReply(selective=True))

    return PASSWORD

# 1. Función de autenticación exitosa
async def handle_password(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    
    password = update.message.text  # Aquí obtenemos la contraseña del usuario
    
    # Obtener el ID único del mensaje (el que contiene la contraseña)
    message_id = update.message.message_id  # ID del mensaje que contiene la contraseña
    print(f"Mensaje con ID {message_id} recibido. Intentando eliminarlo.")
    
    try:
        # Eliminar el mensaje con la contraseña usando el ID único
        update.message.delete()  # Borra el mensaje del usuario que contiene la contraseña
        print(f"Mensaje con ID {message_id} borrado correctamente.")
    except Exception as e:
        print(f"Error al borrar el mensaje: {e}")
    username = context.user_data.get('username')
    
    try:
        # Intentar la autenticación
        auth_token = await zabbix_login(username, password)  # Llama a la función de autenticación
        await update.message.reply_text("Autenticación exitosa. ¡Bienvenido!")
        context.user_data['auth_token'] = auth_token  # Guardar el token de autenticación

        # Primero preguntar por el tipo de host, luego la opción de búsqueda
        return await ask_host_type(update, context) # tipo de host

    except Exception as e:
        await update.message.reply_text(f"Error: {str(e)}. La conversación se ha terminado.")
        return await stop(update, context)  # Termina la conversación

# 2. Función para preguntar por el tipo de host
async def ask_host_type(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    keyboard = [["Equipos Networking", "Clientes", "Rectificadores","Plantas"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)

    await update.message.reply_text(
        "¿Qué tipo deseas buscar? (Si tienes dudas sobre los comandos usa /help)\n\n",
        reply_markup=reply_markup
    )
    return HOST_TYPE  # Cambia al estado de tipo de host

# 3. Manejo de la respuesta sobre el tipo de host
async def handle_host_type(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    host_type = update.message.text
    context.user_data['host_type'] = host_type  # Guardar el tipo de host seleccionado

    # Validación del tipo de host
    if host_type not in ["Equipos Networking", "Clientes", "Rectificadores","Plantas"]:
        await update.message.reply_text("Consulta no válida, inténtelo de nuevo.")
        return await ask_host_type(update, context)  # Volver a preguntar por el tipo de host
    
    await update.message.reply_text(f"Has elegido buscar: {host_type}.")

    # Ahora que el tipo de host ha sido seleccionado, preguntar por la opción de búsqueda
    return await ask_choice(update, context)  # Ahora se pregunta por la opción de búsqueda (Buscar host o Buscar gráficas)

# 4. Función para preguntar por la opción de búsqueda
async def ask_choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    keyboard = [["Buscar Problemas", "Buscar gráficas"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)

    await update.message.reply_text(
        "Por favor, elige una opción:",
        reply_markup=reply_markup
    )
    return CHOICE  # Cambia al estado de elegir opción de búsqueda

# 5. Manejo de la elección de "Buscar host" o "Buscar gráficas"
async def handle_choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    choice = update.message.text
    context.user_data['choice'] = choice  # Guardar la elección

    if choice not in ["Buscar Problemas", "Buscar gráficas"]:
        await update.message.reply_text("Consulta no válida, inténtelo de nuevo.")
        return await ask_choice(update, context)  # Volver a preguntar por la opción

    if choice == "Buscar Problemas":
        
        await update.message.reply_text("Has elegido buscar Problemas.")
        return await ask_host_name(update, context)  # Preguntar por el nombre del host

    elif choice == "Buscar gráficas":
        await update.message.reply_text("Has elegido buscar gráficas.")
        return await ask_graph_choice(update, context)  # Preguntar por el nombre del host (gráficas)
    

async def ask_graph_choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    host_type = context.user_data.get('host_type')
    
    
    if host_type == "Clientes":
            # Preguntar por el tipo de gráfica para Clientes
            keyboard = [["Estado General", "Interfaces"]]
            reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
            await update.message.reply_text(
                "¿Qué tipo de gráfica deseas ver para Clientes?",
                reply_markup=reply_markup
            )
            return GRAPH_CHOICE  # Redirigimos al estado para la selección de gráficos
    elif host_type == "Equipos Networking" :
            # Preguntar por el tipo de gráfica para Clientes
            keyboard = [["Estado General", "Interfaces"]]
            reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
            await update.message.reply_text(
                "¿Qué tipo de gráfica deseas ver ?",
                reply_markup=reply_markup
            )
            return GRAPH_CHOICE  # Redirigimos al estado para la selección de gráficos
    
    elif host_type == "Rectificadores":
            # Preguntar por el tipo de gráfica para Rectificadores
            keyboard = [["Estado General", "Energía"]]
            reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
            await update.message.reply_text(
                "¿Qué tipo de gráfica deseas ver para Rectificadores?",
                reply_markup=reply_markup
            )
            return GRAPH_CHOICE # Redirigimos al estado para la selección de gráficos 
    
    elif host_type == "Plantas":
            # Preguntar por el tipo de gráfica para Rectificadores
            keyboard = [["Estado General", "Energía"]]
            reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
            await update.message.reply_text(
                "¿Qué tipo de gráfica deseas ver ?",
                reply_markup=reply_markup
            )
            return GRAPH_CHOICE # Redirigimos al estado para la selección de gráficos 
     
async def ask_graph_choice2(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
           # Preguntar por el tipo de gráfica para Rectificadores
    keyboard = [["Interface Eth", "Interface Gigabit","LAG"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
    await update.message.reply_text(
     "¿Qué tipo de gráfica deseas ver?",
     reply_markup=reply_markup
            )
    return GRAPH_CHOICE2 # Redirigimos al estado para la selección de gráficos 
# 8. Manejo de la selección del tipo de gráfica
async def handle_graph_choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    graph_choice = update.message.text
    graph_choice2 = update.message.text
    context.user_data['graph_choice'] = graph_choice  # Guardar la elección de gráfica
    context.user_data['graph_choice2'] = graph_choice2 
    host_type = context.user_data.get('host_type')  # Recuperar el tipo de host

    if graph_choice not in ["Estado General", "Interfaces", "Energía"]:
        await update.message.reply_text("Consulta no válida, inténtelo de nuevo.")
        return await handle_choice(update, context)  # Volver a preguntar por el tipo de gráfica

    if graph_choice == "Interfaces":
        if host_type == "Clientes":
            # Salta las opciones de interfaz y va directo a preguntar el nombre del host
            return await ask_host_name(update, context)
        else:
            await update.message.reply_text("¿Qué tipo de interfaz deseas buscar?")
            return await ask_graph_choice2(update, context)  # Preguntar por el tipo de interfaz
    else:
        context.user_data['graph_choice'] = graph_choice  # Guardar la elección de gráfica
        return await ask_host_name(update, context)  # Preguntar por el nombre del host


# 8. Manejo de la selección del tipo de gráfica
async def handle_graph_choice2(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    graph_choice2 = update.message.text
    context.user_data['graph_choice2'] = graph_choice2  # Guardar la elección de gráfica
    host_type = context.user_data.get('host_type')  # Recuperar el tipo de host

    # Si el host es de tipo Clientes, ir directamente a preguntar el nombre del host
    if host_type == "Clientes":
        return await ask_host_name(update, context)

    # Validar que la elección esté entre las opciones permitidas
    if graph_choice2 not in ["Interface Eth", "Interface Gigabit", "LAG"]:
        await update.message.reply_text("Consulta no válida, inténtelo de nuevo.")
        return await handle_choice(update, context)  # Volver a preguntar por el tipo de gráfica

    # Convertir la elección en la representación interna
    if graph_choice2 == "Interface Eth":
        graph_choice2 = "Eth"
    elif graph_choice2 == "Interface Gigabit":
        graph_choice2 = "Gigabit"
    elif graph_choice2 == "LAG":
        graph_choice2 = "LAG"

    # Guardar la elección actualizada y preguntar por el nombre del host
    context.user_data['graph_choice2'] = graph_choice2
    return await ask_host_name(update, context)  # Preguntar por el nombre del host

    


# 6. Función para preguntar el nombre del host
async def ask_host_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Por favor, ingresa el nombre o el nemónico del equipo que deseas consultar.")
    return HOST_NAME  # Cambia al estado para ingresar el nombre del host

# 7. Manejo del nombre del host y búsqueda
async def handle_host_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    host_name = update.message.text
    auth_token = context.user_data.get('auth_token')
    host_type = context.user_data.get('host_type')  # Obtén el tipo de host
    
    # Busca los hosts que coinciden con el nombre ingresado y el tipo de host
    hosts = await search_host_by_name(auth_token, host_name, host_type)  # Asegúrate de pasar el host_type

    if not hosts:
        await update.message.reply_text("No se encontraron hosts con ese nombre. Consulta no válida, inténtelo de nuevo.")
        return await ask_host_type(update, context)  # Volver a preguntar por el tipo de host

    if hosts:
        # Si se encontraron hosts, guarda la selección del usuario y pide elegir un host
        context.user_data['hosts'] = hosts  # Guarda los hosts encontrados

        # Crear un teclado con los nombres de los hosts
        keyboard = [[host['name']] for host in hosts]  # Cada nombre en su propia lista
        reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)

        await update.message.reply_text("Selecciona un host:", reply_markup=reply_markup)
        return SELECTED_HOST  # Asegúrate de que SELECTED_HOST esté definido

# 8. Manejo de la selección del host
async def handle_selected_host(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    choice = context.user_data.get('choice')
    selected_host = update.message.text
    hosts = context.user_data.get('hosts', [])
    host_type = context.user_data.get('host_type')
    

    # Validar que el host seleccionado esté en la lista de hosts encontrados
    if not any(host['name'] == selected_host for host in hosts):
        await update.message.reply_text("No seleccionaste un host válido. Consulta no válida, inténtelo de nuevo.")
        return await handle_host_name(update, context)  # Volver a pedir el nombre del host

    if any(host['name'] == selected_host for host in hosts):
        auth_token = context.user_data.get('auth_token')
        host_id = next(host['hostid'] for host in hosts if host['name'] == selected_host)
        context.user_data['host_id'] = host_id
        graphs = []

        # Obtener problemas o gráficos del host
        if choice == "Buscar Problemas":
            
            problems = get_problems(auth_token, host_id, selected_host)
            if problems:
                problems_list = "\n".join([f"Problema: {problem['name']}" for problem in problems])
                await update.message.reply_text(f"Problemas encontrados:\n{problems_list}")
            else:
                await update.message.reply_text("No hay problemas con este equipo.")

            await ask_new_search(update, context)
            return NEW_SEARCH

        elif choice == "Buscar gráficas":
            graph_choice = context.user_data['graph_choice']
            graph_choice2 = context.user_data['graph_choice2']
            # Obtener gráficas para el host
            if host_type == "Rectificadores":
                if graph_choice == "Energía":
                  tipo = ["fase", "voltaje", "temperatura"]
                elif graph_choice ==  "Estado General":
                    tipo = ["ICMP"]  # Esto ahora es una lista, igual que en el caso de "Rectificadores"
            elif host_type == "Plantas":
                if graph_choice == "Energía":
                  tipo = ["Motor", "Aceite", "Combustible","Tension"]
                elif graph_choice ==  "Estado General":
                    tipo = ["ICMP"]  # Esto ahora es una lista, igual que en el caso de "Rectificadores"
                 
            elif host_type == "Equipos Networking":
                if graph_choice ==  "Estado General":
                   tipo = ["ICMP"]  # Esto ahora es una lista, igual que en el caso de s"
                elif graph_choice == "Interfaces": 
                    graph_choice4=graph_choice2
                    context.user_data['graph_choice4'] = graph_choice4  
                    #await update.message.reply_text("selecciona una interfaz.")
                    return  await ask_interfaces(update, context)


            elif host_type == "Clientes":
                    if graph_choice ==  "Estado General":
                      tipo = ["ICMP"]  # Esto ahora es una lista, igual que en el caso de "Rectificadores"
                    elif graph_choice == "Interfaces": 
                     graph_choice4=graph_choice2
                     context.user_data['graph_choice4'] = graph_choice4  
                     #await update.message.reply_text("selecciona una interfaz.")
                     return  await ask_interfaces(update, context)

            # Recorremos cada tipo en la lista
            for item_tipo in tipo:
                graphs = get_graphs(auth_token, host_id, item_tipo)  # Usamos item_tipo para cada valor
                if graphs:
                    await process_graphs(update, context, graphs)  # Procesar las gráficas encontradas
                else:
                    await update.message.reply_text("No se encontraron gráficas para este host.")  # Respuesta si no hay gráficas

            await ask_new_search(update, context)
            return NEW_SEARCH
    else:
        await update.message.reply_text("No seleccionaste un host válido.")
        return CHOICE

# 9. Procesar gráficas (si el usuario elige esta opción)
async def ask_interfaces(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    # Recupera los datos necesarios
    graph_choice4 = context.user_data.get('graph_choice4')
    auth_token = context.user_data.get('auth_token')
    host_id = context.user_data.get('host_id')
    host_type = context.user_data.get('host_type')  # Identificar el tipo de host
    inter = []

    # Verificar el tipo de host y aplicar el filtro correspondiente
    if host_type == "Clientes":
        # Filtro específico para Clientes
        inter = get_inter_cliente(auth_token, host_id)
        context.user_data['inter'] = inter

    elif graph_choice4 == "Gigabit":
        inter = get_inter1(auth_token, host_id)
        context.user_data['inter'] = inter

    elif graph_choice4 == "Eth":
        inter = get_inter2(auth_token, host_id)
        context.user_data['inter'] = inter

    elif graph_choice4 == "LAG":
        inter = get_inter3(auth_token, host_id)
        context.user_data['inter'] = inter

    # Validar si la lista de interfaces está vacía
    if not inter:
        print("La lista de interfaces está vacía.")  
        await update.message.reply_text("No se encontraron gráficas para las interfaces seleccionadas.")
        await ask_new_search(update, context)
        return NEW_SEARCH

    # Si hay interfaces disponibles, mostrar opciones al usuario
    keyboard = [[interface] for interface in inter.keys()]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
    await update.message.reply_text("Selecciona una Interfaz:", reply_markup=reply_markup)

    # Estado de espera para la selección del usuario
    return GRAPH_CHOICE4


async def handle_interface_selection(update: Update, context: CallbackContext) -> int:
    inter = context.user_data.get('inter', [])
    
    selected_interface = update.message.text  # El nombre de la interfaz seleccionada por el usuario

    graphid = inter[selected_interface]
    #if not any(inter['In'] == selected_interface for inter in inter):
    if selected_interface not in inter:
        await update.message.reply_text(" Consulta no válida, inténtelo de nuevo.")
        return await ask_interfaces(update, context)  # Volver a pedir el nombre del host

    #if any(inter['name'] == selected_interface for inter in inter):
    if selected_interface in inter:
        auth_token = context.user_data.get('auth_token')
        message_target = update.callback_query.message if update.callback_query else update.message
        #valid_interface = next((interface for interface in inter if interface['name'] == selected_interface), None)
        valid_interface = inter.get(selected_interface, None)
        print("la:",valid_interface,"gr:",graphid)
        # Si la interfaz es válida, guarda la selección
        context.user_data['selected_interface'] = valid_interface
        await update.message.reply_text(f"Has seleccionado la interfaz {selected_interface}.")
        url = f"http://10.144.2.194/zabbix/chart2.php?graphid={graphid}&from=now-12h&to=now&height=201&width=1188&profileIdx=web.charts.filter"
 
              #url = f"http://10.144.2.194/zabbix/chart2.php?graphid[]={graphid}&from=now-12h&to=now&height=201&width=1188&profileIdx=web.charts.filter"
        try:
            image = download_image(url)
            await message_target.reply_photo(photo=image, caption=selected_interface)
        except Exception as e:
            await message_target.reply_text(f"Error al descargar la imagen para el ítem: {['name']} - {e}")
                
        await ask_new_search(update, context)
        return NEW_SEARCH
    else:
        await update.message.reply_text("No seleccionaste un host válido.")
        return  await ask_interfaces(update, context)
    # Aquí continuarías con la lógica posterior, como obtener las gráficas, etc.
    #return await ask_new_search(update, context)  # O continuar con la siguiente acción según el flujo


    
async def process_graphs(update: Update, context: CallbackContext, graphs):
    if not graphs:
        await update.message.reply_text("No se encontraron gráficas para mostrar.")
        return
    message_target = update.callback_query.message if update.callback_query else update.message
    for graph in graphs:
        if "Network Traffic" in graph['name']:
            url = generate_graph_url(item_id=graph['itemid'], chart_type="chart2.php")
        else:
            url = generate_graph_url(item_id=graph['itemid'])
        try:
            image = download_image(url)
            await message_target.reply_photo(photo=image, caption=graph['name'])
        except Exception as e:
            await message_target.reply_text(f"Error al descargar la imagen para el ítem: {graph['name']} - {e}")

# 10. Preguntar por una nueva búsqueda
async def ask_new_search(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = [["Sí", "No"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)

    await update.message.reply_text(
        "¿Deseas hacer una nueva búsqueda?",
        reply_markup=reply_markup
    )

# 11. Manejar la respuesta sobre si hacer una nueva búsqueda
async def handle_new_search(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    answer = update.message.text
    if answer == "Sí":
        return await ask_host_type(update, context)  # Regresar a preguntar por la opción
    elif answer == "No":
        await update.message.reply_text("Gracias por usar el bot. La conversación ha finalizado.")
        return ConversationHandler.END  # Termina la conversación
    else:
        await update.message.reply_text("Respuesta no válida. Por favor elige 'Sí' o 'No'.")
        await ask_new_search(update, context)
        return NEW_SEARCH  # Permitir elegir de nuevo

async def stop (update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("La conversación ha sido detenida.")
    return ConversationHandler.END

# 12. Manejar la función del menu
async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Maneja el comando /menu para regresar al menú principal."""
    keyboard = [["Equipos Networking", "Clientes", "Rectificadores","Plantas"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)

    await update.message.reply_text(
        "¿Qué tipo deseas buscar?\n\n (Si en algún momento tienes dudas de los comandos usa /help)\n\n",
        reply_markup=reply_markup
    )
    return HOST_TYPE  # Cambia al estado de tipo de host

# 12. Manejar la función del help
async def help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    help_message = (
         f"¡Hola {user.first_name}. Aquí están los comandos que puedes usar:\n\n"
    "✨ **Comandos principales**:\n"
        "🔹 `/start` - Inicia la conversación desde el principio. ¡Empecemos desde cero! 🌟\n"
        "🔹 `/menu` - Accede al menú principal de opciones para consultar información sobre tus hosts y mucho más. 🖥️\n"
        "🔹 `/stop` - Detiene la conversación actual (no el bot completo). Si necesitas terminar, este es el comando. ❌\n"
        "🔹 `/help` - Muestra este mensaje con todos los comandos disponibles. ¡Aquí siempre puedes volver! ❓\n\n"
        "🚀 **¿Qué puedo hacer por ti?**\n"
        "📊 Consultar **gráficas** sobre el rendimiento de tus equipos.\n"
        "🔍 Obtener **información detallada** sobre tus hosts.\n"
        "⚠️ Detectar y analizar **problemas** en tu red o dispositivos.\n\n"
        "¡Usa estos comandos para comenzar y explorar lo que puedo hacer! 😎 ¡Estoy aquí para ayudarte! 💪"
    )

    await update.message.reply_text(help_message)
