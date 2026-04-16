import { api } from "@/services/api";
import type {
  AddressListResponse,
  AddressPayload,
  AddressResponse,
  AddressUpdatePayload,
} from "@/types/address";

export async function listAddresses(): Promise<AddressListResponse> {
  const { data } = await api.get<AddressListResponse>("/addresses");
  return data;
}

export async function createAddress(payload: AddressPayload): Promise<AddressResponse> {
  const { data } = await api.post<AddressResponse>("/addresses", payload);
  return data;
}

export async function updateAddress(
  addressId: string,
  payload: AddressUpdatePayload
): Promise<AddressResponse> {
  const { data } = await api.put<AddressResponse>(`/addresses/${addressId}`, payload);
  return data;
}

export async function deleteAddress(addressId: string): Promise<AddressResponse> {
  const { data } = await api.delete<AddressResponse>(`/addresses/${addressId}`);
  return data;
}
