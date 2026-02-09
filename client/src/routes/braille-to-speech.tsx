import { createFileRoute } from '@tanstack/react-router'
import { BrailleToSpeech } from '@/components/BrailleToSpeech'

export const Route = createFileRoute('/braille-to-speech')({
  component: BrailleToSpeechPage,
})

function BrailleToSpeechPage() {
  return <BrailleToSpeech />
}
