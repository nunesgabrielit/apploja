import { redirect } from "next/navigation";

export default function PedidosShortcutPage(): null {
  redirect("/dashboard/pedidos");
}
