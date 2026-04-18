import { CONTENT_TYPE_OPTIONS, CTA_OPTIONS, TONE_OPTIONS, PLATFORMS } from "../../constants";
import { FieldLabel, inputClass, ToggleRow } from "../formFields";

export function FacebookContentForm({ values, onChange }) {
  return (
    <div className="flex flex-col gap-4">
      <div>
        <FieldLabel htmlFor="fb-subject">Sujet du post</FieldLabel>
        <textarea
          id="fb-subject"
          rows={3}
          value={values.subject}
          onChange={(e) => onChange({ subject: e.target.value })}
          placeholder="De quoi voulez-vous parler ?"
          className={inputClass + " min-h-[88px] resize-y"}
        />
      </div>

      <div>
        <FieldLabel htmlFor="fb-tone">Ton</FieldLabel>
        <select
          id="fb-tone"
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
      </div>

      <div>
        <FieldLabel htmlFor="fb-type">Type de contenu</FieldLabel>
        <select
          id="fb-type"
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
        <FieldLabel htmlFor="fb-cta">Call to action</FieldLabel>
        <select
          id="fb-cta"
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
        id="fb-image"
        label="Image"
        description="Optionnel — générer une image d’illustration."
        checked={values.includeImage}
        onChange={(v) => onChange({ includeImage: v })}
      />

      <input type="hidden" name="platform" value={PLATFORMS.facebook} readOnly />
    </div>
  );
}

export default FacebookContentForm;
