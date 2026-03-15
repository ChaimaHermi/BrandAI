import React, { useState, useEffect, useMemo } from "react";
import { Link } from "react-router-dom";
import {
  HiOutlineClipboardDocumentList,
  HiOutlineArrowPath,
  HiOutlineCheckCircle,
  HiOutlinePlus,
} from "react-icons/hi2";
import { Navbar } from "../components/layout/Navbar";
import { Card } from "../components/ui/Card";
import { Button } from "../components/ui/Button";
import {
  IdeasTable,
  IdeasTableSkeleton,
  IdeasFilters,
  Pagination,
} from "../components/dashboard";
import { apiGetIdeas, getErrorMessage } from "../services/ideaApi";
import { useAuth } from "../hooks/useAuth";

const IDEAS_PER_PAGE = 5;

export function Dashboard() {
  const { token } = useAuth();
  const [ideas, setIdeas] = useState([]);
  const [totalFromApi, setTotalFromApi] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [currentPage, setCurrentPage] = useState(1);

  useEffect(() => {
    if (!token) return;
    let cancelled = false;
    (async () => {
      try {
        const data = await apiGetIdeas(token);
        if (!cancelled) {
          setIdeas(data.ideas || []);
          setTotalFromApi(data.total ?? (data.ideas || []).length);
          setError("");
        }
      } catch (err) {
        if (!cancelled) setError(getErrorMessage(err));
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => { cancelled = true; };
  }, [token]);

  const filteredIdeas = useMemo(() => {
    let list = [...ideas];
    const q = search.trim().toLowerCase();
    if (q) {
      list = list.filter(
        (i) =>
          (i.name || "").toLowerCase().includes(q) ||
          (i.sector || "").toLowerCase().includes(q)
      );
    }
    if (statusFilter) {
      list = list.filter((i) => i.status === statusFilter);
    }
    return list;
  }, [ideas, search, statusFilter]);

  const totalPages = Math.max(1, Math.ceil(filteredIdeas.length / IDEAS_PER_PAGE));
  const pageIdeas = useMemo(() => {
    const start = (currentPage - 1) * IDEAS_PER_PAGE;
    return filteredIdeas.slice(start, start + IDEAS_PER_PAGE);
  }, [filteredIdeas, currentPage]);

  useEffect(() => {
    if (currentPage > totalPages) setCurrentPage(1);
  }, [currentPage, totalPages]);

  const totalCount = totalFromApi || ideas.length;
  const runningCount = ideas.filter((i) => i.status === "running").length;
  const doneCount = ideas.filter((i) => i.status === "done").length;

  return (
    <div className="min-h-screen bg-white">
      <div className="flex min-h-screen flex-col">
        <Navbar variant="app" />
        <main className="mx-auto w-full max-w-[1200px] flex-1 px-4 py-8 md:px-6 md:py-10">
          <h1 className="mb-6 text-xl font-semibold text-[#111827]">Tableau de bord</h1>

          <div className="mb-8 grid gap-4 sm:grid-cols-3">
            <div className="rounded-[10px] border border-[#E5E7EB] border-l-[3px] border-l-[#7C3AED] bg-[#F9FAFB] p-4">
              <p className="flex items-center gap-2 text-sm text-[#6B7280]">
                <HiOutlineClipboardDocumentList className="h-4 w-4" aria-hidden />
                Total idées
              </p>
              <p className="mt-1 text-xl font-semibold text-[#111827]">{totalCount}</p>
            </div>
            <div className="rounded-[10px] border border-[#E5E7EB] border-l-[3px] border-l-[#7C3AED] bg-[#F9FAFB] p-4">
              <p className="flex items-center gap-2 text-sm text-[#6B7280]">
                <HiOutlineArrowPath className="h-4 w-4" aria-hidden />
                En cours
              </p>
              <p className="mt-1 text-xl font-semibold text-[#7C3AED]">{runningCount}</p>
            </div>
            <div className="rounded-[10px] border border-[#E5E7EB] border-l-[3px] border-l-[#16A34A] bg-[#F9FAFB] p-4">
              <p className="flex items-center gap-2 text-sm text-[#6B7280]">
                <HiOutlineCheckCircle className="h-4 w-4" aria-hidden />
                Terminées
              </p>
              <p className="mt-1 text-xl font-semibold text-[#16A34A]">{doneCount}</p>
            </div>
          </div>

          <section>
            <div className="mb-4 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
              <h2 className="text-lg font-semibold text-[#111827]">Mes idées</h2>
            </div>

            {error && (
              <div className="mb-4 rounded-[10px] border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-600">
                {error}
              </div>
            )}

            {loading ? (
              <IdeasTableSkeleton />
            ) : ideas.length === 0 ? (
              <Card
                hover={false}
                className="flex flex-col items-center justify-center border-2 border-dashed border-[#E5E7EB] bg-white py-16 text-center"
              >
                <div className="mb-4 h-20 w-20 rounded-lg border-2 border-dashed border-[#E5E7EB] bg-[#F9FAFB]" aria-hidden />
                <h3 className="mb-2 font-semibold text-[#111827]">Aucune idée pour le moment</h3>
                <p className="mb-6 max-w-sm text-sm text-[#6B7280]">
                  Commencez par soumettre votre première idée de projet
                </p>
                <Link to="/ideas/new">
                  <Button variant="primary" className="gap-2">
                    <HiOutlinePlus className="h-5 w-5" />
                    Soumettre une idée
                  </Button>
                </Link>
              </Card>
            ) : (
              <>
                <div className="mb-4">
                  <IdeasFilters
                    search={search}
                    onSearchChange={setSearch}
                    statusFilter={statusFilter}
                    onStatusFilterChange={(v) => {
                      setStatusFilter(v);
                      setCurrentPage(1);
                    }}
                  />
                </div>
                {filteredIdeas.length === 0 ? (
                  <Card hover={false} className="border border-[#E5E7EB] py-12 text-center">
                    <p className="text-[#6B7280]">Aucune idée ne correspond à votre recherche ou filtre.</p>
                  </Card>
                ) : (
                  <IdeasTable ideas={pageIdeas} />
                )}
                <div className="mt-4 flex flex-col items-center justify-between gap-3 sm:flex-row">
                  <p className="text-sm text-[#6B7280]">
                    {filteredIdeas.length === 0
                      ? "Aucun résultat"
                      : `${(currentPage - 1) * IDEAS_PER_PAGE + 1}-${Math.min(currentPage * IDEAS_PER_PAGE, filteredIdeas.length)} sur ${filteredIdeas.length}`}
                  </p>
                  <Pagination
                    currentPage={currentPage}
                    totalPages={totalPages}
                    onPageChange={setCurrentPage}
                  />
                </div>
              </>
            )}
          </section>
        </main>
      </div>
    </div>
  );
}

export default Dashboard;
