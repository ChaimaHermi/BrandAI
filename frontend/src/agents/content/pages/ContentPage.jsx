import { Navigate } from "react-router-dom";

/** Legacy route `/content/publish` redirects to the calendar + modal flow. */
export default function ContentPage() {
  return <Navigate to="../schedule" replace />;
}
