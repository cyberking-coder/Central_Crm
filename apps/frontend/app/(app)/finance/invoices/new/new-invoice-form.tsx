"use client";

import { useRouter } from "next/navigation";
import { useState, useTransition } from "react";

import { api } from "@/lib/api-client";
import type { Customer, Invoice } from "@/lib/types";

const input =
  "w-full rounded-md border border-border bg-transparent px-3 py-2 text-sm outline-none focus:border-primary";

type Row = {
  description: string;
  quantity: string;
  unit_price: string;
  tax_rate: string;
};

export function NewInvoiceForm({ customers }: { customers: Customer[] }) {
  const router = useRouter();
  const [customer, setCustomer] = useState("");
  const [discount, setDiscount] = useState("0");
  const [notes, setNotes] = useState("");
  const [rows, setRows] = useState<Row[]>([
    { description: "", quantity: "1", unit_price: "0.00", tax_rate: "0" },
  ]);
  const [error, setError] = useState<string | null>(null);
  const [pending, start] = useTransition();

  function updateRow(i: number, patch: Partial<Row>) {
    setRows((r) => r.map((x, idx) => (idx === i ? { ...x, ...patch } : x)));
  }
  function addRow() {
    setRows((r) => [
      ...r,
      { description: "", quantity: "1", unit_price: "0.00", tax_rate: "0" },
    ]);
  }
  function removeRow(i: number) {
    setRows((r) => (r.length === 1 ? r : r.filter((_, idx) => idx !== i)));
  }

  function submit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    start(async () => {
      const res = await api.post<Invoice>("/finance/invoices/", {
        customer,
        discount,
        notes,
        items: rows,
      });
      if (!res.ok) {
        setError(res.error);
        return;
      }
      router.push(`/finance/invoices/${res.data.id}`);
      router.refresh();
    });
  }

  const estTotal = rows.reduce((sum, r) => {
    const q = Number(r.quantity) || 0;
    const p = Number(r.unit_price) || 0;
    const rate = Number(r.tax_rate) || 0;
    return sum + q * p * (1 + rate / 100);
  }, 0);

  return (
    <form onSubmit={submit} className="max-w-3xl space-y-4">
      <label className="block space-y-1 text-sm">
        <span className="text-muted">Customer *</span>
        <select
          required
          value={customer}
          onChange={(e) => setCustomer(e.target.value)}
          className={input}
        >
          <option value="">—</option>
          {customers.map((c) => (
            <option key={c.id} value={c.id}>
              {c.full_name}
            </option>
          ))}
        </select>
      </label>

      <div className="rounded-xl border border-border p-4">
        <p className="mb-3 text-xs font-medium uppercase tracking-wide text-muted">
          Line items
        </p>
        {rows.map((r, i) => (
          <div key={i} className="mb-2 grid grid-cols-[1fr_80px_100px_80px_32px] gap-2">
            <input
              required
              placeholder="Description"
              value={r.description}
              onChange={(e) => updateRow(i, { description: e.target.value })}
              className={input}
            />
            <input
              type="number"
              min={0.001}
              step="0.001"
              placeholder="Qty"
              value={r.quantity}
              onChange={(e) => updateRow(i, { quantity: e.target.value })}
              className={input}
            />
            <input
              type="number"
              min={0}
              step="0.01"
              placeholder="Price"
              value={r.unit_price}
              onChange={(e) => updateRow(i, { unit_price: e.target.value })}
              className={input}
            />
            <input
              type="number"
              min={0}
              step="0.001"
              placeholder="Tax %"
              value={r.tax_rate}
              onChange={(e) => updateRow(i, { tax_rate: e.target.value })}
              className={input}
            />
            <button
              type="button"
              onClick={() => removeRow(i)}
              className="text-muted hover:text-red-400"
              aria-label="Remove row"
            >
              ✕
            </button>
          </div>
        ))}
        <button
          type="button"
          onClick={addRow}
          className="mt-2 text-xs text-primary hover:underline"
        >
          + Add line
        </button>
        <p className="mt-4 text-right text-sm text-muted">
          Estimated total (incl. tax): <b>{estTotal.toFixed(2)}</b>
        </p>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <label className="block space-y-1 text-sm">
          <span className="text-muted">Discount</span>
          <input
            type="number"
            min={0}
            step="0.01"
            value={discount}
            onChange={(e) => setDiscount(e.target.value)}
            className={input}
          />
        </label>
      </div>

      <label className="block space-y-1 text-sm">
        <span className="text-muted">Notes</span>
        <textarea
          rows={2}
          value={notes}
          onChange={(e) => setNotes(e.target.value)}
          className={input}
        />
      </label>

      {error && <p className="text-sm text-red-400">{error}</p>}

      <button
        type="submit"
        disabled={pending || !customer}
        className="rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-fg disabled:opacity-60"
      >
        {pending ? "Creating…" : "Create invoice"}
      </button>
    </form>
  );
}
