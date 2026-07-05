'use client'

import { useState } from 'react'
import { ChevronDown } from 'lucide-react'

interface CrowdPredictionProps {
  gymName: string
}

export default function CrowdPrediction({ gymName }: CrowdPredictionProps) {
  const [selectedDate, setSelectedDate] = useState<string>(new Date().toISOString().split('T')[0])
  const [selectedTime, setSelectedTime] = useState<string>('13:00')

  // Generate time options in 15-minute intervals
  const generateTimeOptions = () => {
    const times = []
    for (let hour = 0; hour < 24; hour++) {
      for (let minute = 0; minute < 60; minute += 15) {
        times.push(`${hour.toString().padStart(2, '0')}:${minute.toString().padStart(2, '0')}`)
      }
    }
    return times
  }

  const timeOptions = generateTimeOptions()

  // Mock crowd data (in real app, this would come from an API)
  const getCrowdLevel = (time: string) => {
    const hour = parseInt(time.split(':')[0])
    // Peak times: 7-9am, 12-1pm, 5-7pm
    if ((hour >= 7 && hour < 9) || (hour >= 12 && hour < 13) || (hour >= 17 && hour < 19)) {
      return { level: 'High', percentage: 85, color: 'bg-red-500' }
    } else if ((hour >= 9 && hour < 12) || (hour >= 13 && hour < 17) || (hour >= 19 && hour < 21)) {
      return { level: 'Medium', percentage: 55, color: 'bg-yellow-500' }
    } else {
      return { level: 'Low', percentage: 20, color: 'bg-green-500' }
    }
  }

  const crowdData = getCrowdLevel(selectedTime)

  return (
    <div className="flex flex-col gap-6 rounded-2xl border-2 border-border bg-card p-8 shadow-lg transition-transform hover:shadow-xl">
      {/* Gym Name */}
      <h2 className="text-center text-2xl font-bold text-primary">{gymName}</h2>

      {/* Date and Time Selection */}
      <div className="flex flex-col gap-4">
        {/* Date Picker */}
        <div className="flex flex-col gap-2">
          <label className="text-sm font-semibold text-foreground">Date</label>
          <input
            type="date"
            value={selectedDate}
            onChange={(e) => setSelectedDate(e.target.value)}
            className="rounded-lg border border-border bg-background px-4 py-2 text-foreground transition-all focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20"
          />
        </div>

        {/* Time Picker */}
        <div className="flex flex-col gap-2">
          <label className="text-sm font-semibold text-foreground">Time</label>
          <div className="relative">
            <select
              value={selectedTime}
              onChange={(e) => setSelectedTime(e.target.value)}
              className="w-full appearance-none rounded-lg border border-border bg-background px-4 py-2 pr-10 text-foreground transition-all focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20"
            >
              {timeOptions.map((time) => (
                <option key={time} value={time}>
                  {time}
                </option>
              ))}
            </select>
            <ChevronDown className="pointer-events-none absolute right-3 top-1/2 h-5 w-5 -translate-y-1/2 text-muted-foreground" />
          </div>
        </div>
      </div>

      {/* Crowd Level Display */}
      <div className="flex flex-col gap-4">
        <div className="flex items-center justify-between">
          <span className="text-sm font-semibold text-foreground">Predicted Crowd Level</span>
          <span className="rounded-full bg-secondary px-3 py-1 text-sm font-bold text-secondary-foreground">
            {crowdData.level}
          </span>
        </div>

        {/* Progress Bar */}
        <div className="w-full gap-2">
          <div className="h-3 w-full overflow-hidden rounded-full bg-muted">
            <div
              className={`h-full ${crowdData.color} transition-all duration-300`}
              style={{ width: `${crowdData.percentage}%` }}
            />
          </div>
          <p className="text-right text-xs text-muted-foreground">{crowdData.percentage}% capacity</p>
        </div>
      </div>

      {/* Additional Info */}
      <div className="rounded-lg bg-secondary/10 p-4">
        <p className="text-center text-sm text-foreground">
          {selectedDate} at {selectedTime}
        </p>
      </div>
    </div>
  )
}
