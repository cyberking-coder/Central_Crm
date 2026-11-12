import { redirect } from "next/navigation";

import { getMe } from "@/lib/auth";

export const dynamic = "force-dynamic";

export default async function RootPage() {
  const me = await getMe();
  redirect(me ? "/dashboard" : "/login");
}
