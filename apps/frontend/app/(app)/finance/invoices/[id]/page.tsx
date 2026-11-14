import { notFound } from "next/navigation";

import { apiGet } from "@/lib/api-server";
import type { Invoice, Paginated, Payment } from "@/lib/types";
import { InvoiceActions } from "./invoice-actions";

export const dynamic = "force-dynamic";

export default async function InvoiceDetail({
  params,
}: {
  params: { id: string };
}) {
  const invoice = await apiGet<Invoice>(`/finance/invoices/${params.id}/`);
  if (!invoice.ok) {
    if (invoice.status === 404) notFound();
    return <p className="text-red-400">Failed: {invoice.detail}</p>;
  }
  const payments = await apiGet<Paginated<Payment>>(
    `/finance/payments/?invoice=${params.id}`,
  );

  return (
    <div className="space-y-8">
      <header className="flex items-start justify-between gap-4">
        <div>
          <p className="text-xs uppercase tracking-widest text-muted">Invoice</p>
          <h1 className="text-3xl font-semibold tracking-tight font-mono">
            {invoice.data.number}
          </h1>
          <p className="mt-1 text-sm text-muted">
            {invoice.data.customer_name} ·{" "}
            <span className="capitalize">
              {invoice.data.status.replace("_", " ")}
            </span>
          </p>
        </div>
        <InvoiceActions invoice={invoice.data} />
      </header>

      <section className="grid grid-cols-2 gap-6">
        <div className="rounded-xl border border-border p-6">
          <h2 className="mb-4 text-sm font-medium uppercase tracking-wide text-muted">
            Line items
          </h2>
          <table className="w-full text-sm">
            <thead className="text-left text-xs text-muted">
              <tr>
                <th className="pb-2">Description</th>
                <th className="pb-2 text-right">Qty</th>
                <th className="pb-2 text-right">Price</th>
                <th className="pb-2 text-right">Tax</th>
                <th className="pb-2 text-right">Amount</th>
              </tr>
            </thead>
            <tbody>
              {invoice.data.items.map((it) => (
                <tr key={it.id} className="border-t border-border">
                  <td className="py-2">{it.description}</td>
                  <td className="py-2 text-right font-mono">{it.quantity}</td>
                  <td className="py-2 text-right font-mono">{it.unit_price}</td>
                  <td className="py-2 text-right font-mono">{it.tax_rate}%</td>
                  <td className="py-2 text-right font-mono">{it.amount}</td>
                </tr>
              ))}
            </tbody>
          </table>
          <dl className="mt-4 space-y-1 text-right text-sm">
            <div>
              <dt className="inline text-muted">Subtotal:</dt>{" "}
              <span className="font-mono">{invoice.data.subtotal}</span>
            </div>
            <div>
              <dt className="inline text-muted">Tax:</dt>{" "}
              <span className="font-mono">{invoice.data.tax}</span>
            </div>
            <div>
              <dt className="inline text-muted">Discount:</dt>{" "}
              <span className="font-mono">−{invoice.data.discount}</span>
            </div>
            <div className="border-t border-border pt-1 text-base">
              <dt className="inline text-muted">Total:</dt>{" "}
              <span className="font-mono font-semibold">
                {invoice.data.currency} {invoice.data.total}
              </span>
            </div>
          </dl>
        </div>

        <div className="rounded-xl border border-border p-6">
          <h2 className="mb-4 text-sm font-medium uppercase tracking-wide text-muted">
            Payments
          </h2>
          {payments.ok && payments.data.results.length > 0 ? (
            <ul className="space-y-2 text-sm">
              {payments.data.results.map((p) => (
                <li
                  key={p.id}
                  className="flex items-center justify-between rounded-md border border-border p-2"
                >
                  <div>
                    <p className="font-mono">
                      {p.currency} {p.amount}
                    </p>
                    <p className="text-xs text-muted">
                      {p.method} · {new Date(p.payment_date).toLocaleDateString()}{" "}
                      · {p.status}
                    </p>
                  </div>
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-sm text-muted">No payments recorded yet.</p>
          )}
        </div>
      </section>
    </div>
  );
}
