"use client";

import { Filter, Loader2, Search, X } from "lucide-react";
import { type FormEvent, useCallback, useEffect, useState } from "react";

import { Alert } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Pagination } from "@/components/ui/pagination";
import {
  listProductItems,
  listStockMovementsByItem,
  updateProductItemStock
} from "@/admin/services/catalog.service";
import type {
  ProductItemListItem,
  ProductItemStockUpdatePayload,
  StockMovementItem,
  StockOperation
} from "@/admin/types/catalog";
import { getApiErrorMessage } from "@/utils/api-error";

const PAGE_SIZE = 10;

export default function EstoquePage() {
  const [items, setItems] = useState<ProductItemListItem[]>([]);
  const [loadingItems, setLoadingItems] = useState(true);
  const [updatingItemId, setUpdatingItemId] = useState<string | null>(null);
  const [selectedItemId, setSelectedItemId] = useState<string | null>(null);
  const [movements, setMovements] = useState<StockMovementItem[]>([]);
  const [loadingMovements, setLoadingMovements] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);

  const [search, setSearch] = useState("");
  const [sku, setSku] = useState("");
  const [lowStockOnly, setLowStockOnly] = useState(false);

  const [operation, setOperation] = useState<StockOperation>("set");
  const [quantity, setQuantity] = useState(0);
  const [reason, setReason] = useState("");

  const fetchItems = useCallback(async (): Promise<void> => {
    setLoadingItems(true);
    setError(null);
    try {
      const response = await listProductItems({
        page,
        page_size: PAGE_SIZE,
        search: search || undefined,
        sku: sku || undefined,
        low_stock: lowStockOnly ? true : undefined
      });
      setItems(response.data);
      setTotalPages(response.pagination.total_pages);
    } catch (requestError) {
      setError(getApiErrorMessage(requestError, "Não foi possível carregar itens de estoque."));
    } finally {
      setLoadingItems(false);
    }
  }, [lowStockOnly, page, search, sku]);

  useEffect(() => {
    void fetchItems();
  }, [fetchItems]);

  useEffect(() => {
    setPage(1);
  }, [search, sku, lowStockOnly]);

  const fetchMovements = async (itemId: string): Promise<void> => {
    setSelectedItemId(itemId);
    setLoadingMovements(true);
    setError(null);
    try {
      const response = await listStockMovementsByItem(itemId, { page: 1, page_size: 20 });
      setMovements(response.data);
    } catch (requestError) {
      setError(getApiErrorMessage(requestError, "Não foi possível carregar movimentações."));
    } finally {
      setLoadingMovements(false);
    }
  };

  const handleStockUpdate = async (
    event: FormEvent<HTMLFormElement>,
    itemId: string
  ): Promise<void> => {
    event.preventDefault();
    if (!itemId) {
      return;
    }
    setUpdatingItemId(itemId);
    setError(null);
    setSuccessMessage(null);
    try {
      const payload: ProductItemStockUpdatePayload = {
        operation,
        quantity,
        reason: reason.trim() || null
      };
      await updateProductItemStock(itemId, payload);
      setSuccessMessage("Estoque atualizado com sucesso.");
      await fetchItems();
      await fetchMovements(itemId);
    } catch (requestError) {
      setError(getApiErrorMessage(requestError, "Não foi possível atualizar estoque."));
    } finally {
      setUpdatingItemId(null);
    }
  };

  return (
    <section className="space-y-6">
      <header>
        <h2 className="text-xl font-semibold text-slate-900">Estoque</h2>
        <p className="mt-1 text-sm text-slate-500">
          Consulta de itens e ajuste manual com rastreabilidade de movimentação.
        </p>
      </header>

      <div className="rounded-2xl border border-slate-100 bg-white p-6 shadow-sm">
        <div className="mb-4 flex items-center justify-between">
          <h3 className="text-sm font-semibold text-slate-800 flex items-center gap-2">
            <Filter size={16} className="text-blue-600" />
            Filtros de Pesquisa
          </h3>
        </div>
        <div className="grid gap-6 md:grid-cols-3 items-end">
          <Input
            label="Buscar item"
            placeholder="Nome do item"
            value={search}
            onChange={(event) => setSearch(event.target.value)}
          />
          <Input
            label="Filtrar por SKU"
            placeholder="WM-CA007"
            value={sku}
            onChange={(event) => setSku(event.target.value)}
          />
          <label className="flex items-center gap-2 pb-2 text-sm text-slate-700">
            <input
              type="checkbox"
              checked={lowStockOnly}
              onChange={(event) => setLowStockOnly(event.target.checked)}
              className="h-4 w-4 rounded border-slate-300"
            />
            Apenas baixo estoque
          </label>
        </div>
        <div className="mt-6 flex items-center gap-3">
          <button 
            onClick={() => fetchItems()}
            className="flex items-center gap-2 rounded-full bg-blue-600 px-6 py-2.5 text-sm font-semibold text-white shadow-sm transition hover:bg-blue-700 hover:shadow"
          >
            <Search size={16} />
            Pesquisar
          </button>
          <button 
            onClick={() => {
              setSearch("");
              setSku("");
              setLowStockOnly(false);
            }}
            className="flex items-center gap-2 rounded-full border border-slate-200 bg-white px-6 py-2.5 text-sm font-semibold text-slate-600 transition hover:bg-slate-50 hover:text-slate-900"
          >
            <X size={16} />
            Limpar Filtros
          </button>
        </div>
      </div>

      <div className="overflow-hidden rounded-2xl border border-slate-100 bg-white shadow-sm">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-slate-200">
            <thead className="bg-slate-50">
              <tr className="text-left text-xs uppercase tracking-wide text-slate-500">
                <th className="px-4 py-3">Item</th>
                <th className="px-4 py-3">SKU</th>
                <th className="px-4 py-3">Estoque</th>
                <th className="px-4 py-3">Mínimo</th>
                <th className="px-4 py-3">Ações</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 text-sm text-slate-700">
              {loadingItems ? (
                <tr>
                  <td colSpan={5} className="px-4 py-8 text-center text-slate-500">
                    <span className="inline-flex items-center gap-2">
                      <Loader2 className="animate-spin" size={16} />
                      Carregando estoque...
                    </span>
                  </td>
                </tr>
              ) : items.length === 0 ? (
                <tr>
                  <td colSpan={5} className="px-4 py-8 text-center text-slate-500">
                    Nenhum item encontrado.
                  </td>
                </tr>
              ) : (
                items.map((item) => (
                  <tr key={item.id}>
                    <td className="px-4 py-3">
                      <p className="font-medium text-slate-900">{item.name}</p>
                      <p className="text-xs text-slate-500">{item.product_name_base}</p>
                    </td>
                    <td className="px-4 py-3">{item.sku}</td>
                    <td className="px-4 py-3">
                      <span
                        className={
                          item.low_stock
                            ? "rounded-md bg-amber-100 px-2 py-1 text-amber-700"
                            : "rounded-md bg-emerald-100 px-2 py-1 text-emerald-700"
                        }
                      >
                        {item.stock_current}
                      </span>
                    </td>
                    <td className="px-4 py-3">{item.stock_minimum}</td>
                    <td className="px-4 py-3">
                      <Button variant="ghost" onClick={() => void fetchMovements(item.id)}>
                        <span className="mr-2">
                          <Search size={14} />
                        </span>
                        Ver movimentações
                      </Button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
        <Pagination currentPage={page} totalPages={totalPages} onPageChange={setPage} />
      </div>

      <div className="rounded-xl border border-slate-200 bg-white p-5">
        <h3 className="text-base font-semibold text-slate-900">Ajuste manual de estoque</h3>
        <p className="mt-1 text-sm text-slate-500">Selecione um item na lista e aplique a operação.</p>
        <form
          className="mt-4 grid gap-4 md:grid-cols-4"
          onSubmit={(event) => void handleStockUpdate(event, selectedItemId || "")}
        >
          <div className="space-y-1.5">
            <label className="block text-sm font-medium text-slate-700">Item</label>
            <select
              value={selectedItemId || ""}
              onChange={(event) => setSelectedItemId(event.target.value)}
              className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 outline-none transition focus:border-brand-500 focus:ring-2 focus:ring-brand-200"
              required
            >
              <option value="">Selecione</option>
              {items.map((item) => (
                <option key={item.id} value={item.id}>
                  {item.name} ({item.sku})
                </option>
              ))}
            </select>
          </div>
          <div className="space-y-1.5">
            <label className="block text-sm font-medium text-slate-700">Operação</label>
            <select
              value={operation}
              onChange={(event) => setOperation(event.target.value as StockOperation)}
              className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 outline-none transition focus:border-brand-500 focus:ring-2 focus:ring-brand-200"
            >
              <option value="set">Definir</option>
              <option value="increment">Incrementar</option>
              <option value="decrement">Decrementar</option>
            </select>
          </div>
          <Input
            label="Quantidade"
            type="number"
            min={0}
            value={quantity}
            onChange={(event) => setQuantity(Number(event.target.value))}
            required
          />
          <Input
            label="Motivo"
            placeholder="Ex: contagem cíclica"
            value={reason}
            onChange={(event) => setReason(event.target.value)}
          />
          <div className="md:col-span-4">
            {error ? <Alert message={error} /> : null}
            {successMessage ? (
              <div className="rounded-lg border border-emerald-200 bg-emerald-50 px-3 py-2 text-sm text-emerald-700">
                {successMessage}
              </div>
            ) : null}
          </div>
          <div className="md:col-span-4">
            <Button type="submit" disabled={!selectedItemId || updatingItemId === selectedItemId}>
              {updatingItemId === selectedItemId ? "Atualizando..." : "Aplicar ajuste"}
            </Button>
          </div>
        </form>
      </div>

      <div className="rounded-xl border border-slate-200 bg-white p-5">
        <h3 className="text-base font-semibold text-slate-900">Histórico de movimentações</h3>
        <p className="mt-1 text-sm text-slate-500">Últimas 20 movimentações do item selecionado.</p>
        <div className="mt-4 overflow-x-auto">
          <table className="min-w-full divide-y divide-slate-200">
            <thead className="bg-slate-50">
              <tr className="text-left text-xs uppercase tracking-wide text-slate-500">
                <th className="px-3 py-2">Tipo</th>
                <th className="px-3 py-2">Origem</th>
                <th className="px-3 py-2">Qtd</th>
                <th className="px-3 py-2">Referência</th>
                <th className="px-3 py-2">Data</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 text-sm text-slate-700">
              {loadingMovements ? (
                <tr>
                  <td colSpan={5} className="px-3 py-6 text-center text-slate-500">
                    Carregando movimentações...
                  </td>
                </tr>
              ) : movements.length === 0 ? (
                <tr>
                  <td colSpan={5} className="px-3 py-6 text-center text-slate-500">
                    Selecione um item para visualizar o histórico.
                  </td>
                </tr>
              ) : (
                movements.map((movement) => (
                  <tr key={movement.id}>
                    <td className="px-3 py-2">{movement.movement_type}</td>
                    <td className="px-3 py-2">{movement.source}</td>
                    <td className="px-3 py-2">{movement.quantity}</td>
                    <td className="px-3 py-2">{movement.reference_id ?? "-"}</td>
                    <td className="px-3 py-2">
                      {new Date(movement.created_at).toLocaleString("pt-BR")}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </section>
  );
}
