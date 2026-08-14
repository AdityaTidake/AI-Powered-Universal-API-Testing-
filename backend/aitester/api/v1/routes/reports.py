from beanie import PydanticObjectId
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse

from aitester.api.dependencies import get_current_user
from aitester.db.models import Project, TestCase, TestResult, TestRun, User
from aitester.reports.html_generator import generate_html_report
from aitester.reports.json_generator import generate_json_report

router = APIRouter(prefix="/runs/{run_id}/report", tags=["Reports"])


async def _get_run_data(run_id: str, current_user: User) -> dict:
    try:
        test_run = await TestRun.get(PydanticObjectId(run_id))
    except Exception:
        test_run = None
        
    if not test_run:
        raise HTTPException(status_code=404, detail=f"Test run {run_id} not found")

    # Enforce row-level security
    try:
        project = await Project.get(test_run.project_id)
    except Exception:
        project = None
        
    if not project or project.owner_id != current_user.id:
        raise HTTPException(status_code=404, detail="Test run not found")

    # Fetch cases and results manually since there are no SQLAlchemy relationships
    test_cases = await TestCase.find(TestCase.test_run_id == test_run.id).to_list()
    test_results = await TestResult.find(TestResult.test_run_id == test_run.id).to_list()

    # Map results by test_case_id for quick lookup
    results_by_case = {r.test_case_id: r for r in test_results}

    results_data = []
    for tc in test_cases:
        tr = results_by_case.get(tc.id)
        if tr:
            results_data.append({
                "test_case_name": tc.category + " - " + tc.endpoint,
                "category": tc.category,
                "status": tr.status,
                "method": tc.method,
                "path": tc.endpoint,
                "actual_status_code": tr.actual_status_code,
                "response_time_ms": tr.response_time_ms,
            })

    # Compute security score from results that had security-related failures
    security_findings = []
    total_results_count = len(results_data)
    security_fail_count = 0
    for tc in test_cases:
        tr = results_by_case.get(tc.id)
        if tr and not tr.passed:
            ai_analysis = tr.ai_failure_analysis or {}
            if ai_analysis.get("is_security_concern", False):
                security_fail_count += 1
                security_findings.append({
                    "endpoint": tc.endpoint,
                    "method": tc.method,
                    "severity": ai_analysis.get("severity", "medium"),
                    "description": ai_analysis.get("explanation", "Security validation failed")[:150],
                })

    # Security score: 100 minus a weighted penalty per security failure
    if total_results_count > 0:
        security_score = round(
            max(0.0, 100.0 - (security_fail_count / total_results_count) * 100), 1
        )
    else:
        security_score = 100.0

    # AI executive summary derived from run stats
    passed_count = sum(1 for r in results_data if r["status"] == "passed")
    failed_count = total_results_count - passed_count
    pass_rate = round(passed_count / total_results_count * 100, 1) if total_results_count else 0.0
    ai_executive_summary = (
        f"Test run completed with {total_results_count} cases: "
        f"{passed_count} passed ({pass_rate}%), {failed_count} failed. "
        f"Security score: {security_score}/100. "
        + (f"{security_fail_count} security issue(s) detected." if security_fail_count else "No security issues detected.")
    )

    return {
        "project_name": project.name,
        "run_id": str(test_run.id),
        "started_at": test_run.started_at.isoformat() if test_run.started_at else None,
        "completed_at": test_run.completed_at.isoformat() if test_run.completed_at else None,
        "duration_ms": 0,
        "results": results_data,
        "security_score": security_score,
        "security_findings": security_findings,
        "ai_executive_summary": ai_executive_summary,
    }


@router.get("/html", response_class=HTMLResponse)
async def get_html_report(run_id: str, current_user: User = Depends(get_current_user)):
    """Get the HTML report for a test run."""
    run_data = await _get_run_data(run_id, current_user)
    html_content = generate_html_report(run_data)
    return HTMLResponse(content=html_content)


@router.get("/json", response_class=JSONResponse)
async def get_json_report(run_id: str, current_user: User = Depends(get_current_user)):
    """Get the JSON report for a test run."""
    run_data = await _get_run_data(run_id, current_user)
    import json
    json_content = generate_json_report(run_data)
    return JSONResponse(content=json.loads(json_content))
