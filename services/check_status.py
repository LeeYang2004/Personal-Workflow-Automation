from fastapi import APIRouter

router = APIRouter()

# TODO: Check the status of the application
@router.get("/status")
def status():
    return {"status": "ok"}