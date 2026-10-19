/**
 * frontend/src/screens/ResultScreen.jsx
 * Placeholder for quiz results.
 */
import { useTranslation } from "react-i18next";
import { useParams, Link } from "react-router-dom";

export default function ResultScreen() {
  const { t } = useTranslation();
  const { id } = useParams();

  return (
    <div className="result-screen pb-5">
      <div className="d-flex align-items-center mb-3">
        <Link to="/" className="btn btn-sm btn-outline-secondary me-2">
          &larr; {t("common.back")}
        </Link>
        <h1 className="h4 fw-bold mb-0">{t("result.title")}</h1>
      </div>
      <div className="card border-0 shadow-sm p-4 text-center">
        <p className="text-muted mb-2">{t("result.placeholder_text")}</p>
        <span className="badge bg-light text-dark font-monospace">Attempt ID: {id}</span>
      </div>
    </div>
  );
}
