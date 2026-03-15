// ==============================================================
//  frontend/src/components/ui/Toast.jsx
//  RÔLE : Notification de succès affichée en haut de page
//
//  UTILISATION :
//    <Toast message="Compte créé avec succès !" visible={showToast} onClose={() => setShowToast(false)} />
//
//  PROPS :
//    - message : texte à afficher
//    - visible : boolean, contrôle l'affichage
//    - onClose : callback appelé pour fermer (ou après timeout)
//    - duration : durée en ms avant auto-dismiss (défaut 3000)
//    - icon : composant React (icône de react-icons), optionnel
// ==============================================================

import React, { useEffect } from "react";
import { HiCheckCircle } from "react-icons/hi2";

export function Toast({ message, visible, onClose, duration = 3000, icon: Icon = HiCheckCircle }) {
  // Auto-dismiss après duration ms
  useEffect(() => {
    if (!visible || !onClose) return;
    const timer = setTimeout(onClose, duration);
    return () => clearTimeout(timer);
  }, [visible, onClose, duration]);

  if (!visible) return null;

  return (
    <div
      role="alert"
      className="fixed left-1/2 top-6 z-[100] flex -translate-x-1/2 items-center gap-3 rounded-[10px] border border-green-200 bg-green-50 px-6 py-4 text-sm font-medium text-green-800 shadow-lg"
    >
      <Icon className="h-6 w-6 flex-shrink-0 text-green-600" />
      <span>{message}</span>
    </div>
  );
}

export default Toast;
