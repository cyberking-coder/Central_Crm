import { apiGet } from "@/lib/api-server";
import type { Customer, Paginated } from "@/lib/types";
import { NewInvoiceForm } from "./new-invoice-form";

export const dynamic = "force-dynamic";

export default async function NewInvoicePage() {
  const customers = await apiGet<Paginated<Customer>>("/customers/?ordering=full_name");
  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-3xl font-semibold tracking-tight">New invoice</h1>
      </header>
      <NewInvoiceForm
        customers={customers.ok ? customers.data.results : []}
      />
    </div>
  );
}
