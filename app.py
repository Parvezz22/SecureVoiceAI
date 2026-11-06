import os
import shutil
import tempfile

from pathlib import Path

from fastapi import (
    FastAPI,
    UploadFile,
    File,
    Form,
    HTTPException,
    Request,
    Depends
)

from fastapi.responses import (
    FileResponse,
    HTMLResponse,
    RedirectResponse
)

from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from authentication_engine import (
    load_model,
    authenticate_voice
)

from enrollment_engine import (
    enroll_voice,
    enroll_voice_from_recordings
)

from database import (
    initialize_database,
    log_authentication,
    get_dashboard_stats,
    get_authentication_history,
    get_all_users,
    get_analytics_data
)

from security import (
    SESSION_SECRET,
    SESSION_MAX_AGE,
    authenticate_admin,
    require_admin,
    generate_csrf_token,
    validate_csrf_token
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
# SECURE SESSION MIDDLEWARE
# ============================================================

app.add_middleware(
    SessionMiddleware,
    secret_key=SESSION_SECRET,
    max_age=SESSION_MAX_AGE,
    same_site="lax",
    https_only=False
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
# ADMIN LOGIN PAGE
# ============================================================

@app.get("/admin/login")
def admin_login_page(request: Request):

    template_path = Path("templates/admin_login.html")

    if not template_path.exists():
        raise HTTPException(
            status_code=500,
            detail="Admin login template not found."
        )

    html = template_path.read_text(encoding="utf-8")

    csrf_token = generate_csrf_token(request)

    html = html.replace(
        "{{ csrf_token }}",
        csrf_token
    )

    return HTMLResponse(content=html)


# ============================================================
# ADMIN LOGIN API
# ============================================================

@app.post("/admin/login")
async def admin_login(

    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    csrf_token: str = Form(...)

):

    validate_csrf_token(
        request,
        csrf_token
    )

    admin = authenticate_admin(
        username.strip(),
        password
    )

    if not admin:

        return HTMLResponse(
            content=(
                "<h3>Invalid username or password.</h3>"
                '<a href="/admin/login">Try again</a>'
            ),
            status_code=401
        )

    # Clear previous session to prevent session fixation.
    request.session.clear()

    request.session["admin_username"] = admin["username"]

    # Generate a fresh CSRF token for the authenticated session.
    generate_csrf_token(request)

    return RedirectResponse(
        url="/",
        status_code=303
    )


# ============================================================
# ADMIN LOGOUT
# ============================================================

@app.post("/admin/logout")
def admin_logout(

    request: Request,
    csrf_token: str = Form(...)

):

    validate_csrf_token(
        request,
        csrf_token
    )

    request.session.clear()

    return RedirectResponse(
        url="/admin/login",
        status_code=303
    )


# ============================================================
# HOME PAGE - ADMIN ONLY
# ============================================================

@app.get("/")
def home(
    request: Request,
    admin=Depends(require_admin)
):

    html = Path("templates/index.html").read_text(
        encoding="utf-8"
    )

    csrf_token = generate_csrf_token(request)

    html = html.replace(
        "{{ csrf_token }}",
        csrf_token
    )

    return HTMLResponse(content=html)


# ============================================================
# PROTECTED PAGE ROUTES
# ============================================================

@app.get("/history-page")
def history_page(admin=Depends(require_admin)):

    return FileResponse("templates/history.html")


@app.get("/users-page")
def users_page(admin=Depends(require_admin)):

    return FileResponse("templates/users.html")


# ============================================================
# PUBLIC VOICE OPERATION PAGES
# ============================================================

@app.get("/enroll-page")
def enrollment_page():

    return FileResponse("templates/enroll.html")


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

        result = authenticate_voice(
            username,
            temp_path,
            verification_model
        )

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
# LIVE TWO-RECORDING ENROLLMENT API
# ============================================================

@app.post("/enroll-live")
async def enroll_live_user(

    username: str = Form(...),
    voice1: UploadFile = File(...),
    voice2: UploadFile = File(...)

):

    if verification_model is None:
        raise HTTPException(
            status_code=503,
            detail="Speaker model is not loaded"
        )

    temp_paths = []

    try:

        for voice in [voice1, voice2]:

            with tempfile.NamedTemporaryFile(
                delete=False,
                suffix=".wav"
            ) as temp_file:

                temp_paths.append(temp_file.name)

                shutil.copyfileobj(
                    voice.file,
                    temp_file
                )

        result = enroll_voice_from_recordings(
            username,
            temp_paths[0],
            temp_paths[1],
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

        for path in temp_paths:

            if os.path.exists(path):
                os.remove(path)

        await voice1.close()
        await voice2.close()


# ============================================================
# DASHBOARD STATISTICS API - ADMIN ONLY
# ============================================================

@app.get("/dashboard-stats")
def dashboard_stats(admin=Depends(require_admin)):

    try:

        return get_dashboard_stats()

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


# ============================================================
# INTERACTIVE ANALYTICS API - ADMIN ONLY
# ============================================================

@app.get("/analytics-data")
def analytics_data(admin=Depends(require_admin)):

    try:

        return get_analytics_data()

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


# ============================================================
# AUTHENTICATION HISTORY - ADMIN ONLY
# ============================================================

@app.get("/authentication-history")
def authentication_history(

    username: str = None,
    status: str = None,
    admin=Depends(require_admin)

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

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


# ============================================================
# REGISTERED USERS - ADMIN ONLY
# ============================================================

@app.get("/users")
def registered_users(admin=Depends(require_admin)):

    try:

        users = get_all_users()

        return {
            "total_users": len(users),
            "users": users
        }

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )