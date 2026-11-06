from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response

from database import (
    get_authentication_history,
    get_analytics_data
)

from report_export import (
    generate_history_csv,
    generate_history_pdf,
    generate_analytics_csv,
    generate_analytics_pdf
)

from security import require_admin


# ============================================================
# REPORT EXPORT ROUTER
# ============================================================

router = APIRouter(
    tags=["Report Export"]
)


def get_filename(report_name, extension):

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    return f"securevoiceai_{report_name}_{timestamp}.{extension}"


# ============================================================
# AUTHENTICATION HISTORY CSV EXPORT
# ============================================================

@router.get("/export/history/csv")
def export_history_csv(admin=Depends(require_admin)):

    try:

        records = get_authentication_history()

        report = generate_history_csv(records)

        filename = get_filename(
            "authentication_history",
            "csv"
        )

        return Response(
            content=report,
            media_type="text/csv; charset=utf-8",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"'
            }
        )

    except Exception:

        raise HTTPException(
            status_code=500,
            detail="Unable to generate authentication history CSV."
        )


# ============================================================
# AUTHENTICATION HISTORY PDF EXPORT
# ============================================================

@router.get("/export/history/pdf")
def export_history_pdf(admin=Depends(require_admin)):

    try:

        records = get_authentication_history()

        report = generate_history_pdf(records)

        filename = get_filename(
            "authentication_history",
            "pdf"
        )

        return Response(
            content=report,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"'
            }
        )

    except Exception:

        raise HTTPException(
            status_code=500,
            detail="Unable to generate authentication history PDF."
        )


# ============================================================
# ANALYTICS CSV EXPORT
# ============================================================

@router.get("/export/analytics/csv")
def export_analytics_csv(admin=Depends(require_admin)):

    try:

        analytics = get_analytics_data()

        report = generate_analytics_csv(analytics)

        filename = get_filename(
            "analytics",
            "csv"
        )

        return Response(
            content=report,
            media_type="text/csv; charset=utf-8",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"'
            }
        )

    except Exception:

        raise HTTPException(
            status_code=500,
            detail="Unable to generate analytics CSV."
        )


# ============================================================
# ANALYTICS PDF EXPORT
# ============================================================

@router.get("/export/analytics/pdf")
def export_analytics_pdf(admin=Depends(require_admin)):

    try:

        analytics = get_analytics_data()

        report = generate_analytics_pdf(analytics)

        filename = get_filename(
            "analytics",
            "pdf"
        )

        return Response(
            content=report,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"'
            }
        )

    except Exception:

        raise HTTPException(
            status_code=500,
            detail="Unable to generate analytics PDF."
        )