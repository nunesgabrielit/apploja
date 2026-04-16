import { ClipboardList, Package, ShoppingCart, Truck } from "lucide-react";

const cards = [
  {
    title: "Pedidos no dia",
    value: "--",
    icon: ShoppingCart
  },
  {
    title: "Itens em baixo estoque",
    value: "--",
    icon: Package
  },
  {
    title: "Pendências de frete",
    value: "--",
    icon: Truck
  },
  {
    title: "Tarefas operacionais",
    value: "--",
    icon: ClipboardList
  }
];

export default function DashboardPage() {
  return (
    <section className="space-y-6">
      <header>
        <h2 className="text-xl font-semibold text-slate-900">Dashboard</h2>
        <p className="mt-1 text-sm text-slate-500">
          Visualização executiva da operação da WM Distribuidora.
        </p>
      </header>
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        {cards.map((card) => (
          <article
            key={card.title}
            className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm"
          >
            <div className="flex items-center justify-between">
              <p className="text-sm text-slate-500">{card.title}</p>
              <card.icon size={18} className="text-brand-600" />
            </div>
            <p className="mt-4 text-3xl font-semibold tracking-tight text-slate-900">{card.value}</p>
          </article>
        ))}
      </div>
    </section>
  );
}
