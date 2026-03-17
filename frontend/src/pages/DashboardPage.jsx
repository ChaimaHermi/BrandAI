import React, { useState, useEffect, useMemo } from "react";
import { Link } from "react-router-dom";
import {
  HiOutlineClipboardDocumentList,
  HiOutlineArrowPath,
  HiOutlineCheckCircle,
  HiOutlinePlus,
} from "react-icons/hi2";
import { Navbar } from "@/components/layout/Navbar";
import { Card } from "@/shared/ui/Card";
import { Button } from "@/shared/ui/Button";
import {
  IdeasTable,
  IdeasTableSkeleton,
  IdeasFilters,
  Pagination,
} from "@/components/dashboard";
import { apiGetIdeas, apiDeleteIdea, getErrorMessage } from "@/services/ideaApi";
import { useAuth } from "@/shared/hooks/useAuth";

const IDEAS_PER_PAGE = 5;

export default function DashboardPage() {
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
          (i.sector || "").toLowerCase().includes(q),
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

  const handleDeleteIdea = async (ideaId) => {
    if (!token) return;
    try {
      await apiDeleteIdea(ideaId, token);
      setIdeas((prev) => prev.filter((i) => i.id !== ideaId));
      setTotalFromApi((prev) => Math.max(0, prev - 1));
    } catch (err) {
      setError(getErrorMessage(err));
    }
  };

  const totalCount = totalFromApi || ideas.length;
  const runningCount = ideas.filter((i) => i.status === "running").length;
  const doneCount = ideas.filter((i) => i.status === "done").length;

  return (
    <div className="h-screen flex flex-col overflow-hidden bg-white">
      <Navbar variant="app" />
      <main className="flex flex-1 overflow-hidden">
        <div className="mx-auto w-full max-w-[1400px] px-6 py-4 flex flex-col h-full overflow-hidden">
          <h1 className="mb-4 text-xl font-semibold text-[#111827] shrink-0">
            Tableau de bord
          </h1>

          <div className="grid grid-cols-3 gap-4 shrink-0 mb-4">
            <div className="p-4 rounded-xl border border-[#E5E7EB] bg-white">
              <p className="flex items-center gap-2 text-sm text-[#6B7280]">
                <HiOutlineClipboardDocumentList className="h-4 w-4" aria-hidden />
                Total idées
              </p>
              <p className="mt-1 text-xl font-semibold text-[#111827]">{totalCount}</p>
            </div>
            <div className="p-4 rounded-xl border border-[#E5E7EB] bg-white">
              <p className="flex items-center gap-2 text-sm text-[#6B7280]">
                <HiOutlineArrowPath className="h-4 w-4" aria-hidden />
                En cours
              </p>
              <p className="mt-1 text-xl font-semibold text-[#7C3AED]">{runningCount}</p>
            </div>
            <div className="p-4 rounded-xl border border-[#E5E7EB] bg-white">
              <p className="flex items-center gap-2 text-sm text-[#6B7280]">
                <HiOutlineCheckCircle className="h-4 w-4" aria-hidden />
                Terminées
              </p>
              <p className="mt-1 text-xl font-semibold text-[#16A34A]">{doneCount}</p>
            </div>
          </div>

          <section className="flex flex-col flex-1 overflow-hidden min-h-0">
            <div className="mb-4 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between shrink-0">
              <h2 className="text-lg font-semibold text-[#111827]">Mes idées</h2>
            </div>

            {error && (
              <div className="mb-4 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-600 shrink-0">
                {error}
              </div>
            )}

            {loading ? (
              <div className="flex-1 overflow-y-auto min-h-0">
                <IdeasTableSkeleton />
              </div>
            ) : ideas.length === 0 ? (
              <div className="flex-1 overflow-y-auto min-h-0">
                <Card
                  hover={false}
                  className="flex flex-col items-center justify-center border-2 border-dashed border-[#E5E7EB] bg-white rounded-xl py-16 text-center"
                >
                  <div
                    className="mb-4 h-20 w-20 rounded-lg border-2 border-dashed border-[#E5E7EB] bg-[#F9FAFB]"
                    aria-hidden
                  />
                  <h3 className="mb-2 font-semibold text-[#111827]">
                    Aucune idée pour le moment
                  </h3>
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
              </div>
            ) : (
              <div className="flex flex-col flex-1 overflow-hidden min-h-0">
                <div className="mb-4 shrink-0">
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
                <div className="flex-1 overflow-y-auto min-h-0">
                  {filteredIdeas.length === 0 ? (
                    <Card
                      hover={false}
                      className="border border-[#E5E7EB] rounded-xl py-12 text-center"
                    >
                      <p className="text-[#6B7280]">
                        Aucune idée ne correspond à votre recherche ou filtre.
                      </p>
                    </Card>
                  ) : (
                    <IdeasTable ideas={pageIdeas} onDelete={handleDeleteIdea} />
                  )}
                </div>
                <div className="mt-4 flex flex-col items-center justify-between gap-3 sm:flex-row shrink-0">
                  <p className="text-sm text-[#6B7280]">
                    {filteredIdeas.length === 0
                      ? "Aucun résultat"
                      : `${(currentPage - 1) * IDEAS_PER_PAGE + 1}-${Math.min(
                          currentPage * IDEAS_PER_PAGE,
                          filteredIdeas.length,
                        )} sur ${filteredIdeas.length}`}
                  </p>
                  <Pagination
                    currentPage={currentPage}
                    totalPages={totalPages}
                    onPageChange={setCurrentPage}
                  />
                </div>
              </div>
            )}
          </section>
        </div>
      </main>
    </div>
  );
}

