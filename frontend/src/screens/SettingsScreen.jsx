/**
 * frontend/src/screens/SettingsScreen.jsx
 * Settings page for student: profile details, language preference,
 * change pin button, and logout button.
 */
import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { useSession } from "../session.jsx";
import LanguageSelector from "../components/LanguageSelector.jsx";

export default function SettingsScreen() {
  const { t } = useTranslation();
  const { me, logout } = useSession();

  return (
    <div className="settings-screen pb-5">
      <h1 className="h4 fw-bold mb-4">{t("settings.title")}</h1>

      {/* Profile Section */}
      <div className="card border-0 shadow-sm mb-3">
        <div className="card-header bg-transparent fw-semibold py-3">
          {t("settings.profile_section")}
        </div>
        <div className="card-body">
          <div className="mb-3">
            <span className="text-muted small d-block">{t("settings.display_name")}</span>
            <span className="fw-semibold fs-6">{me?.display_name || "—"}</span>
          </div>
          <div className="mb-3">
            <span className="text-muted small d-block">{t("settings.student_id")}</span>
            <span className="font-monospace fw-semibold fs-6">{me?.id}</span>
          </div>
        </div>
      </div>

      {/* Enrolled Classes Section */}
      <div className="card border-0 shadow-sm mb-3">
        <div className="card-header bg-transparent fw-semibold py-3">
          {t("settings.classes_section")}
        </div>
        <div className="card-body">
          {me?.classes && me.classes.length > 0 ? (
            <ul className="list-unstyled mb-0">
              {me.classes.map((cls) => (
                <li key={cls.id} className="py-1 fw-medium">
                  {cls.name}
                </li>
              ))}
            </ul>
          ) : (
            <span className="text-muted small">{t("settings.no_classes")}</span>
          )}
        </div>
      </div>

      {/* Language Section */}
      <div className="card border-0 shadow-sm mb-3">
        <div className="card-header bg-transparent fw-semibold py-3">
          {t("settings.language_section")}
        </div>
        <div className="card-body">
          <LanguageSelector variant="buttons" />
        </div>
      </div>

      {/* Security Section */}
      <div className="card border-0 shadow-sm mb-4">
        <div className="card-header bg-transparent fw-semibold py-3">
          {t("settings.security_section")}
        </div>
        <div className="card-body">
          <Link
            to="/change-pin"
            className="btn btn-outline-primary w-100 fw-semibold min-touch-target"
          >
            {t("settings.change_pin_btn")}
          </Link>
        </div>
      </div>

      {/* Logout */}
      <button
        type="button"
        className="btn btn-danger btn-lg w-100 fw-bold min-touch-target shadow-sm"
        onClick={logout}
      >
        {t("settings.logout_btn")}
      </button>
    </div>
  );
}
