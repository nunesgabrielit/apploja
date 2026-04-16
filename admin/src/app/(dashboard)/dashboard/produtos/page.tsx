"use client";

import { Filter, Loader2, Pencil, Plus, Search, Trash2, X } from "lucide-react";
import { type FormEvent, useCallback, useEffect, useMemo, useState } from "react";

import { Alert } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Pagination } from "@/components/ui/pagination";
import {
  createProduct,
  deleteProduct,
  listCategories,
  listProducts,
  updateProduct
} from "@/services/catalog.service";
import type { CategoryListItem, ProductListItem, ProductUpdatePayload } from "@/types/catalog";
import { getApiErrorMessage } from "@/utils/api-error";

const PAGE_SIZE = 10;

export default function ProdutosPage() {
  const [categories, setCategories] = useState<CategoryListItem[]>([]);
  const [products, setProducts] = useState<ProductListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [savingEdit, setSavingEdit] = useState(false);
  const [deletingProductId, setDeletingProductId] = useState<string | null>(null);
  const [editingProduct, setEditingProduct] = useState<ProductListItem | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);

  const [search, setSearch] = useState("");
  const [brandFilter, setBrandFilter] = useState("");
  const [categoryFilter, setCategoryFilter] = useState("");

  const [categoryId, setCategoryId] = useState("");
  const [nameBase, setNameBase] = useState("");
  const [brand, setBrand] = useState("");
  const [description, setDescription] = useState("");
  const [imageUrl, setImageUrl] = useState("");
  const [editCategoryId, setEditCategoryId] = useState("");
  const [editNameBase, setEditNameBase] = useState("");
  const [editBrand, setEditBrand] = useState("");
  const [editDescription, setEditDescription] = useState("");
  const [editImageUrl, setEditImageUrl] = useState("");

  const canCreate = useMemo(() => Boolean(categoryId && nameBase.trim().length >= 2), [categoryId, nameBase]);
  const canEdit = useMemo(
    () => Boolean(editingProduct && editCategoryId && editNameBase.trim().length >= 2),
    [editCategoryId, editNameBase, editingProduct]
  );

  const fetchCatalog = useCallback(async (): Promise<void> => {
    setLoading(true);
    setError(null);
    try {
      const [categoriesResponse, productsResponse] = await Promise.all([
        listCategories({ page: 1, page_size: 100 }),
        listProducts({
          page,
          page_size: PAGE_SIZE,
          category_id: categoryFilter || undefined,
          brand: brandFilter || undefined,
          search: search || undefined
        })
      ]);
      setCategories(categoriesResponse.data);
      setProducts(productsResponse.data);
      setTotalPages(productsResponse.pagination.total_pages);
    } catch (requestError) {
      setError(getApiErrorMessage(requestError, "Não foi possível carregar produtos."));
    } finally {
      setLoading(false);
    }
  }, [brandFilter, categoryFilter, page, search]);

  useEffect(() => {
    void fetchCatalog();
  }, [fetchCatalog]);

  useEffect(() => {
    setPage(1);
  }, [search, brandFilter, categoryFilter]);

  const resetEditModal = (): void => {
    setEditingProduct(null);
    setEditCategoryId("");
    setEditNameBase("");
    setEditBrand("");
    setEditDescription("");
    setEditImageUrl("");
  };

  const openEditModal = (product: ProductListItem): void => {
    setEditingProduct(product);
    setEditCategoryId(product.category.id);
    setEditNameBase(product.name_base);
    setEditBrand(product.brand ?? "");
    setEditDescription(product.description ?? "");
    setEditImageUrl(product.image_url ?? "");
    setSuccessMessage(null);
    setError(null);
  };

  const handleCreateProduct = async (event: FormEvent<HTMLFormElement>): Promise<void> => {
    event.preventDefault();
    if (!canCreate) {
      return;
    }
    setSubmitting(true);
    setError(null);
    setSuccessMessage(null);
    try {
      await createProduct({
        category_id: categoryId,
        name_base: nameBase.trim(),
        brand: brand.trim() || null,
        description: description.trim() || null,
        image_url: imageUrl.trim() || null
      });
      setNameBase("");
      setBrand("");
      setDescription("");
      setImageUrl("");
      setPage(1);
      setSuccessMessage("Produto criado com sucesso.");
      await fetchCatalog();
    } catch (requestError) {
      setError(getApiErrorMessage(requestError, "Não foi possível criar o produto."));
    } finally {
      setSubmitting(false);
    }
  };

  const handleEditProduct = async (event: FormEvent<HTMLFormElement>): Promise<void> => {
    event.preventDefault();
    if (!editingProduct || !canEdit) {
      return;
    }
    setSavingEdit(true);
    setError(null);
    setSuccessMessage(null);
    try {
      const payload: ProductUpdatePayload = {
        category_id: editCategoryId,
        name_base: editNameBase.trim(),
        brand: editBrand.trim() || null,
        description: editDescription.trim() || null,
        image_url: editImageUrl.trim() || null
      };
      await updateProduct(editingProduct.id, payload);
      setSuccessMessage("Produto atualizado com sucesso.");
      resetEditModal();
      await fetchCatalog();
    } catch (requestError) {
      setError(getApiErrorMessage(requestError, "Não foi possível atualizar o produto."));
    } finally {
      setSavingEdit(false);
    }
  };

  const handleDeleteProduct = async (product: ProductListItem): Promise<void> => {
    const confirmed = window.confirm(
      `Confirma a exclusão do produto "${product.name_base}"? A operação é um soft delete.`
    );
    if (!confirmed) {
      return;
    }
    setDeletingProductId(product.id);
    setError(null);
    setSuccessMessage(null);
    try {
      await deleteProduct(product.id);
      setSuccessMessage("Produto desativado com sucesso.");
      await fetchCatalog();
    } catch (requestError) {
      setError(getApiErrorMessage(requestError, "Não foi possível excluir o produto."));
    } finally {
      setDeletingProductId(null);
    }
  };

  return (
    <section className="space-y-6">
      <header>
        <h2 className="text-xl font-semibold text-slate-900">Produtos</h2>
        <p className="mt-1 text-sm text-slate-500">
          Gestão do catálogo base conectado ao backend em tempo real.
        </p>
      </header>

      <div className="rounded-2xl border border-slate-100 bg-white p-6 shadow-sm">
        <div className="mb-4 flex items-center justify-between">
          <h3 className="text-sm font-semibold text-slate-800 flex items-center gap-2">
            <Filter size={16} className="text-blue-600" />
            Filtros de Pesquisa
          </h3>
        </div>
        <div className="grid gap-6 md:grid-cols-3">
          <Input
            label="Buscar por nome"
            placeholder="Ex: Carregador Motorola"
            value={search}
            onChange={(event) => setSearch(event.target.value)}
          />
          <Input
            label="Buscar por marca"
            placeholder="Ex: Samsung"
            value={brandFilter}
            onChange={(event) => setBrandFilter(event.target.value)}
          />
          <div className="space-y-1.5">
            <label className="block text-xs font-semibold text-slate-500 uppercase tracking-wider">
              Filtrar por Categoria
            </label>
            <select
              value={categoryFilter}
              onChange={(event) => setCategoryFilter(event.target.value)}
              className="w-full rounded-lg border border-slate-200 bg-slate-50 px-4 py-2.5 text-sm text-slate-700 outline-none transition focus:border-blue-500 focus:bg-white focus:ring-4 focus:ring-blue-500/10"
            >
              <option value="">Todas</option>
              {categories.map((category) => (
                <option key={category.id} value={category.id}>
                  {category.name}
                </option>
              ))}
            </select>
          </div>
        </div>
        <div className="mt-6 flex items-center gap-3">
          <button 
            onClick={() => fetchCatalog()}
            className="flex items-center gap-2 rounded-full bg-blue-600 px-6 py-2.5 text-sm font-semibold text-white shadow-sm transition hover:bg-blue-700 hover:shadow"
          >
            <Search size={16} />
            Pesquisar
          </button>
          <button 
            onClick={() => {
              setSearch("");
              setBrandFilter("");
              setCategoryFilter("");
            }}
            className="flex items-center gap-2 rounded-full border border-slate-200 bg-white px-6 py-2.5 text-sm font-semibold text-slate-600 transition hover:bg-slate-50 hover:text-slate-900"
          >
            <X size={16} />
            Limpar Filtros
          </button>
        </div>
      </div>


      <div className="overflow-hidden rounded-2xl border border-slate-100 bg-white shadow-sm">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-slate-200">
            <thead className="bg-slate-50">
              <tr className="text-left text-xs uppercase tracking-wide text-slate-500">
                <th className="px-4 py-3">Produto</th>
                <th className="px-4 py-3">Categoria</th>
                <th className="px-4 py-3">Marca</th>
                <th className="px-4 py-3">Codigos</th>
                <th className="px-4 py-3">Itens ativos</th>
                <th className="px-4 py-3">Ações</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 text-sm text-slate-700">
              {loading ? (
                <tr>
                  <td colSpan={6} className="px-4 py-8 text-center text-slate-500">
                    <span className="inline-flex items-center gap-2">
                      <Loader2 className="animate-spin" size={16} />
                      Carregando produtos...
                    </span>
                  </td>
                </tr>
              ) : products.length === 0 ? (
                <tr>
                  <td colSpan={6} className="px-4 py-8 text-center text-slate-500">
                    Nenhum produto encontrado.
                  </td>
                </tr>
              ) : (
                products.map((product) => (
                  <tr key={product.id}>
                    <td className="px-4 py-3">
                      <div className="flex items-start gap-3">
                        <div className="h-14 w-14 overflow-hidden rounded-xl border border-slate-200 bg-slate-100 shadow-sm">
                          {product.image_url ? (
                            <img
                              src={product.image_url}
                              alt={product.name_base}
                              className="h-full w-full object-cover"
                            />
                          ) : (
                            <div className="flex h-full w-full items-center justify-center bg-gradient-to-br from-slate-800 via-slate-700 to-slate-600 text-xs font-semibold uppercase tracking-wide text-white">
                              {product.category.name.slice(0, 2)}
                            </div>
                          )}
                        </div>
                        <div className="min-w-0">
                          <p className="font-medium text-slate-900">{product.name_base}</p>
                          {product.description ? (
                            <p className="line-clamp-2 max-w-xl text-xs leading-5 text-slate-500">
                              {product.description}
                            </p>
                          ) : null}
                        </div>
                      </div>
                    </td>
                    <td className="px-4 py-3">{product.category.name}</td>
                    <td className="px-4 py-3">{product.brand || "-"}</td>
                    <td className="px-4 py-3">
                      <div className="flex max-w-xs flex-wrap gap-2">
                        {product.items.slice(0, 3).map((item) => (
                          <span
                            key={item.id}
                            className="rounded-full border border-slate-200 bg-slate-50 px-2.5 py-1 text-[11px] font-medium text-slate-600"
                          >
                            {item.internal_code}
                          </span>
                        ))}
                        {product.items.length > 3 ? (
                          <span className="rounded-full border border-blue-100 bg-blue-50 px-2.5 py-1 text-[11px] font-medium text-blue-700">
                            +{product.items.length - 3}
                          </span>
                        ) : null}
                      </div>
                    </td>
                    <td className="px-4 py-3">{product.items.length}</td>
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-2">
                        <Button variant="ghost" onClick={() => openEditModal(product)}>
                          <span className="mr-2">
                            <Pencil size={14} />
                          </span>
                          Editar
                        </Button>
                        <Button
                          variant="ghost"
                          onClick={() => void handleDeleteProduct(product)}
                          disabled={deletingProductId === product.id}
                        >
                          <span className="mr-2">
                            {deletingProductId === product.id ? (
                              <Loader2 className="animate-spin" size={14} />
                            ) : (
                              <Trash2 size={14} />
                            )}
                          </span>
                          Excluir
                        </Button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
        <Pagination currentPage={page} totalPages={totalPages} onPageChange={setPage} />
      </div>

      <div className="rounded-xl border border-slate-200 bg-white p-5">
        <h3 className="text-base font-semibold text-slate-900">Criar novo produto</h3>
        <p className="mt-1 text-sm text-slate-500">Cadastro rápido com integração ao endpoint administrativo.</p>
        <form className="mt-4 grid gap-4 md:grid-cols-2" onSubmit={handleCreateProduct}>
          <div className="space-y-1.5">
            <label className="block text-sm font-medium text-slate-700">Categoria</label>
            <select
              value={categoryId}
              onChange={(event) => setCategoryId(event.target.value)}
              className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 outline-none transition focus:border-brand-500 focus:ring-2 focus:ring-brand-200"
              required
            >
              <option value="">Selecione uma categoria</option>
              {categories.map((category) => (
                <option key={category.id} value={category.id}>
                  {category.name}
                </option>
              ))}
            </select>
          </div>
          <Input
            label="Nome base"
            placeholder="Ex: Carregadores Motorola"
            value={nameBase}
            onChange={(event) => setNameBase(event.target.value)}
            required
          />
          <Input
            label="Marca"
            placeholder="Ex: Motorola"
            value={brand}
            onChange={(event) => setBrand(event.target.value)}
          />
          <Input
            label="URL de imagem"
            placeholder="https://..."
            value={imageUrl}
            onChange={(event) => setImageUrl(event.target.value)}
          />
          <div className="md:col-span-2">
            <Input
              label="Descrição"
              placeholder="Descrição comercial do produto"
              value={description}
              onChange={(event) => setDescription(event.target.value)}
            />
          </div>
          <div className="md:col-span-2">
            {error ? <Alert message={error} /> : null}
            {successMessage ? (
              <div className="rounded-lg border border-emerald-200 bg-emerald-50 px-3 py-2 text-sm text-emerald-700">
                {successMessage}
              </div>
            ) : null}
          </div>
          <div className="md:col-span-2">
            <Button type="submit" disabled={!canCreate || submitting}>
              <span className="mr-2">{submitting ? <Loader2 className="animate-spin" size={16} /> : <Plus size={16} />}</span>
              {submitting ? "Criando..." : "Criar produto"}
            </Button>
          </div>
        </form>
      </div>

      {editingProduct ? (
        <div className="fixed inset-0 z-40 flex items-center justify-center bg-slate-900/40 px-4">
          <div className="w-full max-w-2xl rounded-xl bg-white p-5 shadow-xl">
            <div className="mb-4 flex items-center justify-between">
              <h3 className="text-base font-semibold text-slate-900">Editar produto</h3>
              <button
                type="button"
                className="rounded-md p-2 text-slate-600 hover:bg-slate-100"
                onClick={resetEditModal}
              >
                <X size={16} />
              </button>
            </div>
            <form className="grid gap-4 md:grid-cols-2" onSubmit={handleEditProduct}>
              <div className="space-y-1.5">
                <label className="block text-sm font-medium text-slate-700">Categoria</label>
                <select
                  value={editCategoryId}
                  onChange={(event) => setEditCategoryId(event.target.value)}
                  className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 outline-none transition focus:border-brand-500 focus:ring-2 focus:ring-brand-200"
                  required
                >
                  <option value="">Selecione uma categoria</option>
                  {categories.map((category) => (
                    <option key={category.id} value={category.id}>
                      {category.name}
                    </option>
                  ))}
                </select>
              </div>
              <Input
                label="Nome base"
                value={editNameBase}
                onChange={(event) => setEditNameBase(event.target.value)}
                required
              />
              <Input
                label="Marca"
                value={editBrand}
                onChange={(event) => setEditBrand(event.target.value)}
              />
              <Input
                label="URL de imagem"
                value={editImageUrl}
                onChange={(event) => setEditImageUrl(event.target.value)}
              />
              <div className="md:col-span-2">
                <Input
                  label="Descrição"
                  value={editDescription}
                  onChange={(event) => setEditDescription(event.target.value)}
                />
              </div>
              <div className="md:col-span-2 flex items-center gap-3">
                <Button type="submit" disabled={!canEdit || savingEdit}>
                  {savingEdit ? "Salvando..." : "Salvar alterações"}
                </Button>
                <Button type="button" variant="secondary" onClick={resetEditModal}>
                  Cancelar
                </Button>
              </div>
            </form>
          </div>
        </div>
      ) : null}
    </section>
  );
}
