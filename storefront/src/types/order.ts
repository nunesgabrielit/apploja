import type { ApiResponse, PaginatedResponse } from "@/types/api";

export type FulfillmentType = "delivery" | "pickup";
export type OrderStatus =
  | "waiting_payment"
  | "paid"
  | "pending"
  | "confirmed"
  | "processing"
  | "shipped"
  | "delivered"
  | "cancelled";
export type PaymentStatus =
  | "pending"
  | "approved"
  | "rejected"
  | "authorized"
  | "paid"
  | "failed"
  | "refunded"
  | "cancelled";

export interface OrderItemResponse {
  id: string;
  product_item_id: string;
  internal_code_snapshot: string;
  name_snapshot: string;
  unit_price: string;
  quantity: number;
  total_item: string;
  created_at: string;
}

export interface OrderResponse {
  id: string;
  user_id: string;
  address_id: string | null;
  fulfillment_type: FulfillmentType;
  order_status: OrderStatus;
  payment_status: PaymentStatus;
  subtotal: string;
  shipping_price: string;
  discount: string;
  total: string;
  notes: string | null;
  assigned_employee_id: string | null;
  items: OrderItemResponse[];
  created_at: string;
  updated_at: string;
}

export interface AdminOrderListItem {
  id: string;
  user_id: string;
  assigned_employee_id: string | null;
  fulfillment_type: FulfillmentType;
  order_status: OrderStatus;
  payment_status: PaymentStatus;
  subtotal: string;
  shipping_price: string;
  discount: string;
  total: string;
  total_items: number;
  created_at: string;
  updated_at: string;
}

export interface OrderListItem {
  id: string;
  fulfillment_type: FulfillmentType;
  order_status: OrderStatus;
  payment_status: PaymentStatus;
  subtotal: string;
  shipping_price: string;
  discount: string;
  total: string;
  total_items: number;
  created_at: string;
}

export interface OrderStatusHistory {
  id: string;
  order_id: string;
  previous_status: OrderStatus | null;
  new_status: OrderStatus;
  changed_by_user_id: string | null;
  created_at: string;
}

export interface EmployeePerformanceItem {
  employee_id: string;
  employee_name: string;
  employee_email: string;
  processed_orders: number;
  assigned_orders: number;
  completed_orders: number;
  total_sold: string;
}

export interface AdminOrderFilters {
  page?: number;
  page_size?: number;
  order_status?: OrderStatus;
  payment_status?: PaymentStatus;
  fulfillment_type?: FulfillmentType;
}

export interface AssignEmployeePayload {
  assigned_employee_id: string;
}

export interface UpdateOrderStatusPayload {
  order_status: OrderStatus;
}

export interface OrderCreateRequest {
  fulfillment_type: FulfillmentType;
  address_id?: string | null;
  notes?: string | null;
}

export type AdminOrdersResponse = PaginatedResponse<AdminOrderListItem>;
export type OrderDetailResponse = ApiResponse<OrderResponse>;
export type OrderHistoryResponse = ApiResponse<OrderStatusHistory[]>;
export type EmployeePerformanceResponse = ApiResponse<EmployeePerformanceItem[]>;
