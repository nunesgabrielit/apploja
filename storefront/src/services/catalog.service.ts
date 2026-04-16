import type { ApiResponse } from "@/types/api";
import type {
  CategoryListResponse,
  ProductCreatePayload,
  ProductItemRead,
  ProductRead,
  ProductUpdatePayload,
  ProductItemListResponse,
  ProductItemStockUpdatePayload,
  ProductListResponse,
  StockMovementListResponse
} from "@/types/catalog";

import { api } from "@/services/api";

export interface BaseListParams {
  page?: number;
  page_size?: number;
}

export interface ProductFilters extends BaseListParams {
  category_id?: string;
  brand?: string;
  search?: string;
}

export interface ProductItemFilters extends BaseListParams {
  product_id?: string;
  category_id?: string;
  brand?: string;
  sku?: string;
  internal_code?: string;
  search?: string;
  low_stock?: boolean;
}

export async function listCategories(params?: BaseListParams): Promise<CategoryListResponse> {
  const { data } = await api.get<CategoryListResponse>("/categories", { params });
  return data;
}

export async function listProducts(params?: ProductFilters): Promise<ProductListResponse> {
  const { data } = await api.get<ProductListResponse>("/products", { params });
  return data;
}

export async function getProduct(productId: string): Promise<ApiResponse<ProductRead>> {
  const { data } = await api.get<ApiResponse<ProductRead>>(`/products/${productId}`);
  return data;
}

export async function createProduct(
  payload: ProductCreatePayload
): Promise<ApiResponse<ProductRead>> {
  const { data } = await api.post<ApiResponse<ProductRead>>("/admin/products", payload);
  return data;
}

export async function updateProduct(
  productId: string,
  payload: ProductUpdatePayload
): Promise<ApiResponse<ProductRead>> {
  const { data } = await api.put<ApiResponse<ProductRead>>(`/admin/products/${productId}`, payload);
  return data;
}

export async function deleteProduct(productId: string): Promise<ApiResponse<ProductRead>> {
  const { data } = await api.delete<ApiResponse<ProductRead>>(`/admin/products/${productId}`);
  return data;
}

export async function listProductItems(
  params?: ProductItemFilters
): Promise<ProductItemListResponse> {
  const { data } = await api.get<ProductItemListResponse>("/product-items", { params });
  return data;
}

export async function getProductItem(itemId: string): Promise<ApiResponse<ProductItemRead>> {
  const { data } = await api.get<ApiResponse<ProductItemRead>>(`/product-items/${itemId}`);
  return data;
}

export async function updateProductItemStock(
  itemId: string,
  payload: ProductItemStockUpdatePayload
): Promise<void> {
  await api.patch(`/admin/product-items/${itemId}/stock`, payload);
}

export async function listStockMovementsByItem(
  productItemId: string,
  params?: BaseListParams
): Promise<StockMovementListResponse> {
  const { data } = await api.get<StockMovementListResponse>(
    `/admin/stock/movements/${productItemId}`,
    { params }
  );
  return data;
}
