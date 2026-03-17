import { useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useAuth } from "@/shared/hooks/useAuth";

export default function IdeaPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { token } = useAuth();

  useEffect(() => {
    if (!id || !token) return;
    navigate(`/ideas/${id}/clarifier`, { replace: true });
  }, [id, token, navigate]);

  return null;
}
