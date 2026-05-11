# Composition / "view" endpoints for the BFF.
#
# Owns no persistent state. Every route is a fan-out across peer
# services. The intent is to keep the SPA's existing URL shapes
# stable while moving cross-cutting joins out of the domain services.

import asyncio
from typing import Optional

import httpx
from fastapi import APIRouter, Depends, HTTPException

from app.auth import (
    CurrentUser,
    get_auth_header,
    get_current_user,
    require_role,
)
from app.peer import (
    ASSIGNMENT_SERVICE_URL,
    CLASS_SERVICE_URL,
    ENROLLMENT_SERVICE_URL,
    GRADING_SERVICE_URL,
    SUBMISSION_SERVICE_URL,
    mtls_client,
)

router = APIRouter()


# ───────────────── peer helpers ─────────────────


async def _get_json(client: httpx.AsyncClient, url: str, *, params=None, headers=None, default=None):
    """GET that returns parsed JSON or `default` on any non-200 / network failure."""
    try:
        res = await client.get(url, params=params, headers=headers)
    except httpx.RequestError:
        return default
    if res.status_code != 200:
        return default
    return res.json()


# ───────────────── /views/classes (enriched class catalog) ─────────


async def _enrich_classes(client: httpx.AsyncClient, classes: list, headers: dict) -> list:
    """Attach studentCount + assignmentCount to each class via peer calls.

    Uses batch endpoints where available so an N-class list only needs
    O(N) HTTP calls (one per class for assignments — service-assignment
    has no batch yet — plus one batch for student counts).
    """
    if not classes:
        return []

    class_ids = [str(c["id"]) for c in classes]

    counts_task = _get_json(
        client,
        f"{ENROLLMENT_SERVICE_URL}/enrollments/counts",
        params={"classIds": ",".join(class_ids)},
        headers=headers,
        default={},
    )

    async def assignment_count_for(cid: str) -> int:
        rows = await _get_json(
            client,
            f"{ASSIGNMENT_SERVICE_URL}/assignments",
            params={"classId": cid},
            headers=headers,
            default=[],
        )
        return len(rows or [])

    counts, *acs = await asyncio.gather(
        counts_task,
        *[assignment_count_for(cid) for cid in class_ids],
    )

    out = []
    for c, ac in zip(classes, acs):
        c = {**c}
        c["studentCount"] = int((counts or {}).get(str(c["id"]), 0))
        c["assignmentCount"] = ac
        out.append(c)
    return out


@router.get("/views/classes")
async def list_classes_enriched(
    professorId: Optional[str] = None,
    studentId: Optional[str] = None,
    _: CurrentUser = Depends(get_current_user),
    auth_header: dict = Depends(get_auth_header),
):
    params = {}
    if professorId:
        params["professorId"] = professorId
    if studentId:
        params["studentId"] = studentId

    async with mtls_client() as client:
        # If filtering by student, resolve their class ids via the
        # enrollment service first; service-class is pure CRUD now and
        # no longer accepts studentId.
        if studentId:
            enrollments = await _get_json(
                client,
                f"{ENROLLMENT_SERVICE_URL}/enrollments",
                params={"studentId": studentId},
                headers=auth_header,
                default=[],
            )
            class_ids = [
                (e.get("classId") or e.get("class_id"))
                for e in (enrollments or [])
            ]
            class_ids = [cid for cid in class_ids if cid]
            if not class_ids:
                return []
            # service-class doesn't accept batch ids; fetch each.
            classes = await asyncio.gather(
                *[
                    _get_json(
                        client,
                        f"{CLASS_SERVICE_URL}/classes/{cid}",
                        headers=auth_header,
                    )
                    for cid in class_ids
                ]
            )
            classes = [c for c in classes if c]
        else:
            classes = await _get_json(
                client,
                f"{CLASS_SERVICE_URL}/classes",
                params=params,
                headers=auth_header,
                default=[],
            ) or []

        return await _enrich_classes(client, classes, auth_header)


@router.get("/views/classes/{class_id}")
async def get_class_enriched(
    class_id: str,
    _: CurrentUser = Depends(get_current_user),
    auth_header: dict = Depends(get_auth_header),
):
    async with mtls_client() as client:
        cls = await _get_json(
            client, f"{CLASS_SERVICE_URL}/classes/{class_id}", headers=auth_header
        )
        if not cls:
            raise HTTPException(status_code=404, detail="Class not found")
        enriched = await _enrich_classes(client, [cls], auth_header)
        return enriched[0]


# ───────────────── /assignments/for-student/{id} ────────────────────────


@router.get("/assignments/for-student/{student_id}")
async def assignments_for_student(
    student_id: str,
    _: CurrentUser = Depends(get_current_user),
    auth_header: dict = Depends(get_auth_header),
):
    async with mtls_client() as client:
        # Look up the student's classes via enrollment, then fan out for
        # assignments + submissions.
        enrollments = await _get_json(
            client,
            f"{ENROLLMENT_SERVICE_URL}/enrollments",
            params={"studentId": student_id},
            headers=auth_header,
            default=[],
        ) or []
        class_ids = [
            (e.get("classId") or e.get("class_id"))
            for e in enrollments
        ]
        class_ids = [c for c in class_ids if c]
        if not class_ids:
            return []

        classes, submissions = await asyncio.gather(
            asyncio.gather(*[
                _get_json(
                    client,
                    f"{CLASS_SERVICE_URL}/classes/{cid}",
                    headers=auth_header,
                )
                for cid in class_ids
            ]),
            _get_json(
                client,
                f"{SUBMISSION_SERVICE_URL}/submissions",
                params={"studentId": student_id},
                headers=auth_header,
                default=[],
            ),
        )
        classes = [c for c in classes if c]
        submissions = submissions or []

        assignments_lists = await asyncio.gather(*[
            _get_json(
                client,
                f"{ASSIGNMENT_SERVICE_URL}/assignments",
                params={"classId": cid},
                headers=auth_header,
                default=[],
            )
            for cid in class_ids
        ])

    submission_by_assignment = {
        (s.get("assignmentId") or s.get("assignment_id")): s
        for s in submissions
    }
    class_by_id = {str(c["id"]): c for c in classes}

    out = []
    for cid, alist in zip(class_ids, assignments_lists):
        cls = class_by_id.get(str(cid), {})
        for a in (alist or []):
            out.append({
                "assignment": a,
                "className": cls.get("name", ""),
                "classCode": cls.get("code", ""),
                "submission": submission_by_assignment.get(str(a["id"])),
            })
    return out


# ───────────────── grading-queue + stats ───────────────────────


async def _fetch_grades_by_submissions(
    client: httpx.AsyncClient, submission_ids: list, headers: dict
) -> list:
    """Look up grades for a list of submission ids via the grading service."""
    if not submission_ids:
        return []
    rows = await _get_json(
        client,
        f"{GRADING_SERVICE_URL}/grading",
        params={"submissionIds": ",".join(submission_ids)},
        headers=headers,
        default=[],
    )
    return rows or []


async def _build_professor_context(
    client: httpx.AsyncClient, professor_id: str, headers: dict
) -> dict:
    """Fetch classes/assignments/submissions/grades for a professor."""
    classes = await _get_json(
        client,
        f"{CLASS_SERVICE_URL}/classes",
        params={"professorId": professor_id},
        headers=headers,
        default=[],
    ) or []

    if not classes:
        return {"classes": [], "assignments": [], "submissions": [], "grades": []}

    assignments_lists = await asyncio.gather(*[
        _get_json(
            client,
            f"{ASSIGNMENT_SERVICE_URL}/assignments",
            params={"classId": c["id"]},
            headers=headers,
            default=[],
        )
        for c in classes
    ])
    assignments = [a for lst in assignments_lists for a in (lst or [])]

    submission_lists = await asyncio.gather(*[
        _get_json(
            client,
            f"{SUBMISSION_SERVICE_URL}/submissions",
            params={"assignmentId": a["id"]},
            headers=headers,
            default=[],
        )
        for a in assignments
    ])
    submissions = [s for lst in submission_lists for s in (lst or [])]

    grades = await _fetch_grades_by_submissions(
        client, [s["id"] for s in submissions], headers
    )

    return {
        "classes": classes,
        "assignments": assignments,
        "submissions": submissions,
        "grades": grades,
    }


def _build_queue(ctx: dict) -> list:
    graded = {str(g.get("submissionId") or g.get("submission_id")) for g in ctx["grades"]}
    class_by_id = {str(c["id"]): c for c in ctx["classes"]}
    assignment_by_id = {str(a["id"]): a for a in ctx["assignments"]}

    queue = []
    for s in ctx["submissions"]:
        if str(s["id"]) in graded:
            continue
        a = assignment_by_id.get(str(s.get("assignmentId") or s.get("assignment_id")))
        if not a:
            continue
        cls = class_by_id.get(str(a.get("classId") or a.get("class_id")))
        if not cls:
            continue
        queue.append({"submission": s, "assignment": a, "class": cls})

    queue.sort(
        key=lambda item: (
            item["submission"].get("submittedAt")
            or item["submission"].get("submitted_at")
            or ""
        )
    )
    return queue


@router.get("/professors/{professor_id}/grading-queue")
async def professor_grading_queue(
    professor_id: str,
    limit: int = 50,
    _: CurrentUser = Depends(require_role("professor")),
    auth_header: dict = Depends(get_auth_header),
):
    async with mtls_client() as client:
        ctx = await _build_professor_context(client, professor_id, auth_header)
    return _build_queue(ctx)[:limit]


@router.get("/professors/{professor_id}/stats")
async def professor_stats(
    professor_id: str,
    _: CurrentUser = Depends(require_role("professor")),
    auth_header: dict = Depends(get_auth_header),
):
    async with mtls_client() as client:
        ctx = await _build_professor_context(client, professor_id, auth_header)
    grades = ctx["grades"]
    queue = _build_queue(ctx)

    def _score(g):
        return g.get("score")

    def _possible(g):
        return g.get("pointsPossible") or g.get("points_possible")

    if grades:
        pts = [
            (_score(g) / _possible(g)) * 100.0
            for g in grades
            if _possible(g)
        ]
        avg_grade = sum(pts) / len(pts) if pts else None
    else:
        avg_grade = None

    return {
        "classCount": len(ctx["classes"]),
        "pendingCount": len(queue),
        "gradedCount": len(grades),
        "avgGrade": avg_grade,
    }


@router.get("/students/{student_id}/stats")
async def student_stats(
    student_id: str,
    _: CurrentUser = Depends(get_current_user),
    auth_header: dict = Depends(get_auth_header),
):
    async with mtls_client() as client:
        subs, assignment_views = await asyncio.gather(
            _get_json(
                client,
                f"{SUBMISSION_SERVICE_URL}/submissions",
                params={"studentId": student_id},
                headers=auth_header,
                default=[],
            ),
            assignments_for_student_internal(client, student_id, auth_header),
        )
        subs = subs or []
        grades = await _fetch_grades_by_submissions(
            client, [s["id"] for s in subs], auth_header
        )

    def _score(g):
        return g.get("score")

    def _possible(g):
        return g.get("pointsPossible") or g.get("points_possible")

    if grades:
        pts = [
            (_score(g) / _possible(g)) * 100.0
            for g in grades
            if _possible(g)
        ]
        avg_grade = sum(pts) / len(pts) if pts else None
    else:
        avg_grade = None

    upcoming = sum(
        1
        for v in (assignment_views or [])
        if v.get("submission") is None and v.get("assignment", {}).get("isOpen")
    )

    def _graded_at(g):
        return g.get("gradedAt") or g.get("graded_at") or ""

    recent = sorted(grades, key=_graded_at, reverse=True)[:4]

    return {
        "avgGrade": avg_grade,
        "upcomingCount": upcoming,
        "recentGrades": recent,
    }


async def assignments_for_student_internal(
    client: httpx.AsyncClient, student_id: str, headers: dict
) -> list:
    """In-process callable mirror of the /assignments/for-student/{id} route.

    Used by student_stats so we don't pay a second mTLS hop to ourselves.
    """
    enrollments = await _get_json(
        client,
        f"{ENROLLMENT_SERVICE_URL}/enrollments",
        params={"studentId": student_id},
        headers=headers,
        default=[],
    ) or []
    class_ids = [
        (e.get("classId") or e.get("class_id")) for e in enrollments
    ]
    class_ids = [c for c in class_ids if c]
    if not class_ids:
        return []

    classes, submissions = await asyncio.gather(
        asyncio.gather(*[
            _get_json(
                client,
                f"{CLASS_SERVICE_URL}/classes/{cid}",
                headers=headers,
            )
            for cid in class_ids
        ]),
        _get_json(
            client,
            f"{SUBMISSION_SERVICE_URL}/submissions",
            params={"studentId": student_id},
            headers=headers,
            default=[],
        ),
    )
    classes = [c for c in classes if c]
    submissions = submissions or []

    assignments_lists = await asyncio.gather(*[
        _get_json(
            client,
            f"{ASSIGNMENT_SERVICE_URL}/assignments",
            params={"classId": cid},
            headers=headers,
            default=[],
        )
        for cid in class_ids
    ])

    submission_by_assignment = {
        (s.get("assignmentId") or s.get("assignment_id")): s
        for s in submissions
    }
    class_by_id = {str(c["id"]): c for c in classes}

    out = []
    for cid, alist in zip(class_ids, assignments_lists):
        cls = class_by_id.get(str(cid), {})
        for a in (alist or []):
            out.append({
                "assignment": a,
                "className": cls.get("name", ""),
                "classCode": cls.get("code", ""),
                "submission": submission_by_assignment.get(str(a["id"])),
            })
    return out
