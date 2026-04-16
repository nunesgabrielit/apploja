"use client";

import Link from "next/link";
import { ArrowLeft, Loader2 } from "lucide-react";
import { useParams } from "next/navigation";
import { type FormEvent, useCallback, useEffect, useMemo, useState } from "react";

import { Alert } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  assignOrderEmployee,
  cancelOrder,
  getAdminOrder,
  getOrderHistory,
  listEmployeesPerformance,
  updateOrderStatus
} from "@/admin/services/order.service";
import type {
  EmployeePerformanceItem,
  OrderResponse,
  OrderStatus,
  OrderStatusHistory
} from "@/admin/types/order";
import { getApiErrorMessage } from "@/utils/api-error";
import { cn } from "@/utils/cn";

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

export default function PedidoDetalhePage() {
  const params = useParams<{ id: string }>();
  const orderId = params.id;

  const [order, setOrder] = useState<OrderResponse | null>(null);
  const [history, setHistory] = useState<OrderStatusHistory[]>([]);
  const [employees, setEmployees] = useState<EmployeePerformanceItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const [statusDraft, setStatusDraft] = useState<OrderStatus>("pending");
  const [employeeIdDraft, setEmployeeIdDraft] = useState("");
  const [returnToStock, setReturnToStock] = useState(true);

  const [updatingStatus, setUpdatingStatus] = useState(false);
  const [assigningEmployee, setAssigningEmployee] = useState(false);
  const [cancellingOrder, setCancellingOrder] = useState(false);

  const totalItems = useMemo(
    () => order?.items.reduce((total, item) => total + item.quantity, 0) ?? 0,
    [order]
  );

  const fetchOrderContext = useCallback(async (): Promise<void> => {
    if (!orderId) {
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const [orderResponse, historyResponse, employeesResponse] = await Promise.all([
        getAdminOrder(orderId),
        getOrderHistory(orderId),
        listEmployeesPerformance()
      ]);
      setOrder(orderResponse.data);
      setHistory(historyResponse.data);
      setEmployees(employeesResponse.data);
      setStatusDraft(orderResponse.data.order_status);
      setEmployeeIdDraft(orderResponse.data.assigned_employee_id ?? "");
    } catch (requestError) {
      setError(getApiErrorMessage(requestError, "Não foi possível carregar o pedido."));
    } finally {
      setLoading(false);
    }
  }, [orderId]);

  useEffect(() => {
    void fetchOrderContext();
  }, [fetchOrderContext]);

  const handleUpdateStatus = async (event: FormEvent<HTMLFormElement>): Promise<void> => {
    event.preventDefault();
    if (!order) {
      return;
    }
    setUpdatingStatus(true);
    setError(null);
    setSuccessMessage(null);
    try {
      await updateOrderStatus(order.id, { order_status: statusDraft });
      setSuccessMessage("Status do pedido atualizado com sucesso.");
      await fetchOrderContext();
    } catch (requestError) {
      setError(getApiErrorMessage(requestError, "Não foi possível atualizar o status do pedido."));
    } finally {
      setUpdatingStatus(false);
    }
  };

  const handleAssignEmployee = async (event: FormEvent<HTMLFormElement>): Promise<void> => {
    event.preventDefault();
    if (!order || !employeeIdDraft) {
      return;
    }
    setAssigningEmployee(true);
    setError(null);
    setSuccessMessage(null);
    try {
      await assignOrderEmployee(order.id, { assigned_employee_id: employeeIdDraft });
      setSuccessMessage("Funcionário atribuído com sucesso.");
      await fetchOrderContext();
    } catch (requestError) {
      setError(getApiErrorMessage(requestError, "Não foi possível atribuir funcionário ao pedido."));
    } finally {
      setAssigningEmployee(false);
    }
  };

  const handleCancelOrder = async (): Promise<void> => {
    if (!order) {
      return;
    }
    const confirmed = window.confirm(
      "Tem certeza que deseja cancelar este pedido? Essa operação pode impactar estoque."
    );
    if (!confirmed) {
      return;
    }
    setCancellingOrder(true);
    setError(null);
    setSuccessMessage(null);
    try {
      await cancelOrder(order.id, returnToStock);
      setSuccessMessage("Pedido cancelado com sucesso.");
      await fetchOrderContext();
    } catch (requestError) {
      setError(getApiErrorMessage(requestError, "Não foi possível cancelar o pedido."));
    } finally {
      setCancellingOrder(false);
    }
  };

  if (loading) {
    return (
      <div className="flex min-h-[50vh] items-center justify-center text-slate-500">
        <span className="inline-flex items-center gap-2">
          <Loader2 className="animate-spin" size={16} />
          Carregando detalhes do pedido...
        </span>
      </div>
    );
  }

  if (!order) {
    return (
      <section className="space-y-4">
        <Alert message={error ?? "Pedido não encontrado."} />
        <Link href="/dashboard/pedidos" className="inline-flex items-center text-sm text-brand-700 hover:underline">
          <ArrowLeft size={14} className="mr-2" />
          Voltar para pedidos
        </Link>
      </section>
    );
  }

  return (
    <section className="space-y-6">
      <header className="flex items-center justify-between">
        <div>
          <Link href="/dashboard/pedidos" className="inline-flex items-center text-sm text-brand-700 hover:underline">
            <ArrowLeft size={14} className="mr-2" />
            Voltar para pedidos
          </Link>
          <h2 className="mt-2 text-xl font-semibold text-slate-900">Pedido #{order.id.slice(0, 8)}</h2>
          <p className="mt-1 text-sm text-slate-500">
            Criado em {new Date(order.created_at).toLocaleString("pt-BR")}
          </p>
        </div>
      </header>

      {error ? <Alert message={error} /> : null}
      {successMessage ? (
        <div className="rounded-lg border border-emerald-200 bg-emerald-50 px-3 py-2 text-sm text-emerald-700">
          {successMessage}
        </div>
      ) : null}

      <div className="grid gap-4 md:grid-cols-3">
        <article className="rounded-xl border border-slate-200 bg-white p-4">
          <p className="text-xs uppercase tracking-wide text-slate-500">Status do pedido</p>
          <p className={cn("mt-2 inline-flex rounded-md px-2 py-1 text-xs font-medium", statusBadgeClass(order.order_status))}>
            {readableLabel(order.order_status)}
          </p>
          <p className="mt-3 text-xs uppercase tracking-wide text-slate-500">Pagamento</p>
          <p className={cn("mt-2 inline-flex rounded-md px-2 py-1 text-xs font-medium", statusBadgeClass(order.payment_status))}>
            {readableLabel(order.payment_status)}
          </p>
        </article>
        <article className="rounded-xl border border-slate-200 bg-white p-4">
          <p className="text-xs uppercase tracking-wide text-slate-500">Cliente</p>
          <p className="mt-2 text-sm font-medium text-slate-900">{order.user_id}</p>
          <p className="mt-3 text-xs uppercase tracking-wide text-slate-500">Tipo de atendimento</p>
          <p className="mt-2 text-sm text-slate-800">{readableLabel(order.fulfillment_type)}</p>
          {order.fulfillment_type === "delivery" ? (
            <>
              <p className="mt-3 text-xs uppercase tracking-wide text-slate-500">Endereço</p>
              <p className="mt-2 text-sm text-slate-800">{order.address_id ?? "Não informado"}</p>
            </>
          ) : null}
        </article>
        <article className="rounded-xl border border-slate-200 bg-white p-4">
          <p className="text-xs uppercase tracking-wide text-slate-500">Resumo financeiro</p>
          <p className="mt-2 text-sm text-slate-800">Subtotal: R$ {Number(order.subtotal).toFixed(2)}</p>
          <p className="mt-1 text-sm text-slate-800">Frete: R$ {Number(order.shipping_price).toFixed(2)}</p>
          <p className="mt-1 text-sm text-slate-800">Desconto: R$ {Number(order.discount).toFixed(2)}</p>
          <p className="mt-3 text-base font-semibold text-slate-900">Total: R$ {Number(order.total).toFixed(2)}</p>
          <p className="mt-1 text-xs text-slate-500">{totalItems} itens</p>
        </article>
      </div>

      <div className="grid gap-4 lg:grid-cols-3">
        <form
          className="space-y-3 rounded-xl border border-slate-200 bg-white p-4"
          onSubmit={(event) => void handleUpdateStatus(event)}
        >
          <h3 className="text-sm font-semibold text-slate-900">Alterar status</h3>
          <div className="space-y-1.5">
            <label className="block text-sm font-medium text-slate-700">Novo status</label>
            <select
              value={statusDraft}
              onChange={(event) => setStatusDraft(event.target.value as OrderStatus)}
              className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 outline-none transition focus:border-brand-500 focus:ring-2 focus:ring-brand-200"
            >
              {orderStatusOptions.map((option) => (
                <option key={option} value={option}>
                  {readableLabel(option)}
                </option>
              ))}
            </select>
          </div>
          <Button type="submit" disabled={updatingStatus}>
            {updatingStatus ? "Atualizando..." : "Atualizar status"}
          </Button>
        </form>

        <form
          className="space-y-3 rounded-xl border border-slate-200 bg-white p-4"
          onSubmit={(event) => void handleAssignEmployee(event)}
        >
          <h3 className="text-sm font-semibold text-slate-900">Atribuir funcionário</h3>
          <div className="space-y-1.5">
            <label className="block text-sm font-medium text-slate-700">Funcionário</label>
            <select
              value={employeeIdDraft}
              onChange={(event) => setEmployeeIdDraft(event.target.value)}
              className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 outline-none transition focus:border-brand-500 focus:ring-2 focus:ring-brand-200"
              required
            >
              <option value="">Selecione</option>
              {employees.map((employee) => (
                <option key={employee.employee_id} value={employee.employee_id}>
                  {employee.employee_name} ({employee.employee_email})
                </option>
              ))}
            </select>
          </div>
          <Button type="submit" disabled={assigningEmployee}>
            {assigningEmployee ? "Atribuindo..." : "Salvar atribuição"}
          </Button>
        </form>

        <div className="space-y-3 rounded-xl border border-rose-200 bg-rose-50 p-4">
          <h3 className="text-sm font-semibold text-rose-700">Cancelar pedido</h3>
          <Input
            label="Retornar estoque automaticamente"
            type="text"
            value={returnToStock ? "Sim" : "Não"}
            readOnly
            onClick={() => setReturnToStock((current) => !current)}
          />
          <label className="flex items-center gap-2 text-sm text-rose-700">
            <input
              type="checkbox"
              checked={returnToStock}
              onChange={(event) => setReturnToStock(event.target.checked)}
            />
            Retornar itens ao estoque
          </label>
          <Button type="button" variant="secondary" onClick={() => void handleCancelOrder()} disabled={cancellingOrder}>
            {cancellingOrder ? "Cancelando..." : "Cancelar pedido"}
          </Button>
        </div>
      </div>

      <div className="rounded-xl border border-slate-200 bg-white p-4">
        <h3 className="text-base font-semibold text-slate-900">Itens comprados</h3>
        <p className="mt-1 text-sm text-slate-500">Snapshot de preço e código no momento da compra.</p>
        <div className="mt-3 overflow-x-auto">
          <table className="min-w-full divide-y divide-slate-200">
            <thead className="bg-slate-50">
              <tr className="text-left text-xs uppercase tracking-wide text-slate-500">
                <th className="px-3 py-2">Código</th>
                <th className="px-3 py-2">Nome</th>
                <th className="px-3 py-2">Qtd</th>
                <th className="px-3 py-2">Unitário</th>
                <th className="px-3 py-2">Total</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 text-sm text-slate-700">
              {order.items.map((item) => (
                <tr key={item.id}>
                  <td className="px-3 py-2">{item.internal_code_snapshot}</td>
                  <td className="px-3 py-2">{item.name_snapshot}</td>
                  <td className="px-3 py-2">{item.quantity}</td>
                  <td className="px-3 py-2">R$ {Number(item.unit_price).toFixed(2)}</td>
                  <td className="px-3 py-2">R$ {Number(item.total_item).toFixed(2)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <div className="rounded-xl border border-slate-200 bg-white p-4">
        <h3 className="text-base font-semibold text-slate-900">Histórico do pedido</h3>
        <p className="mt-1 text-sm text-slate-500">Mudanças de status registradas na auditoria operacional.</p>
        <div className="mt-3 overflow-x-auto">
          <table className="min-w-full divide-y divide-slate-200">
            <thead className="bg-slate-50">
              <tr className="text-left text-xs uppercase tracking-wide text-slate-500">
                <th className="px-3 py-2">Status anterior</th>
                <th className="px-3 py-2">Novo status</th>
                <th className="px-3 py-2">Responsável</th>
                <th className="px-3 py-2">Data</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 text-sm text-slate-700">
              {history.length === 0 ? (
                <tr>
                  <td colSpan={4} className="px-3 py-6 text-center text-slate-500">
                    Sem histórico registrado até o momento.
                  </td>
                </tr>
              ) : (
                history.map((item) => (
                  <tr key={item.id}>
                    <td className="px-3 py-2">{item.previous_status ? readableLabel(item.previous_status) : "-"}</td>
                    <td className="px-3 py-2">{readableLabel(item.new_status)}</td>
                    <td className="px-3 py-2">{item.changed_by_user_id ?? "-"}</td>
                    <td className="px-3 py-2">{new Date(item.created_at).toLocaleString("pt-BR")}</td>
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
