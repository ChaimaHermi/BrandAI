import React from "react";

export function Button({
  children,
  variant = "primary",
  type = "button",
  className = "",
  disabled = false,
  fullWidth = false,
  onClick,
  ...rest
}) {
  const base =
    "inline-flex items-center justify-center gap-2 rounded-[10px] font-medium transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed ";
  const variants = {
    primary:
      "bg-[#7C3AED] text-white hover:bg-[#6D28D9] hover:scale-[1.02] active:scale-[0.98] px-5 py-2.5",
    outline:
      "border border-[#E5E7EB] bg-white text-[#111827] hover:border-violet-300 hover:text-[#7C3AED]",
    ghost: "text-[#6B7280] hover:text-[#7C3AED] hover:bg-[#F5F3FF]",
  };
  return (
    <button
      type={type}
      disabled={disabled}
      onClick={onClick}
      className={`${base} ${variants[variant]} ${fullWidth ? "w-full" : ""} ${className}`}
      {...rest}
    >
      {children}
    </button>
  );
}

export default Button;
