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
    get_dashboard_stats
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
