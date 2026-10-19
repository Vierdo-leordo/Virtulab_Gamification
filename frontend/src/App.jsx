/**
 * frontend/src/App.jsx
 * Blank home page — W0a scaffold.
 * All user-visible strings come from the i18n catalogue (HARD RULE 7).
 */
import { useTranslation } from "react-i18next";

export default function App() {
  const { t } = useTranslation();

  return (
    <div className="container py-5 text-center">
      <h1 className="display-4 fw-bold mb-3">{t("app_name")}</h1>
      <p className="lead text-muted">{t("app_tagline")}</p>
    </div>
  );
}
