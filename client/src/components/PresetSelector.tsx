import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"

export type TTSPreset = "natural" | "clear" | "fast" | "slow" | "loud" | null

export interface TTSSettings {
  length_scale: number
  volume: number
  noise_scale: number
  noise_w: number
  normalize_audio: boolean
}

const PRESETS = [
  { value: null, label: "Custom", description: "Manual configuration" },
  { value: "natural" as const, label: "Natural", description: "Balanced everyday settings" },
  { value: "clear" as const, label: "Clear", description: "Slower, precise articulation" },
  { value: "fast" as const, label: "Fast", description: "Quick delivery" },
  { value: "slow" as const, label: "Slow", description: "Very slow for learning" },
  { value: "loud" as const, label: "Loud", description: "Increased volume" },
]

export const PRESET_SETTINGS: Record<string, TTSSettings> = {
  natural: {
    length_scale: 1.0,
    volume: 1.0,
    noise_scale: 0.667,
    noise_w: 0.8,
    normalize_audio: true,
  },
  clear: {
    length_scale: 1.2,
    volume: 1.2,
    noise_scale: 0.5,
    noise_w: 0.6,
    normalize_audio: true,
  },
  fast: {
    length_scale: 0.7,
    volume: 1.0,
    noise_scale: 0.8,
    noise_w: 0.9,
    normalize_audio: true,
  },
  slow: {
    length_scale: 1.8,
    volume: 1.2,
    noise_scale: 0.4,
    noise_w: 0.5,
    normalize_audio: true,
  },
  loud: {
    length_scale: 1.0,
    volume: 1.8,
    noise_scale: 0.667,
    noise_w: 0.8,
    normalize_audio: true,
  },
}

interface PresetSelectorProps {
  selected: TTSPreset
  onChange: (preset: TTSPreset, settings: TTSSettings) => void
}

export function PresetSelector({ selected, onChange }: PresetSelectorProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Quick Presets</CardTitle>
        <CardDescription>Pre-configured settings for common needs</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="flex flex-wrap gap-2">
          {PRESETS.map((preset) => (
            <Button
              key={preset.value ?? "custom"}
              variant={selected === preset.value ? "default" : "outline"}
              size="sm"
              onClick={() => {
                if (preset.value && PRESET_SETTINGS[preset.value]) {
                  onChange(preset.value, PRESET_SETTINGS[preset.value])
                } else {
                  onChange(null, {} as TTSSettings)
                }
              }}
            >
              {preset.label}
            </Button>
          ))}
        </div>
      </CardContent>
    </Card>
  )
}
