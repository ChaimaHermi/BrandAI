export const MOCK_USER_GOOGLE = {
  name: "Ahmed Benali",
  email: "ahmed@gmail.com",
  avatar: "https://i.pravatar.cc/80?img=12",
  loginMethod: "google",
};

export const MOCK_USER_EMAIL = {
  name: "Ahmed Benali",
  email: "ahmed@gmail.com",
  avatar: null,
  loginMethod: "email",
};

export const PROJECTS = [
  { id: "ecoshop", name: "EcoShop", description: "Marketplace durable et local", emoji: "🌱", date: "2026-03-10", status: "completed", agentsDone: 6 },
  { id: "techmentor", name: "TechMentor", description: "Plateforme de mentorat IA pour étudiants tech", emoji: "💻", date: "2026-03-12", status: "running", agentsDone: 2, totalAgents: 6 },
  { id: "foodieapp", name: "FoodieApp", description: "Découverte de restaurants et recettes", emoji: "🍽️", date: "2026-03-11", status: "completed", agentsDone: 6 },
];

export const AGENTS = [
  { id: "idea", name: "Idea Enhancer", icon: "idea", order: 1 },
  { id: "market", name: "Market Analysis", icon: "market", order: 2 },
  { id: "brand", name: "Brand Identity", icon: "brand", order: 3 },
  { id: "content", name: "Content Creator", icon: "content", order: 4 },
  { id: "website", name: "Website Builder", icon: "website", order: 5 },
  { id: "optimizer", name: "Optimizer", icon: "optimizer", order: 6 },
];

export const TECHMENTOR_RESULTS = {
  idea: { status: "done", initial: "Plateforme de mentorat pour étudiants en tech", enhanced: "TechMentor est une plateforme IA qui connecte les étudiants en informatique avec des mentors virtuels personnalisés, offrant un accompagnement adaptatif 24/7 pour accélérer leur progression.", summary: "Idée enrichie et structurée avec proposition de valeur claire." },
  market: { status: "done", market_size: "$2.4B", competitors: 7, growth: "+23% CAGR", opportunity: "Fort potentiel dans le segment mentorat IA personnalisé pour développeurs juniors. Marché sous-servi avec forte demande.", top_competitors: ["Coursera", "Udemy", "Pluralsight"] },
  brand: { status: "running", typewriterLines: ["Analyse de l'idée...", "Génération du nom de marque...", "TechMentor — Apprends avec l'IA ▌"] },
  content: { status: "waiting" },
  website: { status: "waiting" },
  optimizer: { status: "waiting" },
};

export const SECTORS = [
  { value: "tech", label: "Tech / SaaS" },
  { value: "ecommerce", label: "E-commerce" },
  { value: "sante", label: "Santé" },
  { value: "education", label: "Éducation" },
  { value: "finance", label: "Finance" },
  { value: "autre", label: "Autre" },
];
