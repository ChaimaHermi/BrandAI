import React from "react";
import { Link } from "react-router-dom";
import { HiOutlineFolder, HiOutlinePlus } from "react-icons/hi2";
import { Navbar } from "../components/layout/Navbar";
import { Card } from "../components/ui/Card";
import { Badge } from "../components/ui/Badge";
import { Button } from "../components/ui/Button";
import { PROJECTS } from "../data/mockData";

const totalProjects = PROJECTS.length;
const runningCount = PROJECTS.filter((p) => p.status === "running").length;
const completedCount = PROJECTS.filter((p) => p.status === "completed").length;

export function Dashboard() {
  return (
    <div className="min-h-screen bg-white">
      <div className="flex min-h-screen flex-col">
        <Navbar variant="app" />
        <main className="mx-auto w-full max-w-[1200px] flex-1 px-4 py-8 md:px-6 md:py-12">
          <h1 className="mb-8 text-2xl font-semibold text-[#111827]">Tableau de bord</h1>
          <div className="mb-10 grid gap-6 sm:grid-cols-3">
            <div className="rounded-[12px] border border-[#E5E7EB] border-l-[3px] border-l-[#7C3AED] bg-[#F9FAFB] p-6">
              <p className="text-sm text-[#6B7280]">Total projets</p>
              <p className="mt-1 text-2xl font-semibold text-[#111827]">{totalProjects}</p>
            </div>
            <div className="rounded-[12px] border border-[#E5E7EB] border-l-[3px] border-l-[#7C3AED] bg-[#F9FAFB] p-6">
              <p className="text-sm text-[#6B7280]">En cours</p>
              <p className="mt-1 text-2xl font-semibold text-[#7C3AED]">{runningCount}</p>
            </div>
            <div className="rounded-[12px] border border-[#E5E7EB] border-l-[3px] border-l-[#16A34A] bg-[#F9FAFB] p-6">
              <p className="text-sm text-[#6B7280]">Complétés</p>
              <p className="mt-1 text-2xl font-semibold text-[#16A34A]">{completedCount}</p>
            </div>
          </div>
          <section>
            <h2 className="mb-4 text-lg font-semibold text-[#111827]">Mes projets</h2>
            {PROJECTS.length > 0 ? (
              <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
                {PROJECTS.map((project) => (
                  <Link key={project.id} to={`/projects/${project.id}`}>
                    <Card
                      hover={false}
                      className={`h-full border border-[#E5E7EB] bg-white transition-all duration-200 hover:border-[#A78BFA] hover:-translate-y-[1px] ${project.status === "running" ? "border-2 border-[#7C3AED]" : ""}`}
                    >
                      <div className="flex items-start gap-4">
                        <span className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-[#7C3AED]/10 text-2xl">{project.emoji}</span>
                        <div className="min-w-0 flex-1">
                          <h3 className="truncate font-semibold text-[#111827]">{project.name}</h3>
                          <p className="mt-0.5 line-clamp-2 text-sm text-[#6B7280]">{project.description}</p>
                          <div className="mt-3 flex items-center justify-between gap-2">
                            <span className="text-xs text-[#6B7280]">{new Date(project.date).toLocaleDateString("fr-FR")}</span>
                            <Badge variant={project.status === "completed" ? "success" : project.status === "running" ? "violet" : "waiting"}>{project.status === "completed" ? "Complété" : project.status === "running" ? "En cours" : "En attente"}</Badge>
                          </div>
                        </div>
                      </div>
                    </Card>
                  </Link>
                ))}
              </div>
            ) : (
              <Card className="flex flex-col items-center justify-center py-16 text-center" hover={false}>
                <HiOutlineFolder className="mb-4 h-16 w-16 text-[#6B7280]" />
                <h3 className="mb-2 font-semibold text-[#111827]">Aucun projet</h3>
                <p className="mb-6 max-w-sm text-[#6B7280]">Créez votre premier projet pour générer votre marque avec l'IA.</p>
                <Link to="/projects/new"><Button variant="primary" className="gap-2"><HiOutlinePlus className="h-5 w-5" /> Nouveau projet</Button></Link>
              </Card>
            )}
          </section>
        </main>
      </div>
    </div>
  );
}

export default Dashboard;
