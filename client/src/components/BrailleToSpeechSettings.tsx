import { Label } from "@/components/ui/label"
import { Slider } from "@/components/ui/slider"
import { Switch } from "@/components/ui/switch"
import { Separator } from "@/components/ui/separator"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { RefreshCw } from "lucide-react"

export interface TTSSettings {
  length_scale: number
  volume: number
  noise_scale: number
  noise_w: number
  normalize_audio: boolean
}

const DEFAULT_SETTINGS: TTSSettings = {
  length_scale: 1.0,
  volume: 1.0,
  noise_scale: 0.667,
  noise_w: 0.8,
  normalize_audio: true,
}

interface BrailleToSpeechSettingsProps {
  settings: TTSSettings
  onChange: (settings: TTSSettings) => void
  showAdvanced?: boolean
  onToggleAdvanced?: () => void
}

export function BrailleToSpeechSettings({
  settings,
  onChange,
  showAdvanced = false,
  onToggleAdvanced,
}: BrailleToSpeechSettingsProps) {
  const updateSetting = <K extends keyof TTSSettings>(key: K, value: TTSSettings[K]) => {
    onChange({ ...settings, [key]: value })
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle>Speech Settings</CardTitle>
            <CardDescription>Customize how your braille text sounds</CardDescription>
          </div>
          <Button variant="ghost" size="sm" onClick={() => onChange(DEFAULT_SETTINGS)}>
            <RefreshCw className="h-4 w-4 mr-2" />
            Reset
          </Button>
        </div>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Speech Speed */}
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <Label htmlFor="speed-slider">Speech Speed</Label>
            <span className="text-sm text-muted-foreground">{settings.length_scale.toFixed(1)}x</span>
          </div>
          <Slider
            id="speed-slider"
            min={0.5}
            max={2.0}
            step={0.1}
            value={[settings.length_scale]}
            onValueChange={([value]) => updateSetting("length_scale", value)}
          />
        </div>

        {/* Volume */}
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <Label htmlFor="volume-slider">Volume</Label>
            <span className="text-sm text-muted-foreground">{Math.round(settings.volume * 100)}%</span>
          </div>
          <Slider
            id="volume-slider"
            min={0}
            max={200}
            step={10}
            value={[settings.volume * 100]}
            onValueChange={([value]) => updateSetting("volume", value / 100)}
          />
        </div>

        {/* Normalize Audio */}
        <div className="flex items-center justify-between">
          <div className="space-y-0.5">
            <Label htmlFor="normalize-switch">Normalize Audio</Label>
            <p className="text-xs text-muted-foreground">Keep consistent volume</p>
          </div>
          <Switch
            id="normalize-switch"
            checked={settings.normalize_audio}
            onCheckedChange={(checked) => updateSetting("normalize_audio", checked)}
          />
        </div>

        {onToggleAdvanced && (
          <>
            <Separator />
            <Button variant="outline" className="w-full" onClick={onToggleAdvanced}>
              {showAdvanced ? "Hide" : "Show"} Advanced Settings
            </Button>
          </>
        )}

        {showAdvanced && (
          <div className="space-y-6 pt-4">
            <Separator />
            {/* Speech Clarity (noise_scale) */}
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <Label htmlFor="clarity-slider">Speech Clarity</Label>
                <span className="text-sm text-muted-foreground">
                  {settings.noise_scale < 0.5 ? "Clear" : settings.noise_scale > 1.0 ? "Natural" : "Balanced"}
                </span>
              </div>
              <Slider
                id="clarity-slider"
                min={0}
                max={1.5}
                step={0.1}
                value={[settings.noise_scale]}
                onValueChange={([value]) => updateSetting("noise_scale", value)}
              />
            </div>

            {/* Phoneme Variation (noise_w) */}
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <Label htmlFor="phoneme-slider">Phoneme Variation</Label>
                <span className="text-sm text-muted-foreground">
                  {settings.noise_w < 0.5 ? "Steady" : settings.noise_w > 1.0 ? "Expressive" : "Balanced"}
                </span>
              </div>
              <Slider
                id="phoneme-slider"
                min={0}
                max={1.5}
                step={0.1}
                value={[settings.noise_w]}
                onValueChange={([value]) => updateSetting("noise_w", value)}
              />
            </div>

          </div>
        )}
      </CardContent>
    </Card>
  )
}
