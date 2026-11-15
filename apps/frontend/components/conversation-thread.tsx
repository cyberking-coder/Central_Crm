"use client";

import { useEffect, useState } from "react";

import { api } from "@/lib/api-client";

type Message = {
  id: string;
  channel: string;
  channel_label: string;
  direction: "in" | "out";
  from_address: string;
  to_address: string;
  employee_name: string | null;
  subject: string;
  body: string;
  attachments: { name?: string; url?: string; mime?: string }[];
  duration_seconds: number | null;
  recording_url: string;
  occurred_at: string;
};

const CHANNEL_ICON: Record<string, string> = {
  whatsapp: "💬",
  sms: "📱",
  email: "✉️",
  call: "📞",
  other: "•",
};

type Props =
  | { leadId: string; customerId?: never }
  | { leadId?: never; customerId: string };

export function ConversationThread(props: Props) {
  const [msgs, setMsgs] = useState<Message[] | null>(null);

  async function load() {
    const qp = props.leadId
      ? `lead=${props.leadId}`
      : `customer=${props.customerId}`;
    const res = await api.get<{ results: Message[] }>(
      `/communications/?${qp}&ordering=occurred_at`,
    );
    if (res.ok) setMsgs(res.data.results);
  }

  useEffect(() => {
    load();
    const iv = setInterval(load, 30_000);
    return () => clearInterval(iv);
  }, [props.leadId, props.customerId]);

  return (
    <div className="rounded-xl border border-border bg-panel p-5 shadow-sm">
      <div className="mb-3 flex items-center justify-between">
        <h2 className="text-sm font-medium uppercase tracking-wide text-muted">
          Conversations
        </h2>
        <span className="text-xs text-muted">
          {msgs ? `${msgs.length} message${msgs.length === 1 ? "" : "s"}` : ""}
        </span>
      </div>

      {msgs === null ? (
        <p className="text-sm text-muted">Loading…</p>
      ) : msgs.length === 0 ? (
        <p className="text-sm text-muted">
          No messages yet. Conversations auto-appear when an integration
          (WhatsApp, Email, Call) pushes them to{" "}
          <code className="text-xs">/api/v1/communications/ingest/</code>.
        </p>
      ) : (
        <ol className="space-y-3">
          {msgs.map((m) => (
            <li
              key={m.id}
              className={`flex ${m.direction === "out" ? "justify-end" : "justify-start"}`}
            >
              <div
                className={`max-w-[80%] rounded-xl px-3 py-2 text-sm ${
                  m.direction === "out"
                    ? "bg-primary/15 text-fg"
                    : "bg-border/40 text-fg"
                }`}
              >
                <div className="mb-1 flex items-center gap-2 text-[11px] text-muted">
                  <span>{CHANNEL_ICON[m.channel] ?? "•"}</span>
                  <span>{m.channel_label}</span>
                  <span>·</span>
                  <span>{new Date(m.occurred_at).toLocaleString()}</span>
                  {m.employee_name && (
                    <>
                      <span>·</span>
                      <span>{m.employee_name}</span>
                    </>
                  )}
                </div>
                {m.subject && (
                  <p className="mb-1 font-medium">{m.subject}</p>
                )}
                {m.body && (
                  <p className="whitespace-pre-wrap">{m.body}</p>
                )}
                {m.duration_seconds !== null && (
                  <p className="text-xs text-muted">
                    duration: {Math.round(m.duration_seconds / 60)}m{" "}
                    {m.duration_seconds % 60}s
                  </p>
                )}
                {m.recording_url && (
                  <a
                    href={m.recording_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="mt-1 inline-block text-xs text-primary underline"
                  >
                    ▶ play recording
                  </a>
                )}
                {m.attachments?.length > 0 && (
                  <ul className="mt-1 space-y-0.5 text-xs">
                    {m.attachments.map((a, i) => (
                      <li key={i}>
                        <a
                          href={a.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-primary underline"
                        >
                          📎 {a.name || "attachment"}
                        </a>
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            </li>
          ))}
        </ol>
      )}
    </div>
  );
}
