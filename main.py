import asyncio
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, 
    CommandHandler, 
    ConversationHandler, 
    CallbackQueryHandler, 
    MessageHandler, 
    filters  # Cambia aquí a 'filters'
)
from handlers import (
    start, 
    handle_username, 
    handle_password, 
    handle_area_selection, 
    handle_host_selection, 
    handle_primary_option_selection, 
    handle_secondary_option_selection, 
    handle_graph_item_selection
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
from config import TELEGRAM_TOKEN
from zabbix_api import (
    zabbix_login,
    search_host_by_name,
    get_problems,
    get_graphs,
    get_items,
    generate_graph_url
)
from utils import download_graph_image

def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    # Configuración de los handlers
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            USERNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_username)],
            PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_password)],
            AREA_SELECTION: [CallbackQueryHandler(handle_area_selection)],
            HOST_SELECTION: [CallbackQueryHandler(handle_host_selection)],
            PRIMARY_OPTION_SELECTION: [CallbackQueryHandler(handle_primary_option_selection)],
            SECONDARY_OPTION_SELECTION: [CallbackQueryHandler(handle_secondary_option_selection)],
            GRAPH_ITEM_SELECTION: [CallbackQueryHandler(handle_graph_item_selection)],
        },
        fallbacks=[],
    )

    app.add_handler(conv_handler)
    app.run_polling()

if __name__ == '__main__':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    main()
