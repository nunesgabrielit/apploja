"use client";

import Link from "next/link";
import { Copy, MapPinHouse, PackageCheck, QrCode, Store } from "lucide-react";
import { useEffect, useMemo, useState } from "react";

import { Alert } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { listAddresses } from "@/services/address.service";
import { getApiErrorMessage } from "@/services/api";
import { createCustomerOrder } from "@/services/customer-order.service";
import { createPixPayment } from "@/services/payment.service";
import { calculateShipping } from "@/services/shipping.service";
import { useAuthStore } from "@/store/auth.store";
import { useCartStore } from "@/store/cart.store";
import type { Address } from "@/types/address";
import type { OrderResponse } from "@/types/order";
import type { PaymentResponse } from "@/types/payment";
import type { ShippingCalculateResponse } from "@/types/shipping";

function formatCurrency(value: string | number): string {
  return `R$ ${Number(value).toFixed(2).replace(".", ",")}`;
}

export default function CheckoutPage() {
  const { user, isHydrated } = useAuthStore();
  const { cart, isLoading, refreshCart } = useCartStore();

  const [fulfillmentType, setFulfillmentType] = useState<"pickup" | "delivery">("pickup");
  const [addresses, setAddresses] = useState<Address[]>([]);
  const [selectedAddressId, setSelectedAddressId] = useState<string>("");
  const [zipCode, setZipCode] = useState("");
  const [notes, setNotes] = useState("");
  const [shippingQuote, setShippingQuote] = useState<ShippingCalculateResponse | null>(null);
  const [order, setOrder] = useState<OrderResponse | null>(null);
  const [payment, setPayment] = useState<PaymentResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [paymentWarning, setPaymentWarning] = useState<string | null>(null);
  const [isCalculatingShipping, setIsCalculatingShipping] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [copiedCode, setCopiedCode] = useState(false);

  useEffect(() => {
    if (!isHydrated || user?.role !== "customer") {
      return;
    }

    void refreshCart().catch(() => undefined);
    void listAddresses()
      .then((response) => {
        const activeAddresses = response.data.filter((address) => address.is_active);
        setAddresses(activeAddresses);
        if (activeAddresses.length > 0) {
          setSelectedAddressId(activeAddresses[0].id);
          setZipCode(activeAddresses[0].zip_code);
        }
      })
      .catch(() => undefined);
  }, [isHydrated, refreshCart, user]);

  useEffect(() => {
    if (fulfillmentType === "pickup") {
      setShippingQuote({
        zip_code: null,
        zip_code_normalized: null,
        fulfillment_type: "pickup",
        shipping_price: "0.00",
        estimated_time_text: "Retirada na loja",
        rule_name: "Retirada na loja",
        covered: true,
        calculation_mode: "pickup",
        distance_km: null,
      });
      return;
    }

    setShippingQuote(null);
  }, [fulfillmentType]);

  useEffect(() => {
    if (fulfillmentType !== "delivery") {
      return;
    }

    const selectedAddress = addresses.find((address) => address.id === selectedAddressId);
    if (!selectedAddress) {
      setZipCode("");
      setShippingQuote(null);
      return;
    }

    setZipCode(selectedAddress.zip_code);
    void (async () => {
      try {
        const response = await calculateShipping({
          zip_code: selectedAddress.zip_code,
          address_id: selectedAddress.id,
          fulfillment_type: "delivery",
        });
        setShippingQuote(response.data);
      } catch {
        setShippingQuote(null);
      }
    })();
  }, [addresses, fulfillmentType, selectedAddressId]);

  const subtotal = Number(cart?.subtotal ?? "0");
  const shippingPrice = Number(shippingQuote?.shipping_price ?? "0");
  const total = useMemo(() => subtotal + shippingPrice, [shippingPrice, subtotal]);

  if (isHydrated && user?.role !== "customer") {
    return (
      <div className="mx-auto max-w-5xl px-4 py-16 sm:px-6 lg:px-8">
        <div className="rounded-3xl border border-slate-200 bg-white p-8 text-center shadow-sm">
          <PackageCheck className="mx-auto h-12 w-12 text-slate-300" />
          <h1 className="mt-4 text-2xl font-bold text-slate-900">Entre como cliente para finalizar</h1>
          <p className="mt-2 text-sm text-slate-600">
            O checkout da loja funciona apenas com contas do tipo customer.
          </p>
          <div className="mt-6 flex justify-center gap-3">
            <Link href="/cliente/login">
              <Button>Entrar</Button>
            </Link>
            <Link href="/carrinho">
              <Button variant="secondary">Voltar ao carrinho</Button>
            </Link>
          </div>
        </div>
      </div>
    );
  }

  async function handleCalculateShipping(): Promise<void> {
    try {
      setError(null);
      setPaymentWarning(null);
      setIsCalculatingShipping(true);
      const response = await calculateShipping({
        zip_code: zipCode,
        address_id: selectedAddressId || null,
        fulfillment_type: "delivery",
      });
      setShippingQuote(response.data);
    } catch (requestError) {
      setShippingQuote(null);
      setError(getApiErrorMessage(requestError, "Nao foi possivel calcular o frete para esse CEP."));
    } finally {
      setIsCalculatingShipping(false);
    }
  }

  async function handleCheckout(): Promise<void> {
    if (!cart || cart.items.length === 0) {
      setError("Seu carrinho esta vazio.");
      return;
    }

    if (fulfillmentType === "delivery") {
      if (!selectedAddressId) {
        setError("Selecione ou cadastre um endereco para entrega.");
        return;
      }
      if (!shippingQuote?.covered) {
        setError("Nao foi possivel calcular o frete para o endereco selecionado.");
        return;
      }
    }

    try {
      setError(null);
      setPaymentWarning(null);
      setIsSubmitting(true);

      const orderResponse = await createCustomerOrder({
        fulfillment_type: fulfillmentType,
        address_id: fulfillmentType === "delivery" ? selectedAddressId : null,
        notes: notes.trim() || null,
      });
      setOrder(orderResponse.data);
      await refreshCart().catch(() => undefined);

      try {
        const paymentResponse = await createPixPayment({ order_id: orderResponse.data.id });
        setPayment(paymentResponse.data);
      } catch (paymentError) {
        setPayment(null);
        const providerMessage = getApiErrorMessage(
          paymentError,
          "O pedido foi criado, mas nao foi possivel gerar o PIX agora."
        );

        if (providerMessage.toLowerCase().includes("access token is not configured")) {
          setPaymentWarning(
            "O pedido foi criado com sucesso, mas o PIX nao foi gerado porque o Mercado Pago ainda nao esta configurado neste ambiente local."
          );
        } else {
          setPaymentWarning(`O pedido foi criado com sucesso, mas o pagamento falhou: ${providerMessage}`);
        }
      }
    } catch (requestError) {
      setError(getApiErrorMessage(requestError, "Nao foi possivel criar o pedido e iniciar o pagamento."));
    } finally {
      setIsSubmitting(false);
    }
  }

  async function handleRetryPix(): Promise<void> {
    if (!order) {
      return;
    }

    try {
      setError(null);
      setPaymentWarning(null);
      setIsSubmitting(true);
      const paymentResponse = await createPixPayment({ order_id: order.id });
      setPayment(paymentResponse.data);
    } catch (requestError) {
      const providerMessage = getApiErrorMessage(
        requestError,
        "Nao foi possivel gerar o PIX para este pedido."
      );

      if (providerMessage.toLowerCase().includes("access token is not configured")) {
        setPaymentWarning(
          "O pedido ja existe, mas o PIX continua indisponivel porque o Mercado Pago nao esta configurado neste ambiente local."
        );
      } else {
        setPaymentWarning(`O pedido ja existe, mas o PIX falhou novamente: ${providerMessage}`);
      }
    } finally {
      setIsSubmitting(false);
    }
  }

  async function handleCopyPixCode(): Promise<void> {
    if (!payment?.copy_paste_code) {
      return;
    }
    await navigator.clipboard.writeText(payment.copy_paste_code);
    setCopiedCode(true);
    window.setTimeout(() => setCopiedCode(false), 1500);
  }

  const emptyCart = !isLoading && (!cart || cart.items.length === 0);

  return (
    <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold tracking-tight text-slate-900">Checkout</h1>
        <p className="mt-2 text-sm text-slate-500">
          Feche o pedido, escolha a forma de atendimento e confira o resumo final.
        </p>
      </div>

      {error ? <div className="mb-5"><Alert message={error} /></div> : null}
      {paymentWarning ? (
        <div className="mb-5 rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800">
          {paymentWarning}
        </div>
      ) : null}

      {emptyCart ? (
        <div className="rounded-3xl border border-dashed border-slate-300 bg-white p-10 text-center shadow-sm">
          <PackageCheck className="mx-auto h-12 w-12 text-slate-300" />
          <h2 className="mt-4 text-xl font-semibold text-slate-900">Nao ha itens para fechar pedido</h2>
          <p className="mt-2 text-sm text-slate-600">
            Adicione produtos ao carrinho antes de seguir para o checkout.
          </p>
          <div className="mt-6">
            <Link href="/carrinho">
              <Button>Voltar ao carrinho</Button>
            </Link>
          </div>
        </div>
      ) : (
        <div className="grid gap-8 lg:grid-cols-[1.2fr_0.8fr]">
          <section className="space-y-6">
            <div className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
              <h2 className="text-lg font-semibold text-slate-900">Forma de atendimento</h2>
              <div className="mt-4 grid gap-3 sm:grid-cols-2">
                <button
                  type="button"
                  onClick={() => setFulfillmentType("pickup")}
                  className={`rounded-2xl border p-4 text-left transition ${
                    fulfillmentType === "pickup"
                      ? "border-blue-600 bg-blue-50"
                      : "border-slate-200 bg-white hover:bg-slate-50"
                  }`}
                >
                  <Store className="h-5 w-5 text-blue-600" />
                  <p className="mt-3 font-semibold text-slate-900">Retirada</p>
                  <p className="mt-1 text-sm text-slate-600">
                    Pedido pronto para retirada na loja com frete zero.
                  </p>
                </button>
                <button
                  type="button"
                  onClick={() => setFulfillmentType("delivery")}
                  className={`rounded-2xl border p-4 text-left transition ${
                    fulfillmentType === "delivery"
                      ? "border-blue-600 bg-blue-50"
                      : "border-slate-200 bg-white hover:bg-slate-50"
                  }`}
                >
                  <MapPinHouse className="h-5 w-5 text-blue-600" />
                  <p className="mt-3 font-semibold text-slate-900">Entrega</p>
                  <p className="mt-1 text-sm text-slate-600">
                    Calcule o frete por CEP e prepare o fluxo de entrega.
                  </p>
                </button>
              </div>
            </div>

            <div className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
              <h2 className="text-lg font-semibold text-slate-900">Calculo de frete</h2>
              {fulfillmentType === "pickup" ? (
                <div className="mt-4 rounded-2xl border border-emerald-200 bg-emerald-50 p-4 text-sm text-emerald-700">
                  Retirada selecionada. O pedido sera fechado com frete zero.
                </div>
              ) : (
                <>
                  {addresses.length > 0 ? (
                    <div className="mt-4 space-y-3">
                      <label className="block text-sm font-medium text-slate-700">
                        Selecione o endereco para entrega
                      </label>
                      <select
                        value={selectedAddressId}
                        onChange={(event) => setSelectedAddressId(event.target.value)}
                        className="h-12 w-full rounded-xl border border-slate-300 px-4 text-sm text-slate-900 outline-none transition focus:border-blue-500 focus:ring-2 focus:ring-blue-200"
                      >
                        {addresses.map((address) => (
                          <option key={address.id} value={address.id}>
                            {address.street}, {address.number} - {address.city}/{address.state}
                          </option>
                        ))}
                      </select>
                      <div className="flex flex-col gap-3 sm:flex-row">
                        <input
                          type="text"
                          value={zipCode}
                          readOnly
                          className="h-12 flex-1 rounded-xl border border-slate-300 bg-slate-50 px-4 text-sm text-slate-900 outline-none"
                        />
                        <Button
                          onClick={() => void handleCalculateShipping()}
                          disabled={isCalculatingShipping || !selectedAddressId}
                        >
                          {isCalculatingShipping ? "Calculando..." : "Recalcular frete"}
                        </Button>
                      </div>
                      {selectedAddressId ? (
                        <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4 text-sm text-slate-600">
                          {(() => {
                            const selectedAddress = addresses.find(
                              (address) => address.id === selectedAddressId
                            );
                            if (!selectedAddress) {
                              return "Selecione um endereco para visualizar os dados de entrega.";
                            }

                            return (
                              <>
                                <p className="font-semibold text-slate-900">
                                  Entrega para {selectedAddress.recipient_name}
                                </p>
                                <p className="mt-1">
                                  {selectedAddress.street}, {selectedAddress.number}
                                  {selectedAddress.complement ? ` - ${selectedAddress.complement}` : ""}
                                </p>
                                <p>
                                  {selectedAddress.district} - {selectedAddress.city}/{selectedAddress.state}
                                </p>
                              </>
                            );
                          })()}
                        </div>
                      ) : null}
                    </div>
                  ) : (
                    <div className="mt-4 rounded-2xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-700">
                      Voce ainda nao possui endereco cadastrado para entrega.{" "}
                      <Link href="/perfil" className="font-semibold underline">
                        Cadastrar agora
                      </Link>
                    </div>
                  )}

                  {shippingQuote ? (
                    <div className="mt-4 rounded-2xl border border-slate-200 bg-slate-50 p-4">
                      <p className="text-sm font-semibold text-slate-900">{shippingQuote.rule_name}</p>
                      <p className="mt-1 text-sm text-slate-600">
                        {shippingQuote.estimated_time_text || "Prazo sob consulta"}
                      </p>
                      <p className="mt-2 text-xs uppercase tracking-wide text-slate-500">
                        Modo de calculo: {shippingQuote.calculation_mode === "distance" ? "raio por km" : "faixa por CEP"}
                      </p>
                      {shippingQuote.distance_km ? (
                        <p className="mt-1 text-xs uppercase tracking-wide text-slate-500">
                          Distancia aproximada: {shippingQuote.distance_km} km
                        </p>
                      ) : null}
                      {shippingQuote.zip_code_normalized ? (
                        <p className="mt-2 text-xs uppercase tracking-wide text-slate-500">
                          CEP calculado: {shippingQuote.zip_code_normalized}
                        </p>
                      ) : null}
                      <p className="mt-3 text-xl font-bold text-blue-600">
                        {formatCurrency(shippingQuote.shipping_price)}
                      </p>
                    </div>
                  ) : null}
                </>
              )}
            </div>

            <div className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
              <h2 className="text-lg font-semibold text-slate-900">Observacoes do pedido</h2>
              <textarea
                value={notes}
                onChange={(event) => setNotes(event.target.value)}
                rows={4}
                placeholder="Ex: retirar no periodo da tarde, confirmar por WhatsApp, etc."
                className="mt-4 w-full rounded-2xl border border-slate-300 px-4 py-3 text-sm text-slate-900 outline-none transition focus:border-blue-500 focus:ring-2 focus:ring-blue-200"
              />
            </div>

            {payment ? (
              <div className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
                <div className="flex items-center gap-3">
                  <QrCode className="h-5 w-5 text-blue-600" />
                  <h2 className="text-lg font-semibold text-slate-900">Pagamento PIX gerado</h2>
                </div>
                <p className="mt-3 text-sm text-slate-600">
                  Pedido {order?.id} criado com sucesso. Use o codigo abaixo para concluir o pagamento.
                </p>
                {payment.copy_paste_code ? (
                  <div className="mt-4 rounded-2xl border border-slate-200 bg-slate-50 p-4">
                    <p className="break-all text-sm text-slate-700">{payment.copy_paste_code}</p>
                    <div className="mt-4 flex flex-wrap gap-3">
                      <Button onClick={() => void handleCopyPixCode()}>
                        <Copy className="mr-2 h-4 w-4" />
                        {copiedCode ? "Codigo copiado" : "Copiar codigo PIX"}
                      </Button>
                    </div>
                  </div>
                ) : null}
              </div>
            ) : order ? (
              <div className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
                <div className="flex items-center gap-3">
                  <PackageCheck className="h-5 w-5 text-blue-600" />
                  <h2 className="text-lg font-semibold text-slate-900">Pedido criado</h2>
                </div>
                <p className="mt-3 text-sm text-slate-600">
                  Seu pedido foi criado com sucesso e esta aguardando pagamento.
                </p>
                <div className="mt-4 rounded-2xl border border-slate-200 bg-slate-50 p-4 text-sm text-slate-700">
                  <p><span className="font-semibold">Pedido:</span> {order.id}</p>
                  <p className="mt-1"><span className="font-semibold">Status:</span> {order.order_status}</p>
                  <p className="mt-1"><span className="font-semibold">Pagamento:</span> {order.payment_status}</p>
                </div>
                <div className="mt-4 flex flex-wrap gap-3">
                  <Button onClick={() => void handleRetryPix()} disabled={isSubmitting}>
                    {isSubmitting ? "Tentando novamente..." : "Tentar gerar PIX novamente"}
                  </Button>
                </div>
              </div>
            ) : null}
          </section>

          <aside className="h-fit rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
            <h2 className="text-lg font-semibold text-slate-900">Resumo final</h2>
            <div className="mt-5 space-y-4">
              {cart?.items.map((item) => (
                <div key={item.id} className="rounded-2xl bg-slate-50 p-4">
                  <p className="text-sm font-semibold text-slate-900">{item.name}</p>
                  <p className="mt-1 text-xs text-slate-500">
                    {item.internal_code} - {item.quantity} x {formatCurrency(item.unit_price)}
                  </p>
                </div>
              ))}
            </div>

            <div className="mt-6 space-y-3 border-t border-slate-100 pt-4 text-sm text-slate-600">
              <div className="flex justify-between">
                <span>Subtotal</span>
                <span>{formatCurrency(subtotal)}</span>
              </div>
              <div className="flex justify-between">
                <span>Frete</span>
                <span>{formatCurrency(shippingPrice)}</span>
              </div>
              <div className="flex justify-between border-t border-slate-100 pt-3 text-base font-semibold text-slate-900">
                <span>Total</span>
                <span>{formatCurrency(total)}</span>
              </div>
            </div>

            <div className="mt-6 space-y-3">
              <Button className="w-full" onClick={() => void handleCheckout()} disabled={isSubmitting}>
                {isSubmitting ? "Processando..." : "Gerar pedido"}
              </Button>
              <Link href="/carrinho" className="block">
                <Button variant="secondary" className="w-full">
                  Voltar ao carrinho
                </Button>
              </Link>
            </div>
          </aside>
        </div>
      )}
    </div>
  );
}
