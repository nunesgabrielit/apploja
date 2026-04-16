import type { ApiResponse } from "@/types/api";

export interface Address {
  id: string;
  user_id: string;
  recipient_name: string;
  zip_code: string;
  street: string;
  number: string;
  district: string;
  city: string;
  state: string;
  complement: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface AddressPayload {
  recipient_name: string;
  zip_code: string;
  street: string;
  number: string;
  district: string;
  city: string;
  state: string;
  complement?: string | null;
}

export interface AddressUpdatePayload extends AddressPayload {
  is_active?: boolean;
}

export type AddressListResponse = ApiResponse<Address[]>;
export type AddressResponse = ApiResponse<Address>;
