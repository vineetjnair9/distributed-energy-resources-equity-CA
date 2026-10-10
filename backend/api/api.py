import logging
import os
import sqlite3
from contextlib import asynccontextmanager, contextmanager
from pathlib import Path

from fastapi import APIRouter, FastAPI, HTTPException, Path as PathParam, Query, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from backend import catalog
from backend.api.models import (
    CompareResponse,
    Definitions,
    Evidence,
    Facets,
    HealthResponse,
    ModelOutputList,
    RegionDetail,
    RegionList,
    ScreeningResponse,
    SummaryCategoryList,
    SummaryRequest,
    SummaryResponse,
)
from backend.database import (
    PROJECT_ROOT,
    DatabaseNotReady,
    check_database,
    connect_readonly,
    database_path,
)
from backend.services import regions as region_service
from backend.services import summaries as summary_service
from backend.services.regions import RegionNotFound, UnknownOutcome
from backend.services.summaries import UnknownCategory


DB_PATH = database_path()
FRONTEND_DIST = Path(os.environ.get("DER_FRONTEND_DIST") or PROJECT_ROOT / "frontend" / "dist")
LOGGER = logging.getLogger(__name__)
SETUP_COMMAND = "python scripts/run_all.py --only data models database"
FIXTURE_COMMAND = "python -m backend.fixtures.build_fixture_db"
MAX_COMPARE = 6
MAX_TEXT = 100  # longest accepted search/filter value; real values are far shorter

# The SPA needs only its own origin plus OpenStreetMap tiles. Inline styles are
# allowed because React and Leaflet position elements with style attributes.
APP_CSP = "; ".join([
    "default-src 'self'",
    "script-src 'self'",
    "style-src 'self' 'unsafe-inline'",
    "img-src 'self' data: https://*.tile.openstreetmap.org",
    "connect-src 'self'",
    "object-src 'none'",
    "base-uri 'self'",
    "form-action 'self'",
    "frame-ancestors 'none'",
])
# Swagger UI loads its bundle and an inline bootstrap script from jsDelivr.
DOCS_CSP = APP_CSP.replace(
    "script-src 'self'", "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net"
).replace(
    "style-src 'self' 'unsafe-inline'",
    "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net",
).replace("img-src 'self' data:", "img-src 'self' data: https://fastapi.tiangolo.com")
SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "X-Frame-Options": "DENY",
    "Strict-Transport-Security": "max-age=31536000",
    "Permissions-Policy": "geolocation=(), camera=(), microphone=()",
}
RegionId = PathParam(max_length=16, description="Five-character ZCTA.")


def setup_command():
    if DB_PATH.exists():
        return SETUP_COMMAND + " --replace-database"
    return f"{SETUP_COMMAND}  (or, for synthetic demo data: {FIXTURE_COMMAND})"


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup only checks readiness. Schema creation, data builds and LLM calls
    # belong to explicit offline commands, never to the web server lifecycle.
    try:
        check_database(DB_PATH)
    except DatabaseNotReady as exc:
        LOGGER.warning("DER database not ready: %s Run: %s", exc, setup_command())
    yield


app = FastAPI(
    title="California DER Decision Support API",
    version="1.0.0",
    description=(
        "Region-centered access to DER adoption, demographic context, offline "
        "regression screening outputs, and precomputed evidence-grounded summaries "
        "for California ZCTAs. Every resource is keyed by a five-character region_id."
    ),
    lifespan=lifespan,
    openapi_url="/api/openapi.json",
    docs_url="/api/docs",
    redoc_url=None,
)
router = APIRouter(prefix="/api")


@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    for name, value in SECURITY_HEADERS.items():
        response.headers.setdefault(name, value)
    docs = request.url.path == app.docs_url
    response.headers.setdefault("Content-Security-Policy", DOCS_CSP if docs else APP_CSP)
    return response


@contextmanager
def get_connection():
    # sqlite3's own context manager commits/rolls back but does not close, so using
    # `with sqlite3.connect(...)` directly leaked a connection per request.
    conn = None
    try:
        conn = connect_readonly(DB_PATH)
        yield conn
    except (DatabaseNotReady, sqlite3.Error) as exc:
        LOGGER.warning("DER database request failed: %s", exc)
        raise HTTPException(
            status_code=503,
            detail="Database is not ready. Check /api/health for setup instructions.",
        ) from exc
    except RegionNotFound as exc:
        raise HTTPException(status_code=404, detail=f"Region not found: {exc}") from exc
    except UnknownOutcome as exc:
        raise HTTPException(
            status_code=404, detail=f"No model outputs for outcome: {exc}"
        ) from exc
    except UnknownCategory as exc:
        raise HTTPException(
            status_code=422,
            detail={
                "message": f"Unknown summary category: {exc}",
                "valid_categories": list(summary_service.category_labels()),
            },
        ) from exc
    finally:
        if conn is not None:
            conn.close()


def _is_synthetic():
    conn = connect_readonly(DB_PATH)
    try:
        return conn.execute(
            "SELECT 1 FROM summary_responses WHERE model_version LIKE ? LIMIT 1",
            (summary_service.FIXTURE_MODEL_PREFIX + "%",),
        ).fetchone() is not None
    finally:
        conn.close()


@app.get("/health", response_model=HealthResponse, include_in_schema=False)
@router.get("/health", response_model=HealthResponse, tags=["system"])
def health():
    """Readiness check used by the deploy smoke test and the frontend banner."""
    try:
        check_database(DB_PATH)
    except DatabaseNotReady as exc:
        return JSONResponse(status_code=503, content={
            "status": "not_ready",
            "message": str(exc),
            "database": DB_PATH.name,
            "synthetic": False,
            "setup_command": setup_command(),
        })
    return {
        "status": "ready",
        "message": "DER API is running",
        "database": DB_PATH.name,
        "synthetic": _is_synthetic(),
    }


@router.get("/regions", response_model=RegionList, tags=["regions"])
def list_regions(
    q: str | None = Query(
        None, max_length=MAX_TEXT, description="Prefix of a ZCTA or county, or part of a name."
    ),
    county: str | None = Query(None, max_length=MAX_TEXT),
    utility: str | None = Query(None, max_length=MAX_TEXT, description="Utility acronym or full name."),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    with get_connection() as conn:
        return region_service.search_regions(
            conn, q=q, county=county, utility=utility, limit=limit, offset=offset)


@router.get("/facets", response_model=Facets, tags=["regions"])
def facets():
    """Counties, utilities, and modeled outcomes available for filtering."""
    with get_connection() as conn:
        return region_service.get_facets(conn)


@router.get("/screening", response_model=ScreeningResponse, tags=["models"])
def screening(
    outcome_name: str = Query("y_pv", max_length=MAX_TEXT, description="Outcome to screen, e.g. y_pv."),
    county: str | None = Query(None, max_length=MAX_TEXT),
    utility: str | None = Query(None, max_length=MAX_TEXT),
    limit: int = Query(20, ge=1, le=200),
):
    """Regions flagged as priorities, ranked by agreement across specifications.

    DER outcomes flag adoption below prediction (residual at or below the 25th
    percentile); burden outcomes flag burden above prediction (75th or higher).
    """
    with get_connection() as conn:
        return region_service.screen_regions(
            conn, outcome_name, county=county, utility=utility, limit=limit)


@router.get("/regions/{region_id}", response_model=RegionDetail, tags=["regions"])
def get_region(region_id: str = RegionId):
    """Region metadata, every metric observation, missing categories, and geometry."""
    with get_connection() as conn:
        return region_service.get_region_detail(conn, region_id)


@router.get("/regions/{region_id}/evidence", response_model=list[Evidence], tags=["regions"])
def get_region_evidence(region_id: str = RegionId, evidence_type: str | None = None):
    with get_connection() as conn:
        return region_service.get_evidence(conn, region_id, evidence_type)


@router.get(
    "/regions/{region_id}/summaries", response_model=SummaryCategoryList, tags=["summaries"]
)
def list_region_summaries(region_id: str = RegionId):
    """Which summary categories have a stored summary for this region."""
    with get_connection() as conn:
        return summary_service.list_summary_categories(conn, region_id)


@router.get("/model-output/{region_id}", response_model=ModelOutputList, tags=["models"])
def get_model_output(
    region_id: str = RegionId,
    outcome_name: str | None = None,
    model_version: str | None = None,
):
    """Stored offline regression outputs. Nothing is fit or scored per request."""
    with get_connection() as conn:
        return region_service.get_model_outputs(
            conn, region_id, outcome_name=outcome_name, model_version=model_version)


@router.get("/compare", response_model=CompareResponse, tags=["regions"])
def compare(
    region_ids: list[str] = Query(
        ..., max_length=MAX_COMPARE * 2,
        description="Repeat the parameter or pass a comma-separated list.",
    ),
):
    ids = list(dict.fromkeys(
        part.strip() for value in region_ids for part in value.split(",") if part.strip()
    ))
    if not 2 <= len(ids) <= MAX_COMPARE:
        raise HTTPException(
            status_code=400,
            detail=f"Compare needs between 2 and {MAX_COMPARE} distinct region_ids.",
        )
    with get_connection() as conn:
        return region_service.compare_regions(
            conn, ids, lambda region_id: summary_service.get_summary(conn, region_id))


@router.post("/summaries", response_model=SummaryResponse, tags=["summaries"])
def request_summary(request: SummaryRequest):
    """Return the stored, evidence-grounded summary for a region and category.

    Summaries are generated offline; this endpoint never calls an LLM. When no
    traceable summary exists, status is "unavailable" and the retrieved evidence
    is returned with the reason in `warnings`.
    """
    with get_connection() as conn:
        return summary_service.get_summary(conn, request.region_id, request.category)


@router.get("/definitions", response_model=Definitions, tags=["reference"])
def definitions():
    """Plain-language definitions of every term, indicator, outcome, and specification."""
    return {
        "terms": [{"term": t, "definition": d} for t, d in catalog.TERMS],
        "metrics": [
            {
                "metric_name": name,
                "label": catalog.METRIC_DEFINITIONS[name][0],
                "definition": catalog.METRIC_DEFINITIONS[name][1],
                "unit": unit,
                "category": category,
                "source_name": source,
                "source_url": catalog.SOURCE_URLS.get(source),
            }
            for name, (unit, category, source) in catalog.METRIC_COLUMNS.items()
            if name in catalog.METRIC_DEFINITIONS
        ],
        "outcomes": [
            {"outcome_name": name, "label": label, "modeled_as": scale,
             "flag_rule": region_service.flag_direction(name)}
            for name, (label, scale) in catalog.OUTCOME_DEFINITIONS.items()
        ],
        "specifications": [
            {"name": name, "description": text} for name, text in catalog.SPECIFICATIONS
        ],
        "standard_errors": catalog.STANDARD_ERRORS,
    }


@router.get("/summary-categories", response_model=dict[str, str], tags=["summaries"])
def summary_categories():
    """Valid summary categories and their display labels."""
    return summary_service.category_labels()


app.include_router(router)


if (FRONTEND_DIST / "index.html").is_file():
    app.mount("/assets", StaticFiles(directory=FRONTEND_DIST / "assets"), name="assets")

    @app.get("/{path:path}", include_in_schema=False)
    def frontend(path: str):
        # Client-side routes (/regions/90001, /compare) all load the SPA shell;
        # unknown /api paths still 404 as JSON instead of returning HTML.
        if path.startswith("api/"):
            raise HTTPException(status_code=404, detail="Not found")
        candidate = (FRONTEND_DIST / path).resolve()
        if path and candidate.is_file() and candidate.is_relative_to(FRONTEND_DIST.resolve()):
            return FileResponse(candidate)
        return FileResponse(FRONTEND_DIST / "index.html")
