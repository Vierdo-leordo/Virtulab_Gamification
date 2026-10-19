/**
 * frontend/src/screens/HomeScreen.jsx
 * Student home dashboard.
 * Shows student profile info, enrolled class, redeem CTA,
 * points & level overview, and list of salt items with ion chips.
 */
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { useSession } from "../session.jsx";
import api from "../api.js";
import { FormattedFormula, IonChip } from "../components/IonDisplay.jsx";

export default function HomeScreen() {
  const { t } = useTranslation();
  const { me } = useSession();

  const [progress, setProgress] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let isMounted = true;
    async function loadProgress() {
      try {
        const data = await api.get("/progress");
        if (isMounted) {
          setProgress(data);
        }
      } catch (err) {
        console.error("Failed to load progress:", err);
      } finally {
        if (isMounted) setLoading(false);
      }
    }
    loadProgress();
    return () => {
      isMounted = false;
    };
  }, []);

  const className = me?.classes && me.classes.length > 0 ? me.classes[0].name : null;

  return (
    <div className="home-screen pb-5">
      {/* Welcome Banner */}
      <div className="card border-0 shadow-sm mb-4 bg-primary text-white overflow-hidden">
        <div className="card-body p-4">
          <h1 className="h4 fw-bold mb-1">
            {t("home.welcome", { name: me?.display_name || me?.id || "Student" })}
          </h1>
          <div className="d-flex flex-wrap gap-2 text-white-50 small mt-2">
            <span className="badge bg-white text-primary fw-medium px-2 py-1">
              {t("home.student_id", { id: me?.id })}
            </span>
            <span className="badge bg-light bg-opacity-25 text-white fw-medium px-2 py-1">
              {className ? t("home.enrolled_class", { name: className }) : t("home.not_enrolled")}
            </span>
          </div>
        </div>
      </div>

      {/* Quick Action: Redeem Code */}
      <div className="card border-0 shadow-sm mb-4 bg-light">
        <div className="card-body p-4 text-center">
          <p className="fw-medium mb-3">{t("home.redeem_prompt")}</p>
          <Link
            to="/redeem"
            className="btn btn-warning btn-lg fw-bold px-4 py-2 min-touch-target shadow-sm"
          >
            {t("home.redeem_action")}
          </Link>
        </div>
      </div>

      {/* Progress Stats */}
      <div className="mb-4">
        <h2 className="h5 fw-bold mb-3">{t("home.overview")}</h2>
        <div className="row g-2">
          <div className="col-4">
            <div className="card border-0 shadow-sm text-center p-3 h-100">
              <span className="text-muted small">{t("home.points")}</span>
              <span className="fs-3 fw-bold text-primary">
                {progress?.points ?? 0}
              </span>
            </div>
          </div>
          <div className="col-4">
            <div className="card border-0 shadow-sm text-center p-3 h-100">
              <span className="text-muted small">{t("home.level")}</span>
              <span className="fs-5 fw-bold text-success text-truncate">
                {progress?.level?.name || "1"}
              </span>
            </div>
          </div>
          <div className="col-4">
            <div className="card border-0 shadow-sm text-center p-3 h-100">
              <span className="text-muted small">{t("home.completed")}</span>
              <span className="fs-3 fw-bold text-dark">
                {progress?.completed ?? 0} / {progress?.total_items ?? 12}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Salts List */}
      {progress?.items && progress.items.length > 0 && (
        <div className="salt-cards-list mb-4">
          <h2 className="h5 fw-bold mb-3">Salts</h2>
          <div className="d-flex flex-column gap-3">
            {progress.items.map((item) => (
              <div key={item.item} className="card border-0 shadow-sm p-3">
                <div className="d-flex justify-content-between align-items-start mb-2">
                  <div>
                    <h3 className="h6 fw-bold mb-0">
                      <FormattedFormula formula={item.formula} />
                    </h3>
                    <div className="text-muted small">{item.name}</div>
                  </div>
                  <span
                    className={`badge ${
                      item.status === "completed"
                        ? "bg-success"
                        : item.status === "unlocked"
                        ? "bg-warning text-dark"
                        : "bg-secondary"
                    }`}
                  >
                    {item.status}
                  </span>
                </div>
                <div className="d-flex flex-wrap gap-2 mt-2">
                  <IonChip ionKey={item.cation} type="cation" />
                  <IonChip ionKey={item.anion} type="anion" />
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {loading && (
        <div className="text-center py-4 text-muted small">
          {t("common.loading")}
        </div>
      )}
    </div>
  );
}
