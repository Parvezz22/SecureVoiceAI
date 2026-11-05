from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

import os
import shutil
import tempfile

from authentication_engine import (
    load_model,
    authenticate_voice
)

from enrollment_engine import enroll_voice

from database import (
    initialize_database,
    log_authentication,
    get_dashboard_stats,
    get_authentication_history,
    get_all_users
)

# ============================================================
# INITIALIZE FASTAPI
# ============================================================

app = FastAPI(
    title="SecureVoiceAI",
    description="AI-powered Voice Authentication System",
    version="1.0"
)


# ============================================================
# SERVE STATIC FILES
# ============================================================

app.mount(
    "/static",
    StaticFiles(directory="static"),
    name="static"
)


# ============================================================
# LOAD ECAPA MODEL
# ============================================================

verification_model = None


@app.on_event("startup")
def load_speaker_model():

    global verification_model

    initialize_database()

    verification_model = load_model()


# ============================================================
# HOME PAGE
# ============================================================

@app.get("/")
def home():

    return FileResponse("templates/index.html")

@app.get("/history-page")
def history_page():
    return FileResponse("templates/history.html")

@app.get("/users-page")
def users_page():
    return FileResponse("templates/users.html")


# ============================================================
# ENROLLMENT PAGE
# ============================================================

@app.get("/enroll-page")
def enrollment_page():

    return FileResponse("templates/enroll.html")


# ============================================================
# AUTHENTICATION PAGE
# ============================================================

@app.get("/authenticate-page")
def authentication_page():

    return FileResponse("templates/authenticate.html")


# ============================================================
# HEALTH CHECK
# ============================================================

@app.get("/health")
def health():

    return {
        "status": "healthy",
        "model_loaded": verification_model is not None
    }


# ============================================================
# VOICE AUTHENTICATION API
# ============================================================

@app.post("/authenticate")
async def authenticate_user(

    username: str = Form(...),
    voice: UploadFile = File(...)

):

    if verification_model is None:

        raise HTTPException(
            status_code=503,
            detail="Speaker model is not loaded"
        )

    temp_path = None

    try:

        # Save uploaded audio temporarily

        suffix = os.path.splitext(
            voice.filename or ""
        )[1] or ".wav"

        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=suffix
        ) as temp_file:

            temp_path = temp_file.name

            shutil.copyfileobj(
                voice.file,
                temp_file
            )

        # Authenticate voice

        result = authenticate_voice(
            username,
            temp_path,
            verification_model
        )

        # Save authentication attempt in database

        log_authentication(result)

        return result

    except FileNotFoundError as e:

        raise HTTPException(
            status_code=404,
            detail=str(e)
        )

    except Exception as e:

        raise HTTPException(
            status_code=400,
            detail=str(e)
        )

    finally:

        if temp_path and os.path.exists(temp_path):

            os.remove(temp_path)

        await voice.close()


# ============================================================
# VOICE ENROLLMENT API
# ============================================================

@app.post("/enroll")
async def enroll_user(

    username: str = Form(...),
    voice: UploadFile = File(...)

):

    if verification_model is None:

        raise HTTPException(
            status_code=503,
            detail="Speaker model is not loaded"
        )

    temp_path = None

    try:

        # Save uploaded audio temporarily

        suffix = os.path.splitext(
            voice.filename or ""
        )[1] or ".wav"

        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=suffix
        ) as temp_file:

            temp_path = temp_file.name

            shutil.copyfileobj(
                voice.file,
                temp_file
            )

        # Enroll user

        result = enroll_voice(
            username,
            temp_path,
            verification_model
        )

        return result

    except FileExistsError as e:

        raise HTTPException(
            status_code=409,
            detail=str(e)
        )

    except FileNotFoundError as e:

        raise HTTPException(
            status_code=404,
            detail=str(e)
        )

    except ValueError as e:

        raise HTTPException(
            status_code=400,
            detail=str(e)
        )

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

    finally:

        if temp_path and os.path.exists(temp_path):

            os.remove(temp_path)

        await voice.close()

# ============================================================
# DASHBOARD STATISTICS API
# ============================================================

@app.get("/dashboard-stats")
def dashboard_stats():

    try:

        stats = get_dashboard_stats()

        return stats

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )
# GET COMPLETE AUTHENTICATION HISTORY

@app.get("/authentication-history")
def authentication_history(
    username: str = None,
    status: str = None
):

    try:
        if status and status.upper() not in ["SUCCESS", "FAILED"]:
            raise HTTPException(
                status_code=400,
                detail="Status must be SUCCESS or FAILED"
            )

        history = get_authentication_history(
            username=username,
            status=status
        )

        return {
            "total_records": len(history),
            "history": history
        }

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# GET ALL REGISTERED USERS

@app.get("/users")
def registered_users():

    try:
        users = get_all_users()

        return {
            "total_users": len(users),
            "users": users
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))