"use client";

import { useRouter } from "next/navigation";
import { useState, useTransition } from "react";

import { api } from "@/lib/api-client";
import type { Invoice, Payment } from "@/lib/types";

export function InvoiceActions({ invoice }: { invoice: Invoice }) {
  const router = useRouter();
  const [pending, start] = useTransition();
  const [error, setError] = useState<string | null>(null);
  const [showPay, setShowPay] = useState(false);

  function act(url: string) {
    setError(null);
    start(async () => {
      const res = await api.post(url);
      if (!res.ok) {
        setError(res.error);
        return;
      }
      router.refresh();
    });
  }

  function pay(data: FormData) {
    setError(null);
    start(async () => {
      const res = await api.post<Payment>("/finance/payments/", {
        customer: invoice.customer,
        invoice: invoice.id,
        amount: data.get("amount"),
        currency: invoice.currency,
        payment_date: data.get("payment_date"),
        method: data.get("method"),
        transaction_reference: data.get("transaction_reference"),
      });
      if (!res.ok) {
        setError(res.error);
        return;
      }
      setShowPay(false);
      router.refresh();
    });
  }

  return (
    <div className="flex flex-col items-end gap-2">
      <div className="flex gap-2">
        {invoice.status === "draft" && (
          <button
            type="button"
            disabled={pending}
            onClick={() => act(`/finance/invoices/${invoice.id}/issue/`)}
            className="rounded-md bg-primary px-3 py-1.5 text-sm font-medium text-primary-fg"
          >
            Issue
          </button>
        )}
        {["issued", "partially_paid"].includes(invoice.status) && (
          <button
            type="button"
            disabled={pending}
            onClick={() => setShowPay((v) => !v)}
            className="rounded-md bg-primary px-3 py-1.5 text-sm font-medium text-primary-fg"
          >
            Record payment
          </button>
        )}
        {invoice.status !== "paid" && invoice.status !== "void" && (
          <button
            type="button"
            disabled={pending}
            onClick={() => act(`/finance/invoices/${invoice.id}/void/`)}
            className="rounded-md border border-border px-3 py-1.5 text-sm hover:bg-border/30"
          >
            Void
          </button>
        )}
      </div>

      {showPay && (
        <form
          onSubmit={(e) => {
            e.preventDefault();
            pay(new FormData(e.currentTarget));
          }}
          className="mt-2 flex flex-wrap items-center gap-2 rounded-xl border border-border bg-bg p-3 text-sm"
        >
          <input
            name="amount"
            type="number"
            min={0.01}
            step="0.01"
            placeholder="Amount"
            required
            className="w-28 rounded-md border border-border bg-transparent px-2 py-1"
          />
          <input
            name="payment_date"
            type="date"
            required
            defaultValue={new Date().toISOString().slice(0, 10)}
            className="rounded-md border border-border bg-transparent px-2 py-1"
          />
          <select
            name="method"
            defaultValue="cash"
            className="rounded-md border border-border bg-bg px-2 py-1"
          >
            <option value="cash">Cash</option>
            <option value="bank_transfer">Bank</option>
            <option value="upi">UPI</option>
            <option value="card">Card</option>
            <option value="gateway">Gateway</option>
            <option value="other">Other</option>
          </select>
          <input
            name="transaction_reference"
            placeholder="Ref (optional)"
            className="w-40 rounded-md border border-border bg-transparent px-2 py-1"
          />
          <button
            type="submit"
            disabled={pending}
            className="rounded-md bg-primary px-3 py-1 text-xs font-medium text-primary-fg"
          >
            Save
          </button>
        </form>
      )}
      {error && <p className="text-xs text-red-400">{error}</p>}
    </div>
  );
}
