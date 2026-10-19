# docs/DECISIONS.md — VirtuLab Portal Decision Log

This file records every significant technical decision and the reason for it.
A different model or developer reading this later should understand *why*, not
just *what*.

| # | Decision | Chosen | Alternatives considered | Reason |
|---|---|---|---|---|
| D1 | Backend framework | Django 6.1.2 + DRF 3.18.3 | Flask | Spec §3.2 preference; auth, ORM, admin come free |
| D2 | Python requirement | 3.14 | 3.12, 3.13 | User's installed version; both Django 6.1.2 and DRF 3.18.3 officially support it |
| D3 | DRF version pinned to 3.18.3 (not 3.16.x) | 3.18.3 | 3.16.1 | 3.18.3 is the first DRF release to officially list Python 3.14 in its trove classifiers |
| D4 | Frontend build tool | Vite 6 | Create React App | CRA is unmaintained; Vite is faster and the spec recommends it |
| D5 | Bootstrap delivery | npm package | CDN | CDN creates an external dependency; npm bundle works offline (spec §6 performance req) |
| D6 | i18n library | react-i18next | Custom | Approved explicitly; wires the i18n catalogue per HARD RULE 7 |
| D7 | question radical field | From each question's own tag only | Copied from salt header | User note 2: "radical comes from its own tag only" |
| D8 | test_type inference | Keyword heuristics → unclassified fallback | Silence / guess | OVERRIDE 3: never silently guess; every unclassified question is listed in the report |
| D9 | Report encoding | UTF-8 to file; cp1252-safe to terminal | Always UTF-8 | Windows PowerShell terminal is cp1252; the report file itself is UTF-8 |
| D10 | SECRET_KEY in settings | `os.environ["SECRET_KEY"]` — raises if missing | Default fallback | HARD RULE 4: secrets only in env vars; a missing key should fail loudly, not silently |
| D11 | TIME_ZONE | Asia/Kolkata (IST) | UTC | Code date-window is calculated in IST per spec §3.5 |
