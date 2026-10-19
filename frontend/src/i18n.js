/**
 * frontend/src/i18n.js
 * Initialises react-i18next with the English catalogue.
 * To add a language: import its JSON and add to resources.
 */
import i18n from "i18next";
import { initReactI18next } from "react-i18next";
import en from "./locales/en.json";

i18n.use(initReactI18next).init({
  resources: {
    en: en,
  },
  lng: "en",           // default language
  fallbackLng: "en",
  interpolation: {
    escapeValue: false, // React already escapes
  },
});

export default i18n;
