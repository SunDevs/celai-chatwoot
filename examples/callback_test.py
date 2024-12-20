# LOAD ENV VARIABLES
import os
import time
import json
from loguru import logger as log
# Load .env variables
from dotenv import load_dotenv





load_dotenv()


# REMOVE THIS BLOCK IF YOU ARE USING THIS SCRIPT AS A TEMPLATE
# -------------------------------------------------------------
import sys
from pathlib import Path
# Add parent directory to path
path = Path(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(str(path.parents[0]))
# -------------------------------------------------------------

# Import Cel.ai modules
from cel.connectors.telegram import TelegramConnector
from cel.gateway.message_gateway import MessageGateway, StreamMode
from cel.assistants.macaw.macaw_assistant import MacawAssistant
from cel.prompt.prompt_template import PromptTemplate
from cel.assistants.request_context import RequestContext
from cel.gateway.http_callbacks import HttpCallbackProvider
from cel.gateway.model.conversation_lead import ConversationLead
from cel.gateway.model.message_gateway_context import MessageGatewayContext
from celai_chatwoot.connector.woo_connector import WootConnector


from datetime import datetime
date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# Setup prompt
prompt = """You are an AI Assistant called Jane.
Today: {date}
"""

callbacks = HttpCallbackProvider()



prompt_template = PromptTemplate(prompt, initial_state={
        # Today full date and time
        "date": date,
    })

ast = MacawAssistant(prompt=prompt_template, state={})



@ast.event('message')
async def handle_message(session, ctx: RequestContext):
    
    if ctx.message.text == "link":
        log.debug(f"Link request for:{ctx.lead.conversation_from.name}")
      
        async def handle_callback(lead: ConversationLead, data: dict):
            log.critical(f"Callback received from {lead} with data: {data}")
            await ctx.send_text_message("Thank you for completing the task with data: " + json.dumps(data)) 
            return {"saved": True}
        
        # Create a callback
        url = callbacks.create_callback(ctx.lead, 
                                        handle_callback, 
                                        ttl=20, 
                                        single_use=False)
        

        await ctx.send_link_message("Welcome, this is a link to complete the task", "Click here", url)
        return ctx.cancel_ai_response()

# Setup the Callback Provider
def on_startup(context: MessageGatewayContext):       
    callbacks.setup(context)


# Create the Message Gateway - This component is the core of the assistant
# It handles the communication between the assistant and the connectors
gateway = MessageGateway(
    assistant=ast,
    host="127.0.0.1", port=5004,
    on_startup=on_startup
)

# # For this example, we will use the Telegram connector
# conn = TelegramConnector(
#     token=os.environ.get("TELEGRAM_TOKEN"), 
#     stream_mode=StreamMode.FULL
# )
# # Register the connector with the gateway
# gateway.register_connector(conn)


# For this example, we will use the Telegram connector
conn = WootConnector(
    bot_name="Testing Ale Bot",
    access_key=os.environ.get("CHATWOOT_ACCESS_KEY"),
    account_id=os.environ.get("CHATWOOT_ACCOUNT_ID"),
    inbox_id=os.environ.get("CHATWOOT_INBOX_ID"),
    chatwoot_url=os.environ.get("CHATWOOT_URL"),
    bot_description="This is a test bot",
    stream_mode=StreamMode.FULL
)


# Register the connector with the gateway
gateway.register_connector(conn)

# Then start the gateway and begin processing messages
gateway.run(enable_ngrok=True)

