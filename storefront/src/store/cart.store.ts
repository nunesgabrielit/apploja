"use client";

import { AxiosError } from "axios";
import { create } from "zustand";

import {
  addCartItem,
  getCart,
  removeCartItem,
  updateCartItem,
} from "@/services/cart.service";
import type { CartResponse } from "@/types/cart";
import type { ApiErrorPayload } from "@/types/auth";

interface CartState {
  cart: CartResponse | null;
  isLoading: boolean;
  isMutating: boolean;
  error: string | null;
  refreshCart: () => Promise<CartResponse | null>;
  addItem: (productItemId: string, quantity?: number) => Promise<CartResponse>;
  updateItemQuantity: (itemId: string, quantity: number) => Promise<CartResponse>;
  removeItem: (itemId: string) => Promise<CartResponse>;
  clearCartState: () => void;
}

function parseError(error: unknown): string {
  if (error instanceof AxiosError) {
    const payload = error.response?.data as ApiErrorPayload | undefined;
    return payload?.detail ?? "Nao foi possivel concluir a operacao do carrinho.";
  }
  return "Erro inesperado ao atualizar o carrinho.";
}

export const useCartStore = create<CartState>((set) => ({
  cart: null,
  isLoading: false,
  isMutating: false,
  error: null,
  refreshCart: async () => {
    set({ isLoading: true, error: null });
    try {
      const response = await getCart();
      set({ cart: response.data, isLoading: false });
      return response.data;
    } catch (error) {
      set({ isLoading: false, error: parseError(error) });
      throw error;
    }
  },
  addItem: async (productItemId, quantity = 1) => {
    set({ isMutating: true, error: null });
    try {
      const response = await addCartItem({ product_item_id: productItemId, quantity });
      set({ cart: response.data, isMutating: false });
      return response.data;
    } catch (error) {
      set({ isMutating: false, error: parseError(error) });
      throw error;
    }
  },
  updateItemQuantity: async (itemId, quantity) => {
    set({ isMutating: true, error: null });
    try {
      const response = await updateCartItem(itemId, { quantity });
      set({ cart: response.data, isMutating: false });
      return response.data;
    } catch (error) {
      set({ isMutating: false, error: parseError(error) });
      throw error;
    }
  },
  removeItem: async (itemId) => {
    set({ isMutating: true, error: null });
    try {
      const response = await removeCartItem(itemId);
      set({ cart: response.data, isMutating: false });
      return response.data;
    } catch (error) {
      set({ isMutating: false, error: parseError(error) });
      throw error;
    }
  },
  clearCartState: () => set({ cart: null, error: null, isLoading: false, isMutating: false }),
}));
