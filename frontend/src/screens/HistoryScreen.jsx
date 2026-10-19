/**
 * frontend/src/screens/HistoryScreen.jsx
 * History screen displaying attempts and points ledger.
 */
import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import api from "../api.js";
import { FormattedFormula } from "../components/IonDisplay.jsx";

export default function HistoryScreen() {
  const { t } = useTranslation();
  const [history, setHistory] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let isMounted = true;
    async function loadHistory() {
      try {
        const data = await api.get("/history");
        if (isMounted) {
          setHistory(data);
        }
      } catch {
        // /history might not exist yet before quiz backend step
      } finally {
        if (isMounted) setLoading(false);
      }
    }
    loadHistory();
    return () => {
      isMounted = false;
    };
  }, []);

  return (
    <div className="history-screen pb-5">
      <h1 className="h4 fw-bold mb-4">{t("history.title")}</h1>

      {loading ? (
        <div className="text-center py-4 text-muted small">{t("common.loading")}</div>
      ) : !history || (!history.attempts?.length && !history.ledger?.length) ? (
        <div className="card border-0 shadow-sm p-4 text-center">
          <p className="text-muted mb-0">{t("history.placeholder_text")}</p>
        </div>
      ) : (
        <div className="d-flex flex-column gap-3">
          {history.attempts?.map((a) => (
            <div key={a.attempt_id} className="card border-0 shadow-sm p-3">
              <div className="d-flex justify-content-between align-items-center">
                <div>
                  <h2 className="h6 fw-bold mb-1">
                    <FormattedFormula formula={a.formula} /> ({a.name})
                  </h2>
                  <span className="small text-muted">{a.submitted_at}</span>
                </div>
                <span className="badge bg-primary fs-6">
                  {a.correct}/{a.total} ({a.percent}%)
                </span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
