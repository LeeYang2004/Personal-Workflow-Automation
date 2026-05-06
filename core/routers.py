from services.check_status import router as check_status_router
from services.google_calendar import router as calendar_router
from services.notion import router as notion_router

ROUTERS = [
    check_status_router,
    calendar_router,
    notion_router
]