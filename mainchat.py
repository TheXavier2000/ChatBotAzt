from telegram.ext import Application, CommandHandler, MessageHandler, filters, ConversationHandler
from auth import zabbix_login
from bot import start, handle_username, ask_interfaces, handle_interface_selection, handle_password, handle_graph_choice2, ask_choice, handle_choice, handle_graph_choice, handle_selected_host, ask_new_search, handle_host_name, handle_new_search, ask_host_type, handle_host_type, stop, menu, help, handle_search_type, ask_location_name
from telegram import ReplyKeyboardMarkup

# Definir los estados de la conversación
USERNAME, PASSWORD, CHOICE, NEW_SEARCH, HOST_TYPE, HOST_NAME, SELECTED_HOST, GRAPH_CHOICE, GRAPH_CHOICE2, GRAPH_CHOICE3, GRAPH_CHOICE4, LOCATION_NAME, SEARCH_TYPE = range(13)

def main():
    application = Application.builder().token('7319075472:AAGHNFfervCfH3lt5mblsMoDgjtNQwydlwo').build()

    # Definir manejadores
    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler('start', start),
            CommandHandler('menu', menu),
            CommandHandler('help', help)
        ],
        states={
            USERNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_username)],
            PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_password)],
            HOST_TYPE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_host_type)],
            GRAPH_CHOICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_graph_choice)],
            CHOICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_choice)],  # La elección de buscar por problemas o gráficas
            HOST_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_host_name)],
            SELECTED_HOST: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_selected_host)],
            GRAPH_CHOICE2: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_graph_choice2)],
            NEW_SEARCH: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_new_search)],
            GRAPH_CHOICE3: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_interfaces)],
            GRAPH_CHOICE4: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_interface_selection)],
            SEARCH_TYPE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_search_type)],  # Elección entre Host o Ubicación
            LOCATION_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_location_name)],  # Función para preguntar por la ubicación
        },
        fallbacks=[
            CommandHandler('stop', stop),
            CommandHandler('menu', menu),
            CommandHandler('help', help)  # Manejar /menu desde cualquier estado
        ],
    )

    application.add_handler(conv_handler)

    # Ejecutar el bot
    application.run_polling()

if __name__ == '__main__':
    main()
