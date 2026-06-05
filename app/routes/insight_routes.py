from flask import Blueprint, request

from app.extensions import db
from app.models.log_insight import LogInsight
from app.utils.logger import log_message
from app.utils.response import error_response, success_response

insight_bp = Blueprint("insights", __name__)


@insight_bp.route("/insights", methods=["GET"])
def list_insights():
    """
    List all log insights with optional filtering.

    Query params:
      - health_status: filter by healthy|degraded|unhealthy|unknown
      - limit: max results (default 50)
    """
    health_status = request.args.get("health_status")
    limit = request.args.get("limit", 50, type=int)

    query = LogInsight.query

    if health_status:
        query = query.filter_by(health_status=health_status)

    insights = query.order_by(LogInsight.created_at.desc()).limit(limit).all()

    log_message("API", f"Listed {len(insights)} insights")

    return success_response([insight.to_dict() for insight in insights])


@insight_bp.route("/insights/<int:insight_id>", methods=["GET"])
def get_insight(insight_id):
    """
    Get a single insight by ID.

    Response includes full insight data + linked file_job summary.
    """
    insight = LogInsight.query.get(insight_id)

    if not insight:
        return error_response("Insight not found", 404)

    result = insight.to_dict()

    # Include linked file job summary for context
    if insight.file_job:
        result["file_job"] = {
            "id": insight.file_job.id,
            "original_filename": insight.file_job.original_filename,
            "status": insight.file_job.status,
            "processing_time": insight.file_job.processing_time,
            "created_at": insight.file_job.created_at.isoformat() if insight.file_job.created_at else None,
        }

    log_message("API", f"Insight retrieved id={insight_id}")

    return success_response(result)


@insight_bp.route("/insights/health-summary", methods=["GET"])
def health_summary():
    """
    Aggregated health summary across all insights.

    Returns counts by status + average health score.
    """
    from sqlalchemy import func

    total = LogInsight.query.count()

    healthy = LogInsight.query.filter_by(health_status="healthy").count()
    degraded = LogInsight.query.filter_by(health_status="degraded").count()
    unhealthy = LogInsight.query.filter_by(health_status="unhealthy").count()
    unknown = LogInsight.query.filter_by(health_status="unknown").count()

    avg_score = db.session.query(func.avg(LogInsight.health_score)).scalar()

    summary = {
        "total_insights": total,
        "breakdown": {
            "healthy": healthy,
            "degraded": degraded,
            "unhealthy": unhealthy,
            "unknown": unknown,
        },
        "average_health_score": round(float(avg_score), 3) if avg_score else None,
        "healthy_percentage": round((healthy / total) * 100, 1) if total else 0,
    }

    log_message("API", f"Health summary generated: {summary}")

    return success_response(summary)