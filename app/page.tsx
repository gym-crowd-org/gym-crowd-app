import Navbar from '@/components/navbar'

export default function Page() {
  return (
    <>
      <Navbar />
      <main className="min-h-screen bg-background">
        <div className="mx-auto max-w-7xl px-6 py-12">
          <div className="flex flex-col items-center justify-center gap-8">
            <div className="text-center">
              <h1 className="mb-4 text-4xl font-bold text-primary">Real-time Crowd Insights</h1>
              <p className="text-lg text-muted-foreground">Coming Soon</p>
            </div>
            <div className="rounded-2xl border-2 border-border bg-card p-12 shadow-lg">
              <p className="text-center text-base text-foreground">
                Live crowd monitoring data will be available here shortly. Check back soon!
              </p>
            </div>
          </div>
        </div>
      </main>
    </>
  )
}
