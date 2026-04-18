import { CONTENT_TYPE_OPTIONS, CTA_OPTIONS, TONE_OPTIONS, PLATFORMS } from "../../constants";
import { FieldLabel, inputClass, ToggleRow } from "../formFields";

export function LinkedInContentForm({ values, onChange }) {
  return (
    <div className="flex flex-col gap-4">
      <div>
        <FieldLabel htmlFor="li-subject">Sujet du post</FieldLabel>
        <textarea
          id="li-subject"
          rows={3}
          value={values.subject}
          onChange={(e) => onChange({ subject: e.target.value })}
          placeholder="De quoi voulez-vous parler ?"
          className={inputClass + " min-h-[88px] resize-y"}
        />
      </div>

      <div>
        <FieldLabel htmlFor="li-tone">Ton</FieldLabel>
        <select
          id="li-tone"
          value={values.tone}
          onChange={(e) => onChange({ tone: e.target.value })}
          className={inputClass}
        >
          {TONE_OPTIONS.map((o) => (
            <option key={o.id} value={o.id}>
              {o.label}
            </option>
          ))}
        </select>
        <p className="mt-1 text-[11px] text-ink-subtle">
          Par défaut : ton professionnel, adapté à LinkedIn (pas de hashtags en masse).
        </p>
      </div>

      <div>
        <FieldLabel htmlFor="li-type">Type de contenu</FieldLabel>
        <select
          id="li-type"
          value={values.contentType}
          onChange={(e) => onChange({ contentType: e.target.value })}
          className={inputClass}
        >
          {CONTENT_TYPE_OPTIONS.map((o) => (
            <option key={o.id} value={o.id}>
              {o.label}
            </option>
          ))}
        </select>
      </div>

      <div>
        <FieldLabel htmlFor="li-cta">Call to action</FieldLabel>
        <select
          id="li-cta"
          value={values.callToAction}
          onChange={(e) => onChange({ callToAction: e.target.value })}
          className={inputClass}
        >
          {CTA_OPTIONS.map((o) => (
            <option key={o.id} value={o.id}>
              {o.label}
            </option>
          ))}
        </select>
      </div>

      <ToggleRow
        id="li-image"
        label="Image"
        description="Optionnel — image d’illustration pour le post."
        checked={values.includeImage}
        onChange={(v) => onChange({ includeImage: v })}
      />

      <input type="hidden" name="platform" value={PLATFORMS.linkedin} readOnly />
    </div>
  );
}

export default LinkedInContentForm;
