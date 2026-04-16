import { api } from "@/services/api";
import type {
  CartApiResponse,
  CartItemCreatePayload,
  CartItemUpdatePayload,
} from "@/types/cart";

export async function getCart(): Promise<CartApiResponse> {
  const { data } = await api.get<CartApiResponse>("/cart");
  return data;
}

export async function addCartItem(payload: CartItemCreatePayload): Promise<CartApiResponse> {
  const { data } = await api.post<CartApiResponse>("/cart/items", payload);
  return data;
}

export async function updateCartItem(
  itemId: string,
  payload: CartItemUpdatePayload
): Promise<CartApiResponse> {
  const { data } = await api.put<CartApiResponse>(`/cart/items/${itemId}`, payload);
  return data;
}

export async function removeCartItem(itemId: string): Promise<CartApiResponse> {
  const { data } = await api.delete<CartApiResponse>(`/cart/items/${itemId}`);
  return data;
}
