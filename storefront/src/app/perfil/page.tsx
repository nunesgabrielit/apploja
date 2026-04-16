"use client";

import { Edit3, MapPinHouse, Plus, Trash2, UserCircle2 } from "lucide-react";
import { useEffect, useMemo, useState, type FormEvent } from "react";
import Link from "next/link";

import { Alert } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import {
  createAddress,
  deleteAddress,
  listAddresses,
  updateAddress,
} from "@/services/address.service";
import { lookupAddressByZipCode } from "@/services/cep.service";
import { useAuthStore } from "@/store/auth.store";
import type { Address, AddressPayload } from "@/types/address";

interface AddressFormState {
  recipient_name: string;
  zip_code: string;
  street: string;
  number: string;
  district: string;
  city: string;
  state: string;
  complement: string;
}

const emptyForm: AddressFormState = {
  recipient_name: "",
  zip_code: "",
  street: "",
  number: "",
  district: "",
  city: "",
  state: "",
  complement: "",
};

function formatZipCode(value: string): string {
  const digits = value.replace(/\D/g, "").slice(0, 8);
  if (digits.length <= 5) {
    return digits;
  }
  return `${digits.slice(0, 5)}-${digits.slice(5)}`;
}

function buildPayload(form: AddressFormState): AddressPayload {
  return {
    recipient_name: form.recipient_name.trim(),
    zip_code: form.zip_code,
    street: form.street.trim(),
    number: form.number.trim(),
    district: form.district.trim(),
    city: form.city.trim(),
    state: form.state.trim().toUpperCase(),
    complement: form.complement.trim() || null,
  };
}

export default function ProfilePage() {
  const { user, isHydrated } = useAuthStore();
  const [addresses, setAddresses] = useState<Address[]>([]);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [editingAddressId, setEditingAddressId] = useState<string | null>(null);
  const [form, setForm] = useState<AddressFormState>(emptyForm);
  const [isLookingUpZipCode, setIsLookingUpZipCode] = useState(false);
  const [zipLookupError, setZipLookupError] = useState<string | null>(null);

  async function loadAddresses(): Promise<void> {
    setLoading(true);
    try {
      const response = await listAddresses();
      setAddresses(response.data);
      setError(null);
    } catch (requestError) {
      setError(
        requestError instanceof Error
          ? requestError.message
          : "Nao foi possivel carregar seus enderecos."
      );
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    if (!isHydrated || user?.role !== "customer") {
      setLoading(false);
      return;
    }
    void loadAddresses();
  }, [isHydrated, user]);

  const activeAddresses = useMemo(
    () => addresses.filter((address) => address.is_active),
    [addresses]
  );

  function startCreate(): void {
    setEditingAddressId(null);
    setForm(emptyForm);
    setSuccess(null);
    setError(null);
    setZipLookupError(null);
  }

  function startEdit(address: Address): void {
    setEditingAddressId(address.id);
    setForm({
      recipient_name: address.recipient_name,
      zip_code: formatZipCode(address.zip_code),
      street: address.street,
      number: address.number,
      district: address.district,
      city: address.city,
      state: address.state,
      complement: address.complement ?? "",
    });
    setSuccess(null);
    setError(null);
    setZipLookupError(null);
  }

  async function handleZipCodeLookup(rawZipCode: string): Promise<void> {
    const normalizedZipCode = rawZipCode.replace(/\D/g, "");
    if (normalizedZipCode.length !== 8) {
      setZipLookupError(null);
      return;
    }

    try {
      setIsLookingUpZipCode(true);
      setZipLookupError(null);
      const address = await lookupAddressByZipCode(normalizedZipCode);
      setForm((current) => ({
        ...current,
        zip_code: formatZipCode(address.zip_code),
        street: address.street || current.street,
        district: address.district || current.district,
        city: address.city || current.city,
        state: address.state || current.state,
      }));
    } catch (requestError) {
      setZipLookupError(
        requestError instanceof Error
          ? requestError.message
          : "Nao foi possivel localizar o endereco pelo CEP."
      );
    } finally {
      setIsLookingUpZipCode(false);
    }
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault();
    setSubmitting(true);
    setError(null);
    setSuccess(null);

    try {
      if (editingAddressId) {
        await updateAddress(editingAddressId, buildPayload(form));
        setSuccess("Endereco atualizado com sucesso.");
      } else {
        await createAddress(buildPayload(form));
        setSuccess("Endereco cadastrado com sucesso.");
      }
      setForm(emptyForm);
      setEditingAddressId(null);
      setZipLookupError(null);
      await loadAddresses();
    } catch (requestError) {
      setError(
        requestError instanceof Error
          ? requestError.message
          : "Nao foi possivel salvar o endereco."
      );
    } finally {
      setSubmitting(false);
    }
  }

  async function handleDelete(addressId: string): Promise<void> {
    try {
      setError(null);
      setSuccess(null);
      await deleteAddress(addressId);
      setSuccess("Endereco removido com sucesso.");
      await loadAddresses();
    } catch (requestError) {
      setError(
        requestError instanceof Error
          ? requestError.message
          : "Nao foi possivel remover o endereco."
      );
    }
  }

  if (isHydrated && user?.role !== "customer") {
    return (
      <div className="mx-auto max-w-5xl px-4 py-16 sm:px-6 lg:px-8">
        <div className="rounded-3xl border border-slate-200 bg-white p-8 text-center shadow-sm">
          <UserCircle2 className="mx-auto h-12 w-12 text-slate-300" />
          <h1 className="mt-4 text-2xl font-bold text-slate-900">Entre como cliente para ver seu perfil</h1>
          <p className="mt-2 text-sm text-slate-600">
            A area de perfil e enderecos e exclusiva para contas do tipo customer.
          </p>
          <div className="mt-6">
            <Link href="/cliente/login">
              <Button>Entrar</Button>
            </Link>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
      <div className="grid gap-8 lg:grid-cols-[0.75fr_1.25fr]">
        <section className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm h-fit">
          <div className="flex items-center gap-3">
            <UserCircle2 className="h-10 w-10 text-blue-600" />
            <div>
              <h1 className="text-2xl font-bold text-slate-900">Minha conta</h1>
              <p className="text-sm text-slate-500">Dados do cliente autenticado</p>
            </div>
          </div>

          <div className="mt-6 space-y-4 text-sm text-slate-700">
            <div>
              <p className="text-xs uppercase tracking-wide text-slate-500">Nome</p>
              <p className="mt-1 font-medium text-slate-900">{user?.name ?? "-"}</p>
            </div>
            <div>
              <p className="text-xs uppercase tracking-wide text-slate-500">E-mail</p>
              <p className="mt-1 font-medium text-slate-900">{user?.email ?? "-"}</p>
            </div>
            <div>
              <p className="text-xs uppercase tracking-wide text-slate-500">Perfil</p>
              <p className="mt-1 font-medium text-slate-900">{user?.role ?? "-"}</p>
            </div>
          </div>

          <div className="mt-6 rounded-2xl bg-slate-50 p-4 text-sm text-slate-600">
            Seus enderecos salvos aparecem no checkout para liberar pedidos com entrega e calculo de frete por CEP.
          </div>
        </section>

        <section className="space-y-6">
          <div className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
            <div className="flex items-center justify-between gap-4">
              <div className="flex items-center gap-3">
                <MapPinHouse className="h-6 w-6 text-blue-600" />
                <div>
                  <h2 className="text-xl font-semibold text-slate-900">Meus enderecos</h2>
                  <p className="text-sm text-slate-500">
                    Cadastre e mantenha seus dados de entrega atualizados.
                  </p>
                </div>
              </div>
              <Button onClick={startCreate}>
                <Plus className="mr-2 h-4 w-4" />
                Novo endereco
              </Button>
            </div>

            {error ? <div className="mt-4"><Alert message={error} /></div> : null}
            {zipLookupError ? <div className="mt-4"><Alert message={zipLookupError} /></div> : null}
            {success ? (
              <div className="mt-4 rounded-xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-700">
                {success}
              </div>
            ) : null}

            {loading ? (
              <p className="mt-6 text-sm text-slate-500">Carregando enderecos...</p>
            ) : activeAddresses.length === 0 ? (
              <div className="mt-6 rounded-2xl border border-dashed border-slate-300 bg-slate-50 p-6 text-sm text-slate-600">
                Voce ainda nao tem endereco cadastrado.
              </div>
            ) : (
              <div className="mt-6 grid gap-4">
                {activeAddresses.map((address) => (
                  <article
                    key={address.id}
                    className="rounded-2xl border border-slate-200 bg-slate-50 p-5"
                  >
                    <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
                      <div>
                        <h3 className="text-base font-semibold text-slate-900">
                          {address.recipient_name}
                        </h3>
                        <p className="mt-2 text-sm leading-6 text-slate-600">
                          {address.street}, {address.number}
                          {address.complement ? ` • ${address.complement}` : ""}
                          <br />
                          {address.district} • {address.city}/{address.state}
                          <br />
                          CEP {formatZipCode(address.zip_code)}
                        </p>
                      </div>
                      <div className="flex gap-2">
                        <Button variant="secondary" onClick={() => startEdit(address)}>
                          <Edit3 className="mr-2 h-4 w-4" />
                          Editar
                        </Button>
                        <Button variant="ghost" onClick={() => void handleDelete(address.id)}>
                          <Trash2 className="mr-2 h-4 w-4" />
                          Remover
                        </Button>
                      </div>
                    </div>
                  </article>
                ))}
              </div>
            )}
          </div>

          <div className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
            <h2 className="text-xl font-semibold text-slate-900">
              {editingAddressId ? "Editar endereco" : "Cadastrar endereco"}
            </h2>
            <form className="mt-6 grid gap-4 md:grid-cols-2" onSubmit={handleSubmit}>
              <label className="space-y-1.5 md:col-span-2">
                <span className="text-sm font-medium text-slate-700">Nome do destinatario</span>
                <input
                  value={form.recipient_name}
                  onChange={(event) => setForm((current) => ({ ...current, recipient_name: event.target.value }))}
                  className="h-11 w-full rounded-xl border border-slate-300 px-4 text-sm text-slate-900 outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-200"
                  required
                />
              </label>

              <label className="space-y-1.5">
                <span className="text-sm font-medium text-slate-700">CEP</span>
                <input
                  value={form.zip_code}
                  onChange={(event) => {
                    const formattedZipCode = formatZipCode(event.target.value);
                    setForm((current) => ({ ...current, zip_code: formattedZipCode }));
                    if (formattedZipCode.replace(/\D/g, "").length < 8) {
                      setZipLookupError(null);
                    }
                  }}
                  onBlur={(event) => void handleZipCodeLookup(event.target.value)}
                  className="h-11 w-full rounded-xl border border-slate-300 px-4 text-sm text-slate-900 outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-200"
                  required
                />
                <p className="text-xs text-slate-500">
                  {isLookingUpZipCode
                    ? "Buscando endereco pelo CEP..."
                    : "Ao informar um CEP valido, rua, bairro, cidade e estado serao preenchidos automaticamente."}
                </p>
              </label>

              <label className="space-y-1.5">
                <span className="text-sm font-medium text-slate-700">Estado</span>
                <input
                  value={form.state}
                  onChange={(event) =>
                    setForm((current) => ({ ...current, state: event.target.value.toUpperCase().slice(0, 2) }))
                  }
                  className="h-11 w-full rounded-xl border border-slate-300 px-4 text-sm text-slate-900 outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-200"
                  required
                />
              </label>

              <label className="space-y-1.5 md:col-span-2">
                <span className="text-sm font-medium text-slate-700">Rua</span>
                <input
                  value={form.street}
                  onChange={(event) => setForm((current) => ({ ...current, street: event.target.value }))}
                  className="h-11 w-full rounded-xl border border-slate-300 px-4 text-sm text-slate-900 outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-200"
                  required
                />
              </label>

              <label className="space-y-1.5">
                <span className="text-sm font-medium text-slate-700">Numero</span>
                <input
                  value={form.number}
                  onChange={(event) => setForm((current) => ({ ...current, number: event.target.value }))}
                  className="h-11 w-full rounded-xl border border-slate-300 px-4 text-sm text-slate-900 outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-200"
                  required
                />
              </label>

              <label className="space-y-1.5">
                <span className="text-sm font-medium text-slate-700">Complemento</span>
                <input
                  value={form.complement}
                  onChange={(event) => setForm((current) => ({ ...current, complement: event.target.value }))}
                  className="h-11 w-full rounded-xl border border-slate-300 px-4 text-sm text-slate-900 outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-200"
                />
              </label>

              <label className="space-y-1.5">
                <span className="text-sm font-medium text-slate-700">Bairro</span>
                <input
                  value={form.district}
                  onChange={(event) => setForm((current) => ({ ...current, district: event.target.value }))}
                  className="h-11 w-full rounded-xl border border-slate-300 px-4 text-sm text-slate-900 outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-200"
                  required
                />
              </label>

              <label className="space-y-1.5">
                <span className="text-sm font-medium text-slate-700">Cidade</span>
                <input
                  value={form.city}
                  onChange={(event) => setForm((current) => ({ ...current, city: event.target.value }))}
                  className="h-11 w-full rounded-xl border border-slate-300 px-4 text-sm text-slate-900 outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-200"
                  required
                />
              </label>

              <div className="md:col-span-2 flex gap-3">
                <Button type="submit" disabled={submitting}>
                  {submitting ? "Salvando..." : editingAddressId ? "Atualizar endereco" : "Salvar endereco"}
                </Button>
                <Button type="button" variant="secondary" onClick={startCreate}>
                  Limpar formulario
                </Button>
              </div>
            </form>
          </div>
        </section>
      </div>
    </div>
  );
}
