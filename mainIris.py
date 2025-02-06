from telegram.ext import Application, CommandHandler, MessageHandler, filters, ConversationHandler, ApplicationBuilder
from auth import zabbix_login
from telegram import BotCommand
import asyncio


from bot import (
    start, handle_username, ask_interfaces, handle_interface_selection,
    handle_password, handle_graph_choice2, ask_choice, handle_choice, 
    handle_graph_choice, handle_selected_host, ask_new_search, handle_host_name, 
    handle_new_search, ask_host_type, handle_host_type, stop, device_group, menu, list_incidents,help, handle_problemas1,handle_selected_equipo,

    handle_search_type, ask_location_name,process_selection, location_search, show_selected_location,handle_department_selection,handle_new_search1
)
from telegram import ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, CallbackContext
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup

# Definir los estados de la conversación
(
    USERNAME, PASSWORD, CHOICE, NEW_SEARCH, HOST_TYPE, HOST_NAME, 
    SELECTED_HOST, GRAPH_CHOICE, GRAPH_CHOICE2, GRAPH_CHOICE3, GRAPH_CHOICE4,  EQUIPO1,

    LOCATION_NAME, SEARCH_TYPE, SHOW_PROBLEMS, SELECTED_LOCATION,SELECTING_DEPARTMENT,NEW_SEARCH1, PROBLEMAS1,PROCESS_SELECTION1
) = range(20)





def main():
    #application = Application.builder().token('7319075472:AAGHNFfervCfH3lt5mblsMoDgjtNQwydlwo').build()#pruebas 
    application = Application.builder().token('7254640619:AAE_r6W7ajo5nb4lHLZWBLpT8h2MmQqHkMc').build() #principal
    


    # Definir el manejador de la conversación
    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler('start', start),
            CommandHandler('menu', menu),
            CommandHandler('device_group', device_group),
        #    CommandHandler('list_incidents', list_incidents),
            CommandHandler('help', help)
        ],
        states={
            # Manejo de autenticación
            USERNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_username)],
            PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_password)],
            
            # Manejo de problemas y gráficas
            HOST_TYPE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_host_type)],
            HOST_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_host_name)],
            SELECTED_HOST: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_selected_host)],
            GRAPH_CHOICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_graph_choice)],
            GRAPH_CHOICE2: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_graph_choice2)],
            GRAPH_CHOICE3: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_interfaces)],
            GRAPH_CHOICE4: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_interface_selection)],
            CHOICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_choice)],
            EQUIPO1: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_selected_equipo)],
            
            # Manejo de búsqueda
            NEW_SEARCH: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_new_search)],
            SEARCH_TYPE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_search_type)],
            
            # Manejo de búsqueda por ubicación
            LOCATION_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, location_search)],  
            SHOW_PROBLEMS: [MessageHandler(filters.TEXT & ~filters.COMMAND, location_search)],  
            SELECTED_LOCATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, show_selected_location)],  
            SELECTING_DEPARTMENT: [
                CallbackQueryHandler(handle_department_selection)
            ],
            
            NEW_SEARCH1: [
                CallbackQueryHandler(handle_new_search1, pattern='^(Sí|No)$')
            ],
            PROBLEMAS1: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_problemas1)],  
            PROCESS_SELECTION1: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_selection)],  
          
        },
        fallbacks=[
            CommandHandler('stop', stop),
            CommandHandler('device_group', device_group),
            CommandHandler('menu', menu),
        #    CommandHandler('list_incidents', list_incidents),
            CommandHandler('help', help)
        ],
    )

    application.add_handler(conv_handler)

    # Ejecutar el bot  
    #application.add_handler(CallbackQueryHandler(handle_new_search1, pattern='^(Sí|No)$'))
    #application.add_handler(CallbackQueryHandler(handle_department_selection))
   
    #application.add_handler(MessageHandler(filters.Text(["Sí", "No"]), handle_new_search1))
    application.run_polling()
    

if __name__ == '__main__':
    main()