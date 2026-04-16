import { api } from "@/admin/services/api";
import type {
  AdminOrderFilters,
  AdminOrdersResponse,
  AssignEmployeePayload,
  EmployeePerformanceResponse,
  OrderDetailResponse,
  OrderHistoryResponse,
  UpdateOrderStatusPayload
} from "@/admin/types/order";

export async function listAdminOrders(params?: AdminOrderFilters): Promise<AdminOrdersResponse> {
  const { data } = await api.get<AdminOrdersResponse>("/admin/orders", { params });
  return data;
}

export async function getAdminOrder(orderId: string): Promise<OrderDetailResponse> {
  const { data } = await api.get<OrderDetailResponse>(`/admin/orders/${orderId}`);
  return data;
}

export async function getOrderHistory(orderId: string): Promise<OrderHistoryResponse> {
  const { data } = await api.get<OrderHistoryResponse>(`/admin/orders/${orderId}/history`);
  return data;
}

export async function updateOrderStatus(
  orderId: string,
  payload: UpdateOrderStatusPayload
): Promise<OrderDetailResponse> {
  const { data } = await api.patch<OrderDetailResponse>(`/admin/orders/${orderId}/status`, payload);
  return data;
}

export async function assignOrderEmployee(
  orderId: string,
  payload: AssignEmployeePayload
): Promise<OrderDetailResponse> {
  const { data } = await api.patch<OrderDetailResponse>(
    `/admin/orders/${orderId}/assign-employee`,
    payload
  );
  return data;
}

export async function cancelOrder(
  orderId: string,
  returnToStock: boolean
): Promise<OrderDetailResponse> {
  const { data } = await api.post<OrderDetailResponse>(`/admin/orders/${orderId}/cancel`, null, {
    params: {
      return_to_stock: returnToStock
    }
  });
  return data;
}

export async function listEmployeesPerformance(): Promise<EmployeePerformanceResponse> {
  const { data } = await api.get<EmployeePerformanceResponse>("/admin/employees/performance");
  return data;
}
