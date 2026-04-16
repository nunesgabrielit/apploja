import { api } from "@/services/api";
import type { PaymentApiResponse, PixPaymentCreatePayload } from "@/types/payment";

export async function createPixPayment(
  payload: PixPaymentCreatePayload
): Promise<PaymentApiResponse> {
  const { data } = await api.post<PaymentApiResponse>("/payments/mercadopago/pix", payload);
  return data;
}
