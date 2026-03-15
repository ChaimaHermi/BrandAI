import React from "react";

export function Badge({ children, variant = "violet", className = "" }) {
  const variants = {
  violet: "bg-[#EDE9FE] text-[#7C3AED]",
  success: "bg-[#DCFCE7] text-[#16A34A]",
  waiting: "bg-[#FEF3C7] text-[#B45309]",
  danger: "bg-red-100 text-red-600",
};
  return <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${variants[variant]} ${className}`}>{children}</span>;
}

export default Badge;
