"use client";

import { MapPinned, Plus, Save, Trash2, Truck } from "lucide-react";
import { useEffect, useState, type FormEvent } from "react";

import { Alert } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import {
  createDistanceShippingRule,
  deleteDistanceShippingRule,
  getStoreShippingConfig,
  listDistanceShippingRules,
  saveStoreShippingConfig,
  updateDistanceShippingRule
} from "@/services/shipping.service";
import type {
  ShippingDistanceRule,
  ShippingDistanceRulePayload,
  ShippingStoreConfigPayload
} from "@/types/shipping";

interface StoreConfigFormState extends ShippingStoreConfigPayload {}

const defaultStoreForm: StoreConfigFormState = {
  store_name: "WM Distribuidora",
  zip_code: "",
  street: "",
  number: "",
  district: "",
  city: "",
  state: "",
  complement: ""
};

const defaultDistanceForm: ShippingDistanceRulePayload = {
  rule_name: "",
  max_distance_km: "",
  shipping_price: "",
  estimated_time_text: "Entrega local",
  sort_order: 0
};

function formatZipCode(value: string): string {
  const digits = value.replace(/\D/g, "").slice(0, 8);
  if (digits.length <= 5) {
    return digits;
  }
  return `${digits.slice(0, 5)}-${digits.slice(5)}`;
}

export default function FretePage() {
  const [storeForm, setStoreForm] = useState<StoreConfigFormState>(defaultStoreForm);
  const [distanceForm, setDistanceForm] = useState<ShippingDistanceRulePayload>(defaultDistanceForm);
  const [rules, setRules] = useState<ShippingDistanceRule[]>([]);
  const [loading, setLoading] = useState(true);
  const [savingStore, setSavingStore] = useState(false);
  const [savingRule, setSavingRule] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  async function loadData(): Promise<void> {
    setLoading(true);
    try {
      const [storeResponse, rulesResponse] = await Promise.all([
        getStoreShippingConfig(),
        listDistanceShippingRules()
      ]);

      if (storeResponse.data) {
        setStoreForm({
          store_name: storeResponse.data.store_name,
          zip_code: formatZipCode(storeResponse.data.zip_code),
          street: storeResponse.data.street,
          number: storeResponse.data.number,
          district: storeResponse.data.district,
          city: storeResponse.data.city,
          state: storeResponse.data.state,
          complement: storeResponse.data.complement ?? ""
        });
      }

      setRules(rulesResponse.data);
      setError(null);
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Nao foi possivel carregar o modulo de frete.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void loadData();
  }, []);

  async function handleSaveStoreConfig(event: FormEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault();
    try {
      setSavingStore(true);
      setError(null);
      setSuccess(null);
      await saveStoreShippingConfig({
        ...storeForm,
        zip_code: storeForm.zip_code,
        complement: storeForm.complement || null
      });
      setSuccess("Endereco base da loja salvo com sucesso.");
      await loadData();
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Nao foi possivel salvar o endereco da loja.");
    } finally {
      setSavingStore(false);
    }
  }

  async function handleCreateRule(event: FormEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault();
    try {
      setSavingRule(true);
      setError(null);
      setSuccess(null);
      await createDistanceShippingRule({
        ...distanceForm,
        estimated_time_text: distanceForm.estimated_time_text || null
      });
      setDistanceForm(defaultDistanceForm);
      setSuccess("Faixa de frete criada com sucesso.");
      await loadData();
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Nao foi possivel criar a faixa de frete.");
    } finally {
      setSavingRule(false);
    }
  }

  async function handleToggleRule(rule: ShippingDistanceRule): Promise<void> {
    try {
      setError(null);
      setSuccess(null);
      await updateDistanceShippingRule(rule.id, { is_active: !rule.is_active });
      setSuccess("Faixa de frete atualizada com sucesso.");
      await loadData();
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Nao foi possivel atualizar a faixa.");
    }
  }

  async function handleDeleteRule(ruleId: string): Promise<void> {
    try {
      setError(null);
      setSuccess(null);
      await deleteDistanceShippingRule(ruleId);
      setSuccess("Faixa de frete desativada com sucesso.");
      await loadData();
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Nao foi possivel remover a faixa.");
    }
  }

  return (
    <section className="space-y-6">
      <header>
        <h2 className="text-2xl font-semibold text-slate-900">Frete por raio</h2>
        <p className="mt-1 text-sm text-slate-500">
          Configure o endereco base da loja e controle a cobranca por distancia em km.
        </p>
      </header>

      {error ? <Alert message={error} /> : null}
      {success ? (
        <div className="rounded-xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-700">
          {success}
        </div>
      ) : null}

      <div className="grid gap-6 xl:grid-cols-[1.1fr_0.9fr]">
        <form onSubmit={handleSaveStoreConfig} className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
          <div className="flex items-center gap-3">
            <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-brand-50 text-brand-700">
              <MapPinned size={22} />
            </div>
            <div>
              <h3 className="text-lg font-semibold text-slate-900">Endereco da loja</h3>
              <p className="text-sm text-slate-500">Ponto de origem usado para calcular o raio de entrega.</p>
            </div>
          </div>

          <div className="mt-6 grid gap-4 md:grid-cols-2">
            <input
              value={storeForm.store_name}
              onChange={(event) => setStoreForm((current) => ({ ...current, store_name: event.target.value }))}
              className="h-12 rounded-2xl border border-slate-300 px-4 text-sm outline-none focus:border-brand-500"
              placeholder="Nome da loja"
              required
            />
            <input
              value={storeForm.zip_code}
              onChange={(event) =>
                setStoreForm((current) => ({ ...current, zip_code: formatZipCode(event.target.value) }))
              }
              className="h-12 rounded-2xl border border-slate-300 px-4 text-sm outline-none focus:border-brand-500"
              placeholder="CEP"
              required
            />
            <input
              value={storeForm.street}
              onChange={(event) => setStoreForm((current) => ({ ...current, street: event.target.value }))}
              className="h-12 rounded-2xl border border-slate-300 px-4 text-sm outline-none focus:border-brand-500 md:col-span-2"
              placeholder="Rua"
              required
            />
            <input
              value={storeForm.number}
              onChange={(event) => setStoreForm((current) => ({ ...current, number: event.target.value }))}
              className="h-12 rounded-2xl border border-slate-300 px-4 text-sm outline-none focus:border-brand-500"
              placeholder="Numero"
              required
            />
            <input
              value={storeForm.complement ?? ""}
              onChange={(event) => setStoreForm((current) => ({ ...current, complement: event.target.value }))}
              className="h-12 rounded-2xl border border-slate-300 px-4 text-sm outline-none focus:border-brand-500"
              placeholder="Complemento"
            />
            <input
              value={storeForm.district}
              onChange={(event) => setStoreForm((current) => ({ ...current, district: event.target.value }))}
              className="h-12 rounded-2xl border border-slate-300 px-4 text-sm outline-none focus:border-brand-500"
              placeholder="Bairro"
              required
            />
            <input
              value={storeForm.city}
              onChange={(event) => setStoreForm((current) => ({ ...current, city: event.target.value }))}
              className="h-12 rounded-2xl border border-slate-300 px-4 text-sm outline-none focus:border-brand-500"
              placeholder="Cidade"
              required
            />
            <input
              value={storeForm.state}
              onChange={(event) =>
                setStoreForm((current) => ({ ...current, state: event.target.value.toUpperCase().slice(0, 2) }))
              }
              className="h-12 rounded-2xl border border-slate-300 px-4 text-sm outline-none focus:border-brand-500"
              placeholder="UF"
              required
            />
          </div>

          <div className="mt-6">
            <Button type="submit" disabled={savingStore}>
              <Save className="mr-2 h-4 w-4" />
              {savingStore ? "Salvando..." : "Salvar endereco base"}
            </Button>
          </div>
        </form>

        <form onSubmit={handleCreateRule} className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
          <div className="flex items-center gap-3">
            <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-brand-50 text-brand-700">
              <Truck size={22} />
            </div>
            <div>
              <h3 className="text-lg font-semibold text-slate-900">Nova faixa de distancia</h3>
              <p className="text-sm text-slate-500">Cadastre novas faixas ou ajuste a precificacao do raio.</p>
            </div>
          </div>

          <div className="mt-6 grid gap-4">
            <input
              value={distanceForm.rule_name}
              onChange={(event) => setDistanceForm((current) => ({ ...current, rule_name: event.target.value }))}
              className="h-12 rounded-2xl border border-slate-300 px-4 text-sm outline-none focus:border-brand-500"
              placeholder="Nome da faixa"
              required
            />
            <div className="grid gap-4 md:grid-cols-2">
              <input
                value={distanceForm.max_distance_km}
                onChange={(event) => setDistanceForm((current) => ({ ...current, max_distance_km: event.target.value }))}
                className="h-12 rounded-2xl border border-slate-300 px-4 text-sm outline-none focus:border-brand-500"
                placeholder="Raio maximo em km"
                required
              />
              <input
                value={distanceForm.shipping_price}
                onChange={(event) => setDistanceForm((current) => ({ ...current, shipping_price: event.target.value }))}
                className="h-12 rounded-2xl border border-slate-300 px-4 text-sm outline-none focus:border-brand-500"
                placeholder="Valor do frete"
                required
              />
            </div>
            <div className="grid gap-4 md:grid-cols-2">
              <input
                value={distanceForm.estimated_time_text ?? ""}
                onChange={(event) =>
                  setDistanceForm((current) => ({ ...current, estimated_time_text: event.target.value }))
                }
                className="h-12 rounded-2xl border border-slate-300 px-4 text-sm outline-none focus:border-brand-500"
                placeholder="Prazo estimado"
              />
              <input
                type="number"
                value={distanceForm.sort_order}
                onChange={(event) =>
                  setDistanceForm((current) => ({ ...current, sort_order: Number(event.target.value) }))
                }
                className="h-12 rounded-2xl border border-slate-300 px-4 text-sm outline-none focus:border-brand-500"
                placeholder="Ordem"
                min={0}
              />
            </div>
          </div>

          <div className="mt-6">
            <Button type="submit" disabled={savingRule}>
              <Plus className="mr-2 h-4 w-4" />
              {savingRule ? "Salvando..." : "Adicionar faixa"}
            </Button>
          </div>
        </form>
      </div>

      <section className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
        <div className="flex items-center justify-between gap-4">
          <div>
            <h3 className="text-lg font-semibold text-slate-900">Faixas ativas de entrega</h3>
            <p className="text-sm text-slate-500">
              O sistema aplica a primeira faixa que cobrir a distancia do cliente ate a loja.
            </p>
          </div>
        </div>

        {loading ? (
          <p className="mt-6 text-sm text-slate-500">Carregando modulo de frete...</p>
        ) : (
          <div className="mt-6 grid gap-4 lg:grid-cols-2">
            {rules.map((rule) => (
              <article key={rule.id} className="rounded-2xl border border-slate-200 bg-slate-50 p-5">
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <p className="text-base font-semibold text-slate-900">{rule.rule_name}</p>
                    <p className="mt-1 text-sm text-slate-500">
                      Ate {rule.max_distance_km} km • R$ {Number(rule.shipping_price).toFixed(2).replace(".", ",")}
                    </p>
                    <p className="mt-2 text-sm text-slate-600">
                      {rule.estimated_time_text || "Prazo sob consulta"}
                    </p>
                  </div>
                  <span
                    className={`rounded-full px-3 py-1 text-xs font-semibold ${
                      rule.is_active
                        ? "bg-emerald-100 text-emerald-700"
                        : "bg-slate-200 text-slate-600"
                    }`}
                  >
                    {rule.is_active ? "Ativa" : "Inativa"}
                  </span>
                </div>

                <div className="mt-4 flex flex-wrap gap-3">
                  <Button variant="secondary" onClick={() => void handleToggleRule(rule)}>
                    {rule.is_active ? "Desativar" : "Reativar"}
                  </Button>
                  <Button variant="ghost" onClick={() => void handleDeleteRule(rule.id)}>
                    <Trash2 className="mr-2 h-4 w-4" />
                    Remover
                  </Button>
                </div>
              </article>
            ))}
          </div>
        )}
      </section>
    </section>
  );
}
