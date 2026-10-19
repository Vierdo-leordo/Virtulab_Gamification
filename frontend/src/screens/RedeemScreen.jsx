/**
 * frontend/src/screens/RedeemScreen.jsx
 * Placeholder for code redemption (Task U2).
 */
import { useTranslation } from "react-i18next";
import { Link } from "react-router-dom";

export default function RedeemScreen() {
  const { t } = useTranslation();

  return (
    <div className="redeem-screen pb-5">
      <div className="d-flex align-items-center mb-3">
        <Link to="/" className="btn btn-sm btn-outline-secondary me-2">
          &larr; {t("common.back")}
        </Link>
        <h1 className="h4 fw-bold mb-0">{t("redeem.title")}</h1>
      </div>
      <div className="card border-0 shadow-sm p-4 text-center">
        <p className="text-muted mb-0">{t("redeem.placeholder_text")}</p>
      </div>
    </div>
  );
}
