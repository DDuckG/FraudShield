import time
from datetime import datetime, timezone
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse, Response

from src.api.inference import batch_predict, load_artifacts, predict_fraud
from src.api.logger import get_logger

from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

from src.api.prediction_store import (
    make_prediction_record,
    save_prediction_record,
    save_prediction_records,
)

from src.api.schemas import (
    FraudDetectionRequest,
    FraudResponse,
    BatchFraudResponse,
    FeedbackRequest,
    FeedbackResponse,
)

from src.api.feedback_store import (
    make_feedback_record,
    save_feedback_record,
)

from src.monitoring.metrics import (
    HTTP_REQUESTS_TOTAL,
    HTTP_REQUEST_DURATION_SECONDS,
    PREDICTIONS_TOTAL,
    POSITIVE_PREDICTIONS_TOTAL,
    FEEDBACK_TOTAL,
)
from src.settings import env

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        app.state.artifacts = load_artifacts()
        app.state.artifacts_error = None
        logger.info("application startup successful")
    except Exception as exc:
        app.state.artifacts = None
        app.state.artifacts_error = str(exc)
        logger.exception("model artifacts are not ready")
    yield
    logger.info("application shutdown")


app = FastAPI(
    title="Fraud Detection API",
    version="1.0.0",
    lifespan=lifespan,
)


def _artifacts(request: Request) -> dict:
    artifacts = getattr(request.app.state, "artifacts", None)
    if artifacts is None:
        raise HTTPException(
            status_code=503,
            detail="Model artifacts chưa sẵn sàng",
        )
    return artifacts


def _persistence_strict() -> bool:
    return env("PERSISTENCE_MODE", "best_effort").lower() == "strict"


def _handle_prediction_save_error(exc: Exception, prediction_id: str) -> None:
    logger.exception(
        "failed to save prediction record",
        extra={
            "prediction_id": prediction_id,
            "error": str(exc),
        },
    )
    if _persistence_strict():
        raise HTTPException(
            status_code=503,
            detail="Không lưu được trace dự đoán",
        ) from exc


@app.middleware("http")
async def log_requests(request: Request, call_next):
    request_id = str(uuid.uuid4())
    start_time = time.perf_counter()

    request.state.request_id = request_id

    logger.info(
        "request started",
        extra={
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
        },
    )

    try:
        response = await call_next(request)
    except Exception:
        duration = time.perf_counter() - start_time

        HTTP_REQUESTS_TOTAL.labels(
            method=request.method,
            path=request.url.path,
            status_code="500",
        ).inc()

        HTTP_REQUEST_DURATION_SECONDS.labels(
            method=request.method,
            path=request.url.path,
        ).observe(duration)

        logger.exception(
            "request failed",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "latency_ms": round(duration * 1000, 2),
            },
        )
        raise

    duration = time.perf_counter() - start_time

    HTTP_REQUESTS_TOTAL.labels(
        method=request.method,
        path=request.url.path,
        status_code=str(response.status_code),
    ).inc()

    HTTP_REQUEST_DURATION_SECONDS.labels(
        method=request.method,
        path=request.url.path,
    ).observe(duration)

    response.headers["X-Request-ID"] = request_id

    logger.info(
        "request completed",
        extra={
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "latency_ms": round(duration * 1000, 2),
        },
    )

    return response

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    request_id = getattr(request.state, "request_id", None)

    logger.exception(
        "unhandled exception",
        extra={
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "error_type": type(exc).__name__,
        },
    )

    return JSONResponse(
        status_code=500,
        content={
            "error": type(exc).__name__,
            "detail": str(exc),
            "path": str(request.url),
            "request_id": request_id,
        },
    )


@app.get("/")
def root():
    logger.info("root endpoint called")
    return {
        "message": "Fraud Detection API is running",
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/health")
def health_check(request: Request):
    artifacts = getattr(request.app.state, "artifacts", None)
    model_ok = bool(
        artifacts
        and "model" in artifacts
        and "fe_params" in artifacts
        and "model_columns" in artifacts
    )
    meta = artifacts.get("meta", {}) if artifacts else {}

    logger.info(
        "health check evaluated",
        extra={
            "model_loaded": model_ok,
            "model_type": meta.get("selected_model", "unknown"),
            "dataset_branch": meta.get("dataset_branch", "unknown"),
        },
    )

    return {
        "status": "healthy" if model_ok else "degraded",
        "model_loaded": model_ok,
        "model_type": meta.get("selected_model", "unknown"),
        "dataset_branch": meta.get("dataset_branch", "unknown"),
        "artifact_error": getattr(request.app.state, "artifacts_error", None),
    }

@app.get("/metrics")
def metrics():
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST,
    )

@app.post("/predict", response_model=FraudResponse)
def predict(req: FraudDetectionRequest, request: Request):
    logger.info(
        "predict endpoint invoked",
        extra={
            "transaction_id": req.transaction_id,
            "user_id": req.user_id,
        },
    )

    artifacts = _artifacts(request)
    result = predict_fraud(req, artifacts)

    # Ghi metric sau khi model đã trả kết quả.
    PREDICTIONS_TOTAL.labels(endpoint="predict").inc()
    if result.is_fraud:
        POSITIVE_PREDICTIONS_TOTAL.labels(endpoint="predict").inc()

    meta = artifacts.get("meta", {})
    model_version = env("MODEL_VERSION", "unknown")
    request_id = getattr(request.state, "request_id", None)

    record = make_prediction_record(
        request_id=request_id,
        transaction_id=req.transaction_id,
        user_id=req.user_id,
        request_payload=req.model_dump(),
        response_payload=result.model_dump(mode="json"),
        model_version=model_version,
        model_type=meta.get("selected_model", "unknown"),
        dataset_branch=meta.get("dataset_branch", "unknown"),
    )
    result = result.model_copy(update={"prediction_id": record["prediction_id"]})

    try:
        gcs_blob = save_prediction_record(record)
        logger.info(
            "prediction record saved to gcs",
            extra={
                "prediction_id": record["prediction_id"],
                "gcs_blob": gcs_blob,
            },
        )
    except Exception as e:
        _handle_prediction_save_error(e, record["prediction_id"])

    return result

@app.post("/batch", response_model=BatchFraudResponse)
def batch(reqs: list[FraudDetectionRequest], request: Request):
    logger.info(
        "batch endpoint invoked",
        extra={"batch_size": len(reqs)},
    )

    artifacts = _artifacts(request)
    responses = batch_predict(reqs, artifacts)

    # Batch vẫn đếm từng giao dịch để dashboard không bị lệch tổng.
    for result in responses:
        PREDICTIONS_TOTAL.labels(endpoint="batch").inc()
        if result.is_fraud:
            POSITIVE_PREDICTIONS_TOTAL.labels(endpoint="batch").inc()


    meta = artifacts.get("meta", {})
    model_version = env("MODEL_VERSION", "unknown")
    request_id = getattr(request.state, "request_id", None)

    enriched_responses = []
    records = []
    for req, result in zip(reqs, responses):
        record = make_prediction_record(
            request_id=request_id,
            transaction_id=req.transaction_id,
            user_id=req.user_id,
            request_payload=req.model_dump(),
            response_payload=result.model_dump(mode="json"),
            model_version=model_version,
            model_type=meta.get("selected_model", "unknown"),
            dataset_branch=meta.get("dataset_branch", "unknown"),
        )
        result = result.model_copy(update={"prediction_id": record["prediction_id"]})
        enriched_responses.append(result)
        records.append(record)

    if records:
        try:
            batch_id = f"batch-{request_id or uuid.uuid4()}"
            gcs_blob = save_prediction_records(records, batch_id=batch_id)
            logger.info(
                "batch prediction records saved to gcs",
                extra={
                    "batch_size": len(records),
                    "gcs_blob": gcs_blob,
                },
            )
        except Exception as e:
            _handle_prediction_save_error(e, records[0]["prediction_id"])

    return BatchFraudResponse(
        results=enriched_responses,
        total=len(enriched_responses),
        fraud_count=sum(1 for r in enriched_responses if r.is_fraud),
    )


@app.post("/feedback", response_model=FeedbackResponse)
def feedback(req: FeedbackRequest, request: Request):
    request_id = getattr(request.state, "request_id", None)

    logger.info(
        "feedback endpoint invoked",
        extra={
            "prediction_id": req.prediction_id,
            "source": req.source,
        },
    )

    FEEDBACK_TOTAL.labels(source=req.source).inc()

    record = make_feedback_record(
        request_id=request_id,
        prediction_id=req.prediction_id,
        actual_label=req.actual_label,
        feedback_time=req.feedback_time,
        source=req.source,
    )

    try:
        blob_name = save_feedback_record(record)
        logger.info(
            "feedback record saved to gcs",
            extra={
                "feedback_id": record["feedback_id"],
                "prediction_id": req.prediction_id,
                "blob_name": blob_name,
            },
        )
    except Exception as e:
        logger.exception(
            "failed to save feedback record",
            extra={
                "prediction_id": req.prediction_id,
                "error": str(e),
            },
        )
        raise

    return FeedbackResponse(
        status="success",
        prediction_id=req.prediction_id,
        stored_at=datetime.now(timezone.utc),
    )
