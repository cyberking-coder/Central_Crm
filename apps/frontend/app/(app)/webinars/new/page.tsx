import { NewWebinarForm } from "./new-webinar-form";

export default function NewWebinarPage() {
  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-3xl font-semibold tracking-tight">New webinar</h1>
      </header>
      <NewWebinarForm />
    </div>
  );
}
