import { createFileRoute } from '@tanstack/react-router'
import { SpeechToBraille } from '@/components/SpeechToBraille'

export const Route = createFileRoute('/speech')({
  component: SpeechPage,
})

function SpeechPage() {
  return <SpeechToBraille />
}
