import Navbar from "@/components/navbar";
import Link from "next/link";

export default function Page() {
  return (
    <>
      <Navbar />
      <main className="min-h-screen bg-background">
        <div className="mx-auto max-w-7xl px-6 py-12">
          <div className="flex flex-col items-center justify-center gap-8">
            <div className="text-center">
              <h1 className="mb-4 text-4xl font-bold text-primary">
                Real-time Crowd Insights
              </h1>
              <p className="text-lg text-muted-foreground">Coming Soon</p>
            </div>
            <div className="rounded-2xl border-2 border-border bg-card p-12 shadow-lg">
              <p className="text-center text-base text-foreground">
                Live crowd monitoring data will be available here shortly. Check
                out{" "}
                <Link
                  href="/predictions"
                  className="text-primary hover:underline font-bold"
                >
                  Crowd Predictions
                </Link>{" "}
                machine for now!
              </p>
            </div>
          </div>
        </div>
      </main>
    </>
  );
}
