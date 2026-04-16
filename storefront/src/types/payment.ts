import type { ApiResponse } from "@/types/api";

export type PaymentProvider = "mercadopago";
export type PaymentMethod = "pix" | "card";
export type PaymentStatus = "pending" | "approved" | "rejected" | "cancelled";

export interface PixPaymentCreatePayload {
  order_id: string;
}

export interface PaymentResponse {
  id: string;
  order_id: string;
  provider: PaymentProvider;
  method: PaymentMethod;
  external_id: string | null;
  status: PaymentStatus;
  amount: string;
  qr_code: string | null;
  copy_paste_code: string | null;
  created_at: string;
  updated_at: string;
}

export type PaymentApiResponse = ApiResponse<PaymentResponse>;
