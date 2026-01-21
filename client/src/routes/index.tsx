import { createFileRoute } from '@tanstack/react-router'
import { BrailleTranslator } from '@/components/BrailleTranslator'

export const Route = createFileRoute('/')({
  component: Index,
})

function Index() {
  return <BrailleTranslator />
}
