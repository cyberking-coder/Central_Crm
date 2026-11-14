import Link from "next/link";

export const dynamic = "force-dynamic";

export default function FinanceHome() {
  return (
    <div className="space-y-8">
      <header>
        <h1 className="text-3xl font-semibold tracking-tight">Finance</h1>
        <p className="text-sm text-muted">
          Invoices, payments, refunds, expenses.
        </p>
      </header>
      <div className="grid grid-cols-2 gap-4 md:grid-cols-3">
        <Card href="/finance/invoices" title="Invoices"
              body="Issue, track and export." />
        <Card href="/finance/payments" title="Payments"
              body="Record receipts, refunds." />
        <Card href="/finance/expenses" title="Expenses"
              body="Track outgoings by department." />
      </div>
    </div>
  );
}

function Card({
  href,
  title,
  body,
}: {
  href: string;
  title: string;
  body: string;
}) {
  return (
    <Link
      href={href}
      className="block rounded-xl border border-border p-6 hover:bg-border/10"
    >
      <p className="text-lg font-medium">{title}</p>
      <p className="mt-1 text-sm text-muted">{body}</p>
    </Link>
  );
}
