import { createFileRoute } from '@tanstack/react-router'
import { OCR2Braille } from '@/components/OCR2Braille'

export const Route = createFileRoute('/ocr')({
  component: OCRPage,
})

function OCRPage() {
  return <OCR2Braille />
}
