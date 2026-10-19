/**
 * frontend/src/components/IonDisplay.jsx
 * Chemistry display components: IonChip, FormattedFormula, and SaltCard.
 * Cation chips: Blue style.
 * Anion chips: Orange style.
 * Subscripts & superscripts correctly rendered.
 */
import { CATIONS, ANIONS } from "../utils/chemistry.js";

/**
 * Format chemical formula string with proper subscripts.
 * e.g. "CuSO4" -> "CuSO₄", "Al2(SO4)3" -> "Al₂(SO₄)₃"
 */
export function FormattedFormula({ formula }) {
  if (!formula) return null;

  // Split formula into letters/parentheses and numbers to wrap numbers in <sub>
  const parts = formula.split(/(\d+)/);
  return (
    <span className="font-monospace fw-bold">
      {parts.map((part, i) =>
        /^\d+$/.test(part) ? <sub key={i}>{part}</sub> : <span key={i}>{part}</span>
      )}
    </span>
  );
}

/**
 * Display an ion with formula and charge.
 * e.g. Na+ -> Na⁺, SO4 2- -> SO₄²⁻
 */
export function FormattedIonSymbol({ ionKey, type }) {
  const meta = type === "cation" ? CATIONS[ionKey] : ANIONS[ionKey];
  if (!meta) return <span>{ionKey}</span>;

  // Render specific symbol
  switch (meta.key) {
    case "NA":
      return <span>Na<sup>+</sup></span>;
    case "NH4":
      return <span>NH<sub>4</sub><sup>+</sup></span>;
    case "CU":
      return <span>Cu<sup>2+</sup></span>;
    case "FE2":
      return <span>Fe<sup>2+</sup></span>;
    case "FE3":
      return <span>Fe<sup>3+</sup></span>;
    case "AL":
      return <span>Al<sup>3+</sup></span>;
    case "ZN":
      return <span>Zn<sup>2+</sup></span>;
    case "BA":
      return <span>Ba<sup>2+</sup></span>;
    case "CA":
      return <span>Ca<sup>2+</sup></span>;
    case "MG":
      return <span>Mg<sup>2+</sup></span>;
    case "PB":
      return <span>Pb<sup>2+</sup></span>;
    case "CL":
      return <span>Cl<sup>-</sup></span>;
    case "SO4":
      return <span>SO<sub>4</sub><sup>2-</sup></span>;
    case "CO3":
      return <span>CO<sub>3</sub><sup>2-</sup></span>;
    case "NO3":
      return <span>NO<sub>3</sub><sup>-</sup></span>;
    default:
      return <span>{meta.symbol || ionKey}</span>;
  }
}

/**
 * Ion chip component.
 * Blue style for cations, Orange style for anions.
 */
export function IonChip({ ionKey, type, showName = true }) {
  const meta = type === "cation" ? CATIONS[ionKey] : ANIONS[ionKey];
  const chipClass = type === "cation" ? "ion-chip-cation" : "ion-chip-anion";

  return (
    <span className={`ion-chip ${chipClass}`}>
      <span className="ion-chip-symbol">
        <FormattedIonSymbol ionKey={ionKey} type={type} />
      </span>
      {showName && meta?.name && (
        <span className="ion-chip-name">{meta.name}</span>
      )}
    </span>
  );
}
