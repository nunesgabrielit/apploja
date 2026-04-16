import { redirect } from "next/navigation";

interface PedidosShortcutDetailPageProps {
  params: Promise<{ id: string }>;
}

export default async function PedidosShortcutDetailPage({
  params
}: PedidosShortcutDetailPageProps): Promise<null> {
  const { id } = await params;
  redirect(`/dashboard/pedidos/${id}`);
}
