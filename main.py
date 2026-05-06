import uvicorn
import logging
from fastapi import FastAPI
from core.logger import setup_logger
from services.google_calendar import calendar_service
from services.notion import upsert_notion_page
from core.routers import ROUTERS

def run():    
    events = calendar_service()
    
    if not events:
        logger.info("No events found.")
        return
    
    for event in events:
        upsert_notion_page(event)

    # uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

if __name__ == "__main__":
    # Suppress verbose logging from external libraries
    logging.getLogger("google.auth").setLevel(logging.ERROR)
    logging.getLogger("googleapiclient").setLevel(logging.ERROR)
    logging.getLogger("urllib3").setLevel(logging.ERROR)

    # Initialize FastAPI
    app = FastAPI()

    # Register router
    for router in ROUTERS:
        app.include_router(router)

    # Set up logger
    logger = setup_logger()

    run()