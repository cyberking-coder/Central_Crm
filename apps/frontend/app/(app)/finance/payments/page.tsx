import { apiGet } from "@/lib/api-server";
import type { Paginated, Payment } from "@/lib/types";

export const dynamic = "force-dynamic";

export default async function PaymentsPage() {
  const result = await apiGet<Paginated<Payment>>("/finance/payments/");

  return (
    <div className="space-y-6">
      <header className="flex items-end justify-between">
        <div>
          <h1 className="text-3xl font-semibold tracking-tight">Payments</h1>
          <p className="text-sm text-muted">
            {result.ok ? `${result.data.count} total` : "—"}
          </p>
        </div>
        <a
          href="/api/v1/finance/payments/export/"
          className="rounded-md border border-border px-3 py-1.5 text-sm hover:bg-border/30"
        >
          Export CSV
        </a>
      </header>

      {!result.ok ? (
        <p className="text-red-400">Failed: {result.detail}</p>
      ) : (result.data.results ?? []).length === 0 ? (
        <div className="rounded-xl border border-dashed border-border p-12 text-center text-muted">
          No payments yet. Create an invoice and record a payment against it.
        </div>
      ) : (
        <div className="overflow-hidden rounded-xl border border-border">
          <table className="w-full text-sm">
            <thead className="bg-border/20 text-left text-xs uppercase tracking-wide text-muted">
              <tr>
                <th className="px-4 py-3">Date</th>
                <th className="px-4 py-3">Customer</th>
                <th className="px-4 py-3">Invoice</th>
                <th className="px-4 py-3 text-right">Amount</th>
                <th className="px-4 py-3">Method</th>
                <th className="px-4 py-3">Status</th>
              </tr>
            </thead>
            <tbody>
              {result.data.results.map((p) => (
                <tr key={p.id} className="border-t border-border hover:bg-border/10">
                  <td className="px-4 py-3 text-muted">
                    {new Date(p.payment_date).toLocaleDateString()}
                  </td>
                  <td className="px-4 py-3">{p.customer_name}</td>
                  <td className="px-4 py-3 font-mono text-xs">
                    {p.invoice_number ?? "—"}
                  </td>
                  <td className="px-4 py-3 text-right font-mono">
                    {p.currency} {p.amount}
                  </td>
                  <td className="px-4 py-3">{p.method}</td>
                  <td className="px-4 py-3 capitalize">
                    {p.status.replace("_", " ")}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
