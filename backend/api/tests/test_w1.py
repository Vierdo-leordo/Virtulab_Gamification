"""W1 tests: auth, classes, redeem (spec scenarios E2 E3 E4 E5 E9), rate limits, sessions.
Run:  python backend\\manage.py test api -v 2"""
import datetime as dt

from django.test import TestCase, override_settings
from django.utils import timezone

from api.models import AuthToken, InvalidAttempt, Redemption, UserBadge, AuditLog
from lab_pack.verify_code import ist_today

from .helpers import (api, code_for, days_ago, load_all, make_class, make_teacher, register, token_for)

SID = "2411021061202"


class Base(TestCase):
    @classmethod
    def setUpTestData(cls):
        load_all()
        cls.teacher = make_teacher()
        cls.klass = make_class(cls.teacher)

    def student(self, sid=SID, pin="4321", klass=None):
        r = register((klass or self.klass).join_code, sid, pin)
        self.assertEqual(r.status_code, 201, r.data)
        return api(r.data["token"])


class TestAuth(Base):
    def test_register_normalises_student_id(self):
        r = register(self.klass.join_code, " 24 11021 061202 ")
        self.assertEqual(r.status_code, 201)
        self.assertEqual(r.data["me"]["id"], SID)
        self.assertEqual(r.data["me"]["classes"][0]["name"], "PU1-A")

    def test_register_validation(self):
        self.assertEqual(register("NOPE99").data["error"], "invalid_join_code")
        self.assertEqual(register(self.klass.join_code, pin="12").data["error"], "invalid_pin")
        self.assertEqual(register(self.klass.join_code, pin="abcd").data["error"], "invalid_pin")
        self.assertEqual(register(self.klass.join_code, student_id="a@b").data["error"], "invalid_student_id")
        self.assertEqual(register(self.klass.join_code, student_id="  ").data["error"], "invalid_student_id")
        self.assertEqual(register(self.klass.join_code, student_id="AB|C").data["error"], "invalid_student_id")

    def test_join_code_is_case_and_space_insensitive(self):
        r = register(" " + self.klass.join_code.lower() + " ")
        self.assertEqual(r.status_code, 201)

    def test_duplicate_registration_rejected(self):
        self.student()
        r = register(self.klass.join_code)
        self.assertEqual((r.status_code, r.data["error"]), (409, "already_registered"))

    def test_disabled_join_code_rejected(self):
        self.klass.join_enabled = False
        self.klass.save()
        self.assertEqual(register(self.klass.join_code).data["error"], "invalid_join_code")

    def test_login_ok_and_wrong_pin(self):
        self.student()
        ok = api().post("/api/auth/login", {"identifier": " 24 11021061202", "secret": "4321"}, format="json")
        self.assertEqual(ok.status_code, 200)
        bad = api().post("/api/auth/login", {"identifier": SID, "secret": "0000"}, format="json")
        self.assertEqual((bad.status_code, bad.data["error"]), (401, "invalid_credentials"))
        unknown = api().post("/api/auth/login", {"identifier": "NOBODY", "secret": "0000"}, format="json")
        self.assertEqual(unknown.data, bad.data)                       # no hint whether the ID exists

    def test_login_rate_limited_even_with_right_pin(self):
        self.student()
        for _ in range(5):
            api().post("/api/auth/login", {"identifier": SID, "secret": "9999"}, format="json")
        r = api().post("/api/auth/login", {"identifier": SID, "secret": "4321"}, format="json")
        self.assertEqual((r.status_code, r.data["error"]), (429, "rate_limited"))

    def test_teacher_login_and_roles(self):
        t = api().post("/api/auth/login", {"identifier": "T1@school.in", "secret": "teacher-pass-1"}, format="json")
        self.assertEqual(t.status_code, 200)
        self.assertEqual(t.data["me"]["role"], "teacher")
        teacher, student = api(t.data["token"]), self.student()
        self.assertEqual(teacher.get("/api/progress").status_code, 403)        # teacher cannot use student API
        self.assertEqual(student.get("/api/teacher/classes").status_code, 403)  # student cannot use teacher API
        self.assertEqual(api().get("/api/progress").status_code, 401)

    def test_student_cannot_login_through_teacher_path(self):
        self.student()
        r = api().post("/api/auth/login", {"identifier": "2411021061202@x.in", "secret": "4321"}, format="json")
        self.assertEqual(r.status_code, 401)

    def test_expired_and_logged_out_sessions(self):
        c = self.student()
        AuthToken.objects.update(expires=timezone.now() - dt.timedelta(seconds=1))
        self.assertEqual(c.get("/api/me").status_code, 401)
        c2 = api(register(self.klass.join_code, "ZZ1", "1111").data["token"])
        self.assertEqual(c2.post("/api/auth/logout").status_code, 200)
        self.assertEqual(c2.get("/api/me").status_code, 401)

    def test_change_pin(self):
        c = self.student()
        self.assertEqual(c.post("/api/auth/change-pin", {"old_pin": "0000", "new_pin": "5555"}, format="json").status_code, 400)
        self.assertEqual(c.post("/api/auth/change-pin", {"old_pin": "4321", "new_pin": "55"}, format="json").status_code, 400)
        self.assertEqual(c.post("/api/auth/change-pin", {"old_pin": "4321", "new_pin": "5555"}, format="json").status_code, 200)
        self.assertEqual(api().post("/api/auth/login", {"identifier": SID, "secret": "5555"}, format="json").status_code, 200)

    def test_student_joins_second_class(self):
        c = self.student()
        other = make_class(self.teacher, "PU1-B")
        r = c.post("/api/classes/join", {"join_code": other.join_code}, format="json")
        self.assertEqual(len(r.data["classes"]), 2)


class TestRedeem(Base):
    def test_happy_path_with_token(self):
        c = self.student()
        code = code_for(SID, "cuso4")
        r = c.post("/api/redeem", {"code": code, "token": token_for(SID, "cuso4", code)}, format="json")
        self.assertEqual(r.status_code, 201, r.data)
        self.assertEqual((r.data["item"], r.data["token_valid"], r.data["no_lab_data"]), ("cuso4", True, False))
        self.assertEqual([b["key"] for b in r.data["new_badges"]], ["first_spark", "lab_perfectionist"])  # flawless lab run
        grid = {i["item"]: i for i in c.get("/api/progress").data["items"]}
        self.assertEqual(grid["cuso4"]["status"], "unlocked")
        self.assertEqual(grid["nacl"]["status"], "locked")
        self.assertEqual(len(grid), 12)

    def test_typing_variants_accepted(self):
        c = self.student()
        code = code_for(SID, "nacl", nonce="0000")
        sloppy = " " + code.lower().replace("-0000-", "-oooo-").replace("-", "\u2013") + " "
        r = c.post("/api/redeem", {"code": sloppy}, format="json")
        self.assertEqual(r.status_code, 201, r.data)

    def test_no_token_means_no_lab_data_E4(self):
        c = self.student()
        r = c.post("/api/redeem", {"code": code_for(SID, "nacl")}, format="json")
        self.assertEqual((r.data["token_valid"], r.data["no_lab_data"]), (False, True))
        self.assertIsNone(r.data["token_error"])

    def test_bad_token_ignored_but_logged_E5(self):
        c = self.student()
        code = code_for(SID, "nacl")
        tok = token_for(SID, "nacl", code)
        head, body, sig = tok.split(".")
        forged = ".".join([head, body[:-2] + ("AA" if body[-2:] != "AA" else "BB"), sig])
        r = c.post("/api/redeem", {"code": code, "token": forged}, format="json")
        self.assertEqual(r.status_code, 201)                       # redeem still succeeds
        self.assertEqual((r.data["token_valid"], r.data["no_lab_data"], r.data["token_error"]), (False, True, "bad_signature"))
        self.assertTrue(InvalidAttempt.objects.filter(kind="token", reason="bad_signature").exists())
        self.assertIsNone(Redemption.objects.get().token_json)      # nothing from a bad token is stored

    def test_token_for_other_student_ignored(self):
        c = self.student()
        code = code_for(SID, "nacl")
        other_tok = token_for("SOMEONEELSE", "nacl", code)
        r = c.post("/api/redeem", {"code": code, "token": other_tok}, format="json")
        self.assertFalse(r.data["token_valid"])
        self.assertTrue(r.data["no_lab_data"])
        self.assertIn(r.data["token_error"], ("wrong_student", "wrong_code"))

    def test_token_with_no_tests_counts_as_too_small(self):
        c = self.student()
        code = code_for(SID, "nacl")
        r = c.post("/api/redeem", {"code": code, "token": token_for(SID, "nacl", code, tests=[])}, format="json")
        self.assertEqual((r.data["token_valid"], r.data["no_lab_data"]), (True, True))

    def test_code_for_another_student_E2(self):
        c = self.student()
        r = c.post("/api/redeem", {"code": code_for("SOMEONEELSE", "nacl")}, format="json")
        self.assertEqual((r.status_code, r.data["error"]), (400, "invalid_code"))
        self.assertTrue(InvalidAttempt.objects.filter(kind="code", reason="invalid_code", student_id_text=SID).exists())
        self.assertTrue(AuditLog.objects.filter(action="redeem_rejected").exists())

    def test_reuse_by_another_student_E3(self):
        a = self.student()
        b = self.student("2411021061203", "1234")
        code = code_for(SID, "nacl")
        self.assertEqual(a.post("/api/redeem", {"code": code}, format="json").status_code, 201)
        r = b.post("/api/redeem", {"code": code}, format="json")
        self.assertEqual((r.status_code, r.data["error"]), (400, "already_used"))
        self.assertEqual(Redemption.objects.count(), 1)             # original untouched
        self.assertEqual(Redemption.objects.get().student.username, SID)

    def test_same_student_retry_is_idempotent(self):
        c = self.student()
        code = code_for(SID, "nacl")
        first = c.post("/api/redeem", {"code": code}, format="json")
        again = c.post("/api/redeem", {"code": code}, format="json")
        self.assertEqual((first.status_code, again.status_code), (201, 200))
        self.assertTrue(again.data["already"])
        self.assertEqual(first.data["redemption_id"], again.data["redemption_id"])
        self.assertEqual(Redemption.objects.count(), 1)
        self.assertEqual(UserBadge.objects.count(), 1)

    def test_expired_code(self):
        c = self.student()
        r = c.post("/api/redeem", {"code": code_for(SID, "nacl", issue=days_ago(40))}, format="json")
        self.assertEqual(r.data["error"], "expired")
        ok = c.post("/api/redeem", {"code": code_for(SID, "nacl", issue=days_ago(30))}, format="json")
        self.assertEqual(ok.status_code, 201)                      # oldest allowed day

    def test_forged_and_malformed_codes(self):
        c = self.student()
        good = code_for(SID, "nacl")
        flipped = good[:-1] + ("0" if good[-1] != "0" else "1")
        self.assertEqual(c.post("/api/redeem", {"code": flipped}, format="json").data["error"], "invalid_code")
        self.assertEqual(c.post("/api/redeem", {"code": "hello"}, format="json").data["error"], "bad_format")
        self.assertEqual(c.post("/api/redeem", {"code": ""}, format="json").data["error"], "bad_format")
        self.assertEqual(c.post("/api/redeem", {"code": "VL-NA-SO4-7K3Q-9F2A"}, format="json").data["error"], "bad_format")
        self.assertEqual(c.post("/api/redeem", {}, format="json").data["error"], "bad_format")

    def test_second_code_for_same_salt_rejected(self):
        c = self.student()
        self.assertEqual(c.post("/api/redeem", {"code": code_for(SID, "nacl", nonce="AAAA")}, format="json").status_code, 201)
        r = c.post("/api/redeem", {"code": code_for(SID, "nacl", nonce="BBBB")}, format="json")
        self.assertEqual(r.data["error"], "item_already_unlocked")

    def test_rate_limit_after_five_failures(self):
        c = self.student()
        for _ in range(5):
            self.assertEqual(c.post("/api/redeem", {"code": "VL-NA-CL-AAAA-BBBB"}, format="json").status_code, 400)
        r = c.post("/api/redeem", {"code": code_for(SID, "nacl")}, format="json")      # even a valid code is held back
        self.assertEqual((r.status_code, r.data["error"]), (429, "rate_limited"))
        self.assertEqual(Redemption.objects.count(), 0)

    def test_old_failures_do_not_count(self):
        c = self.student()
        for _ in range(5):
            c.post("/api/redeem", {"code": "VL-NA-CL-AAAA-BBBB"}, format="json")
        InvalidAttempt.objects.update(ts=timezone.now() - dt.timedelta(seconds=700))
        self.assertEqual(c.post("/api/redeem", {"code": code_for(SID, "nacl")}, format="json").status_code, 201)

    @override_settings(HMAC_SECRET="")
    def test_unconfigured_secret_fails_safe(self):
        c = self.student()
        r = c.post("/api/redeem", {"code": "VL-NA-CL-AAAA-BBBB"}, format="json")
        self.assertEqual((r.status_code, r.data["error"]), (503, "server_not_configured"))

    def test_all_twelve_items_redeemable_and_badge_progress(self):
        c = self.student()
        keys = [i["item"] for i in c.get("/api/progress").data["items"]]
        for k in keys:
            self.assertEqual(c.post("/api/redeem", {"code": code_for(SID, k)}, format="json").status_code, 201, k)
        self.assertEqual(c.get("/api/progress").data["total_items"], 12)
        self.assertEqual(Redemption.objects.count(), 12)

    def test_error_shape_is_uniform(self):
        c = self.student()
        r = c.post("/api/redeem", {"code": "x"}, format="json")
        self.assertEqual(set(r.data), {"error"})


class TestTeacherIsolation(Base):
    def setUp(self):
        self.t2 = make_teacher("t2@school.in")
        self.c1 = api(api().post("/api/auth/login", {"identifier": "t1@school.in", "secret": "teacher-pass-1"}, format="json").data["token"])
        self.c2 = api(api().post("/api/auth/login", {"identifier": "t2@school.in", "secret": "teacher-pass-1"}, format="json").data["token"])
        self.student()

    def test_lists_only_own_classes(self):
        self.assertEqual(len(self.c1.get("/api/teacher/classes").data), 1)
        self.assertEqual(self.c2.get("/api/teacher/classes").data, [])

    def test_other_teacher_gets_404_everywhere_E9(self):
        cid = self.klass.id
        self.assertEqual(self.c2.get(f"/api/teacher/classes/{cid}/students").status_code, 404)
        self.assertEqual(self.c2.patch(f"/api/teacher/classes/{cid}", {"name": "hacked"}, format="json").status_code, 404)
        self.assertEqual(self.c2.post(f"/api/teacher/classes/{cid}/students/{SID}/reset-pin").status_code, 404)
        self.klass.refresh_from_db()
        self.assertEqual(self.klass.name, "PU1-A")
        self.assertEqual(api().post("/api/auth/login", {"identifier": SID, "secret": "4321"}, format="json").status_code, 200)

    def test_owner_manages_class_and_roster(self):
        r = self.c1.post("/api/teacher/classes", {"name": "PU2-B", "grade": "12", "section": "B"}, format="json")
        self.assertEqual(r.status_code, 201)
        self.assertEqual(len(r.data["join_code"]), 6)
        old = self.klass.join_code
        rot = self.c1.patch(f"/api/teacher/classes/{self.klass.id}", {"rotate_join_code": True}, format="json")
        self.assertNotEqual(rot.data["join_code"], old)
        self.assertEqual(register(old, "NEW1", "1111").data["error"], "invalid_join_code")
        roster = self.c1.get(f"/api/teacher/classes/{self.klass.id}/students").data
        self.assertEqual([s["student_id"] for s in roster], [SID])

    def test_reset_pin_forces_change_and_logs_out(self):
        old = api(register(self.klass.join_code, "RESET1", "1111").data["token"])
        r = self.c1.post(f"/api/teacher/classes/{self.klass.id}/students/RESET1/reset-pin")
        temp = r.data["temporary_pin"]
        self.assertEqual(len(temp), 6)
        self.assertEqual(old.get("/api/me").status_code, 401)          # old sessions ended
        login = api().post("/api/auth/login", {"identifier": "RESET1", "secret": temp}, format="json")
        self.assertTrue(login.data["me"]["must_change_pin"])
        self.assertEqual(api().post("/api/auth/login", {"identifier": "RESET1", "secret": "1111"}, format="json").status_code, 401)
