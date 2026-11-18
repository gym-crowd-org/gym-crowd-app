import { Suspense } from "react";

import CrowdInsights from "@/components/crowd-insights";
import Navbar from "@/components/navbar";

export default function Page() {
  return (
    <>
      <Navbar />
      <main className="min-h-screen bg-background">
        <div className="mx-auto max-w-5xl px-4 py-10 sm:px-6 sm:py-12">
          <div className="mb-8 text-center">
            <h1 className="text-3xl font-bold text-primary sm:text-4xl">
              Real-time Crowd Insights
            </h1>
            <p className="mt-2 text-muted-foreground">
              Today&apos;s crowd so far, next to what the model forecast this morning
            </p>
          </div>
          <Suspense fallback={<div className="h-[520px] animate-pulse rounded-xl bg-muted" />}>
            <CrowdInsights />
          </Suspense>
        </div>
      </main>
    </>
  );
}
