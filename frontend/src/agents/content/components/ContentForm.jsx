import { PLATFORMS } from "../constants";
import { InstagramContentForm } from "./forms/InstagramContentForm";
import { FacebookContentForm } from "./forms/FacebookContentForm";
import { LinkedInContentForm } from "./forms/LinkedInContentForm";

export function ContentForm({ platform, values, onChange }) {
  const patch = (p) => onChange(platform, p);

  switch (platform) {
    case PLATFORMS.instagram:
      return <InstagramContentForm values={values} onChange={patch} />;
    case PLATFORMS.facebook:
      return <FacebookContentForm values={values} onChange={patch} />;
    case PLATFORMS.linkedin:
      return <LinkedInContentForm values={values} onChange={patch} />;
    default:
      return null;
  }
}

export default ContentForm;
