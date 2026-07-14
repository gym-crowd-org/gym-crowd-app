import Navbar from "@/components/navbar";
import CrowdPrediction from "@/components/crowd-prediction";

export default function PredictionsPage() {
  return (
    <>
      <Navbar />
      <main className="min-h-screen bg-background">
        <div className="mx-auto max-w-7xl px-6 py-12">
          {/* Page Title */}
          <div className="mb-12 text-center">
            <h1 className="text-4xl font-bold text-primary">
              Crowd Predictions
            </h1>
            <p className="mt-2 text-muted-foreground">
              Select a date and time to view predicted gym crowd levels
            </p>
          </div>

          {/* Gym Cards Grid */}
          <div className="grid grid-cols-1 gap-8 md:grid-cols-2 lg:grid-cols-2">
            <CrowdPrediction gymName="USC Gym" />
            <CrowdPrediction gymName="UTown Gym" disablePredict={true} />
          </div>
        </div>
      </main>
    </>
  );
}
