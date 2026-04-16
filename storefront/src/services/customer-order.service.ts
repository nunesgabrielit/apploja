import { api } from "@/services/api";
import type { ApiResponse, PaginatedResponse } from "@/types/api";
import type { OrderCreateRequest, OrderListItem, OrderResponse } from "@/types/order";

export async function createCustomerOrder(
  payload: OrderCreateRequest
): Promise<ApiResponse<OrderResponse>> {
  const { data } = await api.post<ApiResponse<OrderResponse>>("/orders", payload);
  return data;
}

export async function listMyOrders(params?: {
  page?: number;
  page_size?: number;
}): Promise<PaginatedResponse<OrderListItem>> {
  const { data } = await api.get<PaginatedResponse<OrderListItem>>("/orders/me", { params });
  return data;
}

export async function getMyOrder(orderId: string): Promise<ApiResponse<OrderResponse>> {
  const { data } = await api.get<ApiResponse<OrderResponse>>(`/orders/me/${orderId}`);
  return data;
}
