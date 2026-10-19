/**
 * frontend/src/screens/BadgesScreen.jsx
 * Badges screen displaying earned achievements.
 */
import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import api from "../api.js";

export default function BadgesScreen() {
  const { t } = useTranslation();
  const [badges, setBadges] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let isMounted = true;
    async function loadBadges() {
      try {
        const data = await api.get("/progress");
        if (isMounted && data.badges) {
          setBadges(data.badges);
        }
      } catch (err) {
        console.error("Failed to load badges:", err);
      } finally {
        if (isMounted) setLoading(false);
      }
    }
    loadBadges();
    return () => {
      isMounted = false;
    };
  }, []);

  return (
    <div className="badges-screen pb-5">
      <h1 className="h4 fw-bold mb-4">{t("badges.title")}</h1>

      {loading ? (
        <div className="text-center py-4 text-muted small">{t("common.loading")}</div>
      ) : badges.length === 0 ? (
        <div className="card border-0 shadow-sm p-4 text-center">
          <p className="text-muted mb-0">{t("badges.placeholder_text")}</p>
        </div>
      ) : (
        <div className="d-flex flex-column gap-3">
          {badges.map((b) => (
            <div
              key={b.key}
              className={`card border-0 shadow-sm p-3 ${
                b.earned ? "bg-white" : "bg-light opacity-75"
              }`}
            >
              <div className="d-flex justify-content-between align-items-center">
                <div>
                  <h2 className="h6 fw-bold mb-1">{b.name}</h2>
                  <p className="small text-muted mb-0">{b.description}</p>
                </div>
                <span className={`badge ${b.earned ? "bg-success" : "bg-secondary"}`}>
                  {b.earned ? "Earned" : "Locked"}
                </span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
