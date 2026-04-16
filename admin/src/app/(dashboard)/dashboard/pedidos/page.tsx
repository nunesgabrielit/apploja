"use client";

import Link from "next/link";
import { Filter, Loader2, Search, X } from "lucide-react";
import { useCallback, useEffect, useState } from "react";

import { Alert } from "@/components/ui/alert";
import { Pagination } from "@/components/ui/pagination";
import { listAdminOrders } from "@/services/order.service";
import type {
  AdminOrderListItem,
  FulfillmentType,
  OrderStatus,
  PaymentStatus
} from "@/types/order";
import { getApiErrorMessage } from "@/utils/api-error";
import { cn } from "@/utils/cn";

const PAGE_SIZE = 12;

const orderStatusOptions: OrderStatus[] = [
  "waiting_payment",
  "paid",
  "pending",
  "confirmed",
  "processing",
  "shipped",
  "delivered",
  "cancelled"
];

const paymentStatusOptions: PaymentStatus[] = [
  "pending",
  "approved",
  "rejected",
  "authorized",
  "paid",
  "failed",
  "refunded",
  "cancelled"
];

const fulfillmentOptions: FulfillmentType[] = ["pickup", "delivery"];

function statusBadgeClass(value: string): string {
  if (["paid", "approved", "delivered"].includes(value)) {
    return "bg-emerald-100 text-emerald-700";
  }
  if (["waiting_payment", "pending", "processing", "authorized", "shipped", "confirmed"].includes(value)) {
    return "bg-amber-100 text-amber-700";
  }
  if (["cancelled", "rejected", "failed"].includes(value)) {
    return "bg-rose-100 text-rose-700";
  }
  return "bg-slate-100 text-slate-700";
}

function readableLabel(value: string): string {
  return value.replaceAll("_", " ");
}

export default function PedidosPage() {
  const [orders, setOrders] = useState<AdminOrderListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [orderStatus, setOrderStatus] = useState<OrderStatus | "">("");
  const [paymentStatus, setPaymentStatus] = useState<PaymentStatus | "">("");
  const [fulfillmentType, setFulfillmentType] = useState<FulfillmentType | "">("");

  const fetchOrders = useCallback(async (): Promise<void> => {
    setLoading(true);
    setError(null);
    try {
      const response = await listAdminOrders({
        page,
        page_size: PAGE_SIZE,
        order_status: orderStatus || undefined,
        payment_status: paymentStatus || undefined,
        fulfillment_type: fulfillmentType || undefined
      });
      setOrders(response.data);
      setTotalPages(response.pagination.total_pages);
    } catch (requestError) {
      setError(getApiErrorMessage(requestError, "Não foi possível carregar os pedidos."));
    } finally {
      setLoading(false);
    }
  }, [fulfillmentType, orderStatus, page, paymentStatus]);

  useEffect(() => {
    void fetchOrders();
  }, [fetchOrders]);

  useEffect(() => {
    setPage(1);
  }, [orderStatus, paymentStatus, fulfillmentType]);

  return (
    <section className="space-y-6">
      <header>
        <h2 className="text-xl font-semibold text-slate-900">Pedidos</h2>
        <p className="mt-1 text-sm text-slate-500">
          Gestão administrativa de pedidos com filtros e paginação server-side.
        </p>
      </header>

      <div className="rounded-2xl border border-slate-100 bg-white p-6 shadow-sm">
        <div className="mb-4 flex items-center justify-between">
          <h3 className="text-sm font-semibold text-slate-800 flex items-center gap-2">
            <Filter size={16} className="text-blue-600" />
            Filtros de Pesquisa
          </h3>
        </div>
        <div className="grid gap-6 md:grid-cols-3">
          <div className="space-y-1.5">
            <label className="block text-xs font-semibold text-slate-500 uppercase tracking-wider">
              Status do pedido
            </label>
            <select
              value={orderStatus}
              onChange={(event) => setOrderStatus(event.target.value as OrderStatus | "")}
              className="w-full rounded-lg border border-slate-200 bg-slate-50 px-4 py-2.5 text-sm text-slate-700 outline-none transition focus:border-blue-500 focus:bg-white focus:ring-4 focus:ring-blue-500/10"
            >
              <option value="">Todos</option>
              {orderStatusOptions.map((option) => (
                <option key={option} value={option}>
                  {readableLabel(option)}
                </option>
              ))}
            </select>
          </div>
          <div className="space-y-1.5">
            <label className="block text-xs font-semibold text-slate-500 uppercase tracking-wider">
              Status do pagamento
            </label>
            <select
              value={paymentStatus}
              onChange={(event) => setPaymentStatus(event.target.value as PaymentStatus | "")}
              className="w-full rounded-lg border border-slate-200 bg-slate-50 px-4 py-2.5 text-sm text-slate-700 outline-none transition focus:border-blue-500 focus:bg-white focus:ring-4 focus:ring-blue-500/10"
            >
              <option value="">Todos</option>
              {paymentStatusOptions.map((option) => (
                <option key={option} value={option}>
                  {readableLabel(option)}
                </option>
              ))}
            </select>
          </div>
          <div className="space-y-1.5">
            <label className="block text-xs font-semibold text-slate-500 uppercase tracking-wider">
              Tipo de entrega
            </label>
            <select
              value={fulfillmentType}
              onChange={(event) => setFulfillmentType(event.target.value as FulfillmentType | "")}
              className="w-full rounded-lg border border-slate-200 bg-slate-50 px-4 py-2.5 text-sm text-slate-700 outline-none transition focus:border-blue-500 focus:bg-white focus:ring-4 focus:ring-blue-500/10"
            >
              <option value="">Todos</option>
              {fulfillmentOptions.map((option) => (
                <option key={option} value={option}>
                  {readableLabel(option)}
                </option>
              ))}
            </select>
          </div>
        </div>
        
        <div className="mt-6 flex items-center gap-3">
          <button 
            onClick={() => fetchOrders()}
            className="flex items-center gap-2 rounded-full bg-blue-600 px-6 py-2.5 text-sm font-semibold text-white shadow-sm transition hover:bg-blue-700 hover:shadow"
          >
            <Search size={16} />
            Pesquisar
          </button>
          <button 
            onClick={() => {
              setOrderStatus("");
              setPaymentStatus("");
              setFulfillmentType("");
            }}
            className="flex items-center gap-2 rounded-full border border-slate-200 bg-white px-6 py-2.5 text-sm font-semibold text-slate-600 transition hover:bg-slate-50 hover:text-slate-900"
          >
            <X size={16} />
            Limpar Filtros
          </button>
        </div>
      </div>

      {error ? <Alert message={error} /> : null}

      <div className="overflow-hidden rounded-2xl border border-slate-100 bg-white shadow-sm">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-slate-200">
            <thead className="bg-slate-50">
              <tr className="text-left text-xs uppercase tracking-wide text-slate-500">
                <th className="px-4 py-3">Pedido</th>
                <th className="px-4 py-3">Cliente</th>
                <th className="px-4 py-3">Total</th>
                <th className="px-4 py-3">Status</th>
                <th className="px-4 py-3">Pagamento</th>
                <th className="px-4 py-3">Data</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 text-sm text-slate-700">
              {loading ? (
                <tr>
                  <td colSpan={6} className="px-4 py-8 text-center text-slate-500">
                    <span className="inline-flex items-center gap-2">
                      <Loader2 className="animate-spin" size={16} />
                      Carregando pedidos...
                    </span>
                  </td>
                </tr>
              ) : orders.length === 0 ? (
                <tr>
                  <td colSpan={6} className="px-4 py-8 text-center text-slate-500">
                    Nenhum pedido encontrado para os filtros selecionados.
                  </td>
                </tr>
              ) : (
                orders.map((order) => (
                  <tr key={order.id}>
                    <td className="px-4 py-3 font-medium text-slate-900">
                      <Link
                        href={`/dashboard/pedidos/${order.id}`}
                        className="text-brand-700 hover:underline"
                      >
                        #{order.id.slice(0, 8)}
                      </Link>
                    </td>
                    <td className="px-4 py-3">{order.user_id.slice(0, 8)}</td>
                    <td className="px-4 py-3">R$ {Number(order.total).toFixed(2)}</td>
                    <td className="px-4 py-3">
                      <span className={cn("rounded-md px-2 py-1 text-xs font-medium", statusBadgeClass(order.order_status))}>
                        {readableLabel(order.order_status)}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <span className={cn("rounded-md px-2 py-1 text-xs font-medium", statusBadgeClass(order.payment_status))}>
                        {readableLabel(order.payment_status)}
                      </span>
                    </td>
                    <td className="px-4 py-3">{new Date(order.created_at).toLocaleString("pt-BR")}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
        <Pagination currentPage={page} totalPages={totalPages} onPageChange={setPage} />
      </div>
    </section>
  );
}
