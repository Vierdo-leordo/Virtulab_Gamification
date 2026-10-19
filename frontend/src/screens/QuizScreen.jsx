/**
 * frontend/src/screens/QuizScreen.jsx
 * Placeholder for quiz flow.
 */
import { useTranslation } from "react-i18next";
import { useParams, Link } from "react-router-dom";

export default function QuizScreen() {
  const { t } = useTranslation();
  const { id } = useParams();

  return (
    <div className="quiz-screen pb-5">
      <div className="d-flex align-items-center mb-3">
        <Link to="/" className="btn btn-sm btn-outline-secondary me-2">
          &larr; {t("common.back")}
        </Link>
        <h1 className="h4 fw-bold mb-0">{t("quiz.title")}</h1>
      </div>
      <div className="card border-0 shadow-sm p-4 text-center">
        <p className="text-muted mb-2">{t("quiz.placeholder_text")}</p>
        <span className="badge bg-light text-dark font-monospace">Attempt ID: {id}</span>
      </div>
    </div>
  );
}
