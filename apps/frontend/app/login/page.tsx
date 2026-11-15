import { Suspense } from "react";

import { LoginForm } from "./login-form";

export const dynamic = "force-dynamic";

export default function LoginPage() {
  return (
    <main className="container flex min-h-screen items-center py-16">
      <Suspense fallback={null}>
        <LoginForm />
      </Suspense>
    </main>
  );
}
