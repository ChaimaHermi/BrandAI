import React, { useEffect } from "react";
import { HiCheckCircle } from "react-icons/hi2";

export function Toast({
  message,
  visible,
  onClose,
  duration = 3000,
  icon: Icon = HiCheckCircle,
}) {
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
