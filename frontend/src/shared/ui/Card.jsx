import React from "react";

export function Card({ children, className = "", hover = true, ...rest }) {
  return <div className={`rounded-[12px] border border-[#E5E7EB] bg-white p-6 transition-all duration-200 ${hover ? "hover:border-[#A78BFA] hover:-translate-y-[1px]" : ""} ${className}`} {...rest}>{children}</div>;
}

export default Card;
