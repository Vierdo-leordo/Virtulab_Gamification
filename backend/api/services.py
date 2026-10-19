"""Business rules: rate limiting, audit, redeem, points, badges. No HTTP in here."""
import datetime as dt

from django.conf import settings
from django.db import IntegrityError, transaction
from django.utils import timezone

from lab_pack.token_codec import TokenError, parse_token
from lab_pack.verify_code import CodeError, ist_today, normalise_student_id, parse_code, verify_code

from .conf import cfg, level_for
from .errors import ApiError
from .models import (AuditLog, Badge, InvalidAttempt, Item, PointsLedger, QuizAttempt, Redemption, UserBadge)


# ------------------------------------------------------------------ audit & limits
def audit(actor, action, **detail):
    AuditLog.objects.create(actor=actor if getattr(actor, "pk", None) else None,
                            actor_text=getattr(actor, "username", "")[:60], action=action, detail_json=detail)


def log_invalid(kind, reason, student=None, student_id_text="", code_text="", ip=""):
    InvalidAttempt.objects.create(kind=kind, reason=reason, student=student if getattr(student, "pk", None) else None,
                                  student_id_text=student_id_text[:60], code_text=code_text[:80], ip=ip[:45])


def _window_start():
    return timezone.now() - dt.timedelta(seconds=cfg("rate_limit", "window_seconds", default=600))


def check_rate_limit(kind, student_id_text=None, ip=None, ip_factor=4):
    """Raise ApiError(429) if too many recent failures for this student id or ip."""
    limit = cfg("rate_limit", "max_failures", default=5)
    qs = InvalidAttempt.objects.filter(kind=kind, ts__gte=_window_start())
    over = bool(student_id_text) and qs.filter(student_id_text=student_id_text).count() >= limit
    over = over or (bool(ip) and qs.filter(ip=ip).count() >= limit * ip_factor)
    if over:
        raise ApiError(429, "rate_limited", retry_after=cfg("rate_limit", "window_seconds", default=600))


# --------------------------------------------------------------------------- points
def add_points(student, delta, reason, ref_id):
    """Idempotent: the same (student, reason, ref) can only ever be recorded once."""
    try:
        with transaction.atomic():
            PointsLedger.objects.create(student=student, delta=delta, reason=reason, ref_id=str(ref_id))
        return True
    except IntegrityError:
        return False


def total_points(student) -> int:
    from django.db.models import Sum
    return PointsLedger.objects.filter(student=student).aggregate(s=Sum("delta"))["s"] or 0


# ---------------------------------------------------------------------------- badges
def _graded(student):
    return QuizAttempt.objects.filter(student=student, is_practice=False, status="submitted")


def _rule_met(rule, student) -> bool:
    kind = rule.get("type")
    if kind == "first_redeem":
        return Redemption.objects.filter(student=student).exists()
    if kind == "perfect_score":
        return any(a.total > 0 and a.correct_count == a.total for a in _graded(student))
    if kind == "lab_flawless":
        return any(r.token_valid and (r.token_json or {}).get("att") == 1 and not (r.token_json or {}).get("mis")
                   and not (r.token_json or {}).get("wrong") for r in Redemption.objects.filter(student=student))
    if kind == "all_dynamic_correct":
        need = rule.get("min_dynamic", 1)
        for a in _graded(student):
            dyn = list(a.questions.filter(source="dynamic").prefetch_related("answers"))
            if len(dyn) >= need and all(any(x.is_correct for x in q.answers.all()) for q in dyn):
                return True
        return False
    if kind == "complete_items":
        done = set(_graded(student).values_list("redemption__item__key", flat=True))
        return set(rule.get("items", [])) <= done and bool(rule.get("items"))
    if kind == "complete_experiment":
        keys = set(Item.objects.filter(experiment__key=rule.get("experiment")).values_list("key", flat=True))
        done = set(_graded(student).values_list("redemption__item__key", flat=True))
        return bool(keys) and keys <= done
    if kind == "comeback":
        return any(r.token_valid and (r.token_json or {}).get("passed") and (r.token_json or {}).get("wrong")
                   for r in Redemption.objects.filter(student=student))
    return False


def evaluate_badges(student, ref="") -> list:
    """Award every badge whose rule is now met. Rules live in the database (loaded from badges.json)."""
    have = set(UserBadge.objects.filter(student=student).values_list("badge__key", flat=True))
    new = []
    for badge in Badge.objects.all():
        if badge.key in have or not _rule_met(badge.rule_json, student):
            continue
        try:
            with transaction.atomic():
                UserBadge.objects.create(student=student, badge=badge, ref=str(ref))
            new.append({"key": badge.key, "name": badge.name, "description": badge.description})
        except IntegrityError:
            pass
    return new


# ---------------------------------------------------------------------------- redeem
def _item_maps():
    items = list(Item.objects.all())
    return ({(i.cation, i.anion): i.key for i in items}, {i.key: (i.cation, i.anion) for i in items})


def redemption_payload(r: Redemption, already=False) -> dict:
    return {"redemption_id": r.id, "item": r.item.key, "formula": r.item.formula, "name": r.item.name,
            "cation": r.item.cation, "anion": r.item.anion, "token_valid": r.token_valid,
            "no_lab_data": r.no_lab_data, "token_error": r.token_error or None, "already": already}


def redeem_code(student, raw_code: str, raw_token: str | None, ip: str, today: dt.date | None = None) -> dict:
    """Spec 3.5 / 3.6 / S-03 / S-04. Raises ApiError with a reason code on any rejection."""
    if not settings.HMAC_SECRET:
        raise ApiError(503, "server_not_configured")
    sid = student.username
    check_rate_limit("code", student_id_text=sid, ip=ip)

    def reject(reason, status=400):
        log_invalid("code", reason, student, sid, str(raw_code), ip)
        audit(student, "redeem_rejected", reason=reason)
        raise ApiError(status, reason)

    try:
        parsed = parse_code(str(raw_code or ""))
    except CodeError:
        reject("bad_format")
    canonical = parsed.canonical

    existing = Redemption.objects.select_related("item").filter(code=canonical).first()
    if existing:
        if existing.student_id == student.id:
            return redemption_payload(existing, already=True)          # double click / retry: idempotent
        reject("already_used")

    pair_to_item, item_pairs = _item_maps()
    today = today or ist_today()
    window = cfg("code", "date_window_days", default=30)
    drift = cfg("code", "clock_drift_days", default=1)
    res = verify_code(canonical, sid, settings.HMAC_SECRET, today, window, drift, pair_to_item=pair_to_item)
    if not res.ok:
        if res.reason == "checksum_mismatch":
            wide = verify_code(canonical, sid, settings.HMAC_SECRET, today, 3650, drift, pair_to_item=pair_to_item)
            reject("expired" if wide.ok else "invalid_code")             # "not yours" cannot be told apart from forged
        reject("bad_format" if res.reason in ("unknown_pair", "bad_format") else res.reason)

    item = Item.objects.get(key=res.item_id)
    if Redemption.objects.filter(student=student, item=item).exists():
        reject("item_already_unlocked")

    token_valid, token_error, token_json = False, "", None
    if raw_token and str(raw_token).strip():
        try:
            token_json = parse_token(str(raw_token), settings.HMAC_SECRET, expected_student=sid,
                                     expected_code=canonical, items=item_pairs)
            token_valid = True
        except TokenError as e:
            token_error = e.reason
            log_invalid("token", e.reason, student, sid, canonical, ip)   # E5: ignored, but logged
    usable = token_valid and len((token_json or {}).get("tests", [])) >= 1
    try:
        with transaction.atomic():
            r = Redemption.objects.create(student=student, item=item, code=canonical, code_issue_date=res.issue_date,
                                          token_valid=token_valid, token_error=token_error,
                                          token_json=token_json if token_valid else None, no_lab_data=not usable)
    except IntegrityError:                                               # two requests raced: return the winner
        r = Redemption.objects.select_related("item").get(code=canonical)
        if r.student_id != student.id:
            reject("already_used")
        return redemption_payload(r, already=True)
    audit(student, "redeem_ok", item=item.key, token_valid=token_valid, no_lab_data=r.no_lab_data)
    out = redemption_payload(r)
    out["new_badges"] = evaluate_badges(student, ref=r.id)
    return out


# --------------------------------------------------------------------------- progress
def progress_for(student) -> dict:
    items = list(Item.objects.select_related("experiment").all())
    reds = {r.item_id: r for r in Redemption.objects.filter(student=student)}
    graded = {a.redemption_id: a for a in _graded(student)}
    open_attempts = {a.redemption_id: a for a in QuizAttempt.objects.filter(student=student, is_practice=False,
                                                                             status="in_progress")}
    grid = []
    for it in items:
        r = reds.get(it.id)
        status, score, attempt_id = "locked", None, None
        if r:
            status = "unlocked"
            a = graded.get(r.id)
            if a:
                status, score = "completed", {"correct": a.correct_count, "total": a.total,
                                              "percent": round(100 * a.correct_count / a.total) if a.total else 0}
                attempt_id = a.id
            elif r.id in open_attempts:
                attempt_id = open_attempts[r.id].id
        grid.append({"item": it.key, "formula": it.formula, "name": it.name, "cation": it.cation, "anion": it.anion,
                     "group": it.group_tag, "status": status, "score": score,
                     "redemption_id": r.id if r else None, "attempt_id": attempt_id,
                     "no_lab_data": bool(r and r.no_lab_data)})
    pts = total_points(student)
    earned = {ub.badge.key: ub.earned_at for ub in UserBadge.objects.filter(student=student).select_related("badge")}
    badges = [{"key": b.key, "name": b.name, "description": b.description, "earned": b.key in earned,
               "earned_at": earned.get(b.key)} for b in Badge.objects.all()]
    return {"points": pts, "level": level_for(pts), "items": grid, "badges": badges,
            "completed": sum(1 for g in grid if g["status"] == "completed"), "total_items": len(grid)}
