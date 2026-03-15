import React from "react";

export function UserAvatar({ size = 32, user }) {
  if (!user) return null;
  const getInitials = (name) => {
    if (!name || !name.trim()) return "?";
    const parts = name.trim().split(/\s+/);
    return parts.length >= 2 ? (parts[0][0] + parts[parts.length - 1][0]).toUpperCase() : name.slice(0, 2).toUpperCase();
  };
  const avatarSrc = user.avatar_url || user.avatar;
  if (avatarSrc) return <img src={avatarSrc} alt={user.name || "Avatar"} className="rounded-full object-cover" style={{ width: size, height: size }} />;
  return <div className="flex items-center justify-center rounded-full bg-[#7C3AED] font-medium text-white" style={{ width: size, height: size, fontSize: size / 2.5 }}>{getInitials(user.name)}</div>;
}

export default UserAvatar;
