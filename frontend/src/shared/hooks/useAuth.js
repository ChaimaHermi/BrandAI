import { useAuthContext } from "@/context/AuthContext";

// Canonical location for the useAuth hook.
export function useAuth() {
  return useAuthContext();
}

export default useAuth;
