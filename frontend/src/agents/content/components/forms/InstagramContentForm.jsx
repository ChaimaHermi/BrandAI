import { CONTENT_TYPE_OPTIONS, TONE_OPTIONS, PLATFORMS } from "../../constants";
import { FieldLabel, inputClass, ToggleRow } from "../formFields";

export function InstagramContentForm({ values, onChange }) {
  return (
    <div className="flex flex-col gap-4">
      <div>
        <FieldLabel htmlFor="ig-subject">Sujet du post</FieldLabel>
        <textarea
          id="ig-subject"
          rows={3}
          value={values.subject}
          onChange={(e) => onChange({ subject: e.target.value })}
          placeholder="De quoi voulez-vous parler ?"
          className={inputClass + " min-h-[88px] resize-y"}
        />
      </div>

      <div>
        <FieldLabel htmlFor="ig-tone">Ton</FieldLabel>
        <select
          id="ig-tone"
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
        <FieldLabel htmlFor="ig-type">Type de contenu</FieldLabel>
        <select
          id="ig-type"
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

      <ToggleRow
        id="ig-hashtags"
        label="Hashtags"
        description="Inclure des hashtags pertinents (recommandé pour Instagram)."
        checked={values.hashtagsEnabled}
        onChange={(v) => onChange({ hashtagsEnabled: v })}
      />

      <ToggleRow
        id="ig-image"
        label="Image"
        description="Générer une image d’illustration avec le post."
        checked={values.includeImage}
        onChange={(v) => onChange({ includeImage: v })}
      />

      <input type="hidden" name="platform" value={PLATFORMS.instagram} readOnly />
    </div>
  );
}

export default InstagramContentForm;
