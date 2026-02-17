import { useState, useEffect, useRef } from 'react'
import { useQuery, useMutation } from '@tanstack/react-query'
import {
  listTablesApiTablesGetOptions,
} from '@/lib/client/@tanstack/react-query.gen'
import type { BrailleTable } from '@/lib/client'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Label } from '@/components/ui/label'
import { Button } from '@/components/ui/button'
import {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectLabel,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Loader2, ImageIcon, Languages } from 'lucide-react'

// PaddleOCR supported languages
const OCR_LANGUAGES = [
  { code: 'en', name: 'English' },
  { code: 'ch', name: 'Chinese' },
  { code: 'fr', name: 'French' },
  { code: 'de', name: 'German' },
  { code: 'ja', name: 'Japanese' },
  { code: 'ko', name: 'Korean' },
  { code: 'es', name: 'Spanish' },
  { code: 'pt', name: 'Portuguese' },
  { code: 'it', name: 'Italian' },
  { code: 'ru', name: 'Russian' },
  { code: 'ar', name: 'Arabic' },
  { code: 'hi', name: 'Hindi' },
  { code: 'id', name: 'Indonesian' },
  { code: 'vi', name: 'Vietnamese' },
]

interface OCRLine {
  text: string
  confidence: number
  bbox: number[][]
}

interface OCRToBrailleResult {
  lines: OCRLine[]
  full_text: string
  braille: string
  language: string
  table_used: string
  success: boolean
}

function getBrailleDots(char: string): number[] {
  const codePoint = char.charCodeAt(0)
  if (codePoint < 0x2800 || codePoint > 0x28ff) return []
  const offset = codePoint - 0x2800
  const dots: number[] = []
  if (offset & 0x01) dots.push(1)
  if (offset & 0x02) dots.push(2)
  if (offset & 0x04) dots.push(3)
  if (offset & 0x08) dots.push(4)
  if (offset & 0x10) dots.push(5)
  if (offset & 0x20) dots.push(6)
  if (offset & 0x40) dots.push(7)
  if (offset & 0x80) dots.push(8)
  return dots
}

function BrailleCharacter({ char }: { char: string }) {
  const activeDots = getBrailleDots(char)
  const isSpace = char === ' ' || char === '\u00A0'

  if (isSpace) {
    return (
      <div className="inline-flex flex-col items-center gap-2 px-2">
        <div className="grid grid-cols-2 gap-x-2.5 gap-y-2">
          {[1, 2, 3].map((row) => (
            <>
              <div
                key={`left-${row}`}
                className="w-3 h-3 rounded-full bg-slate-100 dark:bg-slate-800 opacity-20 border border-slate-300 dark:border-slate-600"
              />
              <div
                key={`right-${row}`}
                className="w-3 h-3 rounded-full bg-slate-100 dark:bg-slate-800 opacity-20 border border-slate-300 dark:border-slate-600"
              />
            </>
          ))}
        </div>
      </div>
    )
  }

  const isDotActive = (dotNumber: number) => activeDots.includes(dotNumber)

  return (
    <div className="inline-flex flex-col items-center gap-2 px-2">
      <div className="grid grid-cols-2 gap-x-2.5 gap-y-2">
        {[
          [1, 4],
          [2, 5],
          [3, 6],
        ].map(([left, right]) => (
          <>
            <div
              key={`dot-${left}`}
              className={`w-3 h-3 rounded-full transition-all ${
                isDotActive(left)
                  ? 'bg-blue-600 dark:bg-blue-500 shadow-md'
                  : 'bg-slate-200 dark:bg-slate-700 opacity-30'
              }`}
              title={`Dot ${left}`}
            />
            <div
              key={`dot-${right}`}
              className={`w-3 h-3 rounded-full transition-all ${
                isDotActive(right)
                  ? 'bg-blue-600 dark:bg-blue-500 shadow-md'
                  : 'bg-slate-200 dark:bg-slate-700 opacity-30'
              }`}
              title={`Dot ${right}`}
            />
          </>
        ))}
      </div>
    </div>
  )
}

export function OCR2Braille() {
  const [selectedTable, setSelectedTable] = useState<string>(() => {
    return localStorage.getItem('speech2braille_table') || 'en-ueb-g2.ctb'
  })
  const [selectedLanguage, setSelectedLanguage] = useState<string>(() => {
    return localStorage.getItem('ocr2braille_language') || 'en'
  })
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [imagePreview, setImagePreview] = useState<string | null>(null)
  const [result, setResult] = useState<OCRToBrailleResult | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const [isDragging, setIsDragging] = useState(false)

  useEffect(() => {
    localStorage.setItem('speech2braille_table', selectedTable)
  }, [selectedTable])

  useEffect(() => {
    localStorage.setItem('ocr2braille_language', selectedLanguage)
  }, [selectedLanguage])

  const { data: tables, isLoading: tablesLoading } = useQuery(listTablesApiTablesGetOptions())

  const ocrMutation = useMutation({
    mutationFn: async ({ file, language, brailleTable }: { file: File; language: string; brailleTable: string }) => {
      const formData = new FormData()
      formData.append('image', file)
      const params = new URLSearchParams()
      params.set('language', language)
      params.set('braille_table', brailleTable)
      const res = await fetch(`http://127.0.0.1:8000/api/ocr-to-braille?${params}`, {
        method: 'POST',
        body: formData,
      })
      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: res.statusText }))
        throw new Error(err.detail || res.statusText)
      }
      return res.json() as Promise<OCRToBrailleResult>
    },
    onSuccess: (data) => {
      setResult(data)
    },
  })

  const handleFileSelect = (file: File) => {
    setSelectedFile(file)
    setResult(null)
    const reader = new FileReader()
    reader.onload = (e) => setImagePreview(e.target?.result as string)
    reader.readAsDataURL(file)
  }

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) handleFileSelect(file)
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
    const file = e.dataTransfer.files[0]
    if (file) handleFileSelect(file)
  }

  const handleSubmit = () => {
    if (selectedFile) {
      ocrMutation.mutate({
        file: selectedFile,
        language: selectedLanguage,
        brailleTable: selectedTable,
      })
    }
  }

  const groupedTables = tables?.reduce(
    (acc, table) => {
      const lang = table.language || 'other'
      if (!acc[lang]) acc[lang] = []
      acc[lang].push(table)
      return acc
    },
    {} as Record<string, BrailleTable[]>,
  )

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Settings Card */}
      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <Languages className="w-5 h-5" />
            <CardTitle>OCR Settings</CardTitle>
          </div>
          <CardDescription>
            Configure OCR language and braille output table
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="ocr-language">OCR Language</Label>
              <Select value={selectedLanguage} onValueChange={setSelectedLanguage}>
                <SelectTrigger id="ocr-language">
                  <SelectValue placeholder="Select language" />
                </SelectTrigger>
                <SelectContent>
                  {OCR_LANGUAGES.map((lang) => (
                    <SelectItem key={lang.code} value={lang.code}>
                      {lang.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label htmlFor="braille-table">Braille Table</Label>
              {tablesLoading ? (
                <div className="flex items-center gap-2 text-sm text-slate-500">
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Loading tables...
                </div>
              ) : (
                <Select value={selectedTable} onValueChange={setSelectedTable}>
                  <SelectTrigger id="braille-table">
                    <SelectValue placeholder="Select a braille table" />
                  </SelectTrigger>
                  <SelectContent>
                    {Object.entries(groupedTables || {})
                      .sort(([a], [b]) => a.localeCompare(b))
                      .map(([language, languageTables]) => (
                        <SelectGroup key={language}>
                          <SelectLabel className="capitalize">{language}</SelectLabel>
                          {languageTables.map((table) => (
                            <SelectItem key={table.filename} value={table.filename}>
                              {table.display_name}
                              {table.grade && ` (${table.grade.toUpperCase()})`}
                            </SelectItem>
                          ))}
                        </SelectGroup>
                      ))}
                  </SelectContent>
                </Select>
              )}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Upload Card */}
      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <ImageIcon className="w-5 h-5" />
            <CardTitle>Image Upload</CardTitle>
          </div>
          <CardDescription>
            Upload an image containing text to recognize and convert to braille
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Drop zone */}
          <div
            className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors cursor-pointer ${
              isDragging
                ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                : 'border-slate-300 dark:border-slate-600 hover:border-slate-400 dark:hover:border-slate-500'
            }`}
            onClick={() => fileInputRef.current?.click()}
            onDragOver={(e) => {
              e.preventDefault()
              setIsDragging(true)
            }}
            onDragLeave={() => setIsDragging(false)}
            onDrop={handleDrop}
          >
            <input
              ref={fileInputRef}
              type="file"
              accept="image/png,image/jpeg,image/bmp,image/tiff,image/webp"
              onChange={handleInputChange}
              className="hidden"
            />
            {imagePreview ? (
              <div className="space-y-4">
                <img
                  src={imagePreview}
                  alt="Preview"
                  className="max-h-64 mx-auto rounded-lg shadow-md"
                />
                <p className="text-sm text-slate-500">{selectedFile?.name}</p>
                <p className="text-xs text-slate-400">Click or drag to replace</p>
              </div>
            ) : (
              <div className="space-y-2">
                <ImageIcon className="w-12 h-12 mx-auto text-slate-400" />
                <p className="text-slate-600 dark:text-slate-400">
                  Drag and drop an image here, or click to browse
                </p>
                <p className="text-xs text-slate-400">
                  Supports PNG, JPG, BMP, TIFF, WebP
                </p>
              </div>
            )}
          </div>

          {/* Submit button */}
          <Button
            onClick={handleSubmit}
            disabled={!selectedFile || ocrMutation.isPending}
            className="w-full"
            size="lg"
          >
            {ocrMutation.isPending ? (
              <>
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                Processing...
              </>
            ) : (
              'Recognize & Convert to Braille'
            )}
          </Button>

          {/* Error */}
          {ocrMutation.isError && (
            <div className="p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
              <p className="text-sm text-red-600 dark:text-red-400">
                <strong>Error:</strong> {String(ocrMutation.error?.message || ocrMutation.error)}
              </p>
            </div>
          )}

          {/* Results */}
          {result && (
            <div className="space-y-4 pt-4 border-t">
              {/* Recognized text lines */}
              <div className="space-y-2">
                <Label>Recognized Text Lines</Label>
                <div className="space-y-1">
                  {result.lines.map((line, i) => (
                    <div
                      key={i}
                      className="flex items-center justify-between p-2 bg-slate-50 dark:bg-slate-800 rounded text-sm"
                    >
                      <span className="font-mono">{line.text}</span>
                      <span
                        className={`text-xs px-2 py-0.5 rounded-full ${
                          line.confidence >= 0.9
                            ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400'
                            : line.confidence >= 0.7
                              ? 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400'
                              : 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400'
                        }`}
                      >
                        {(line.confidence * 100).toFixed(1)}%
                      </span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Full text */}
              <div className="space-y-2">
                <Label>Full Text</Label>
                <div className="p-3 bg-slate-50 dark:bg-slate-800 rounded-lg font-mono text-sm whitespace-pre-wrap">
                  {result.full_text}
                </div>
              </div>

              {/* Braille output */}
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <Label>Visual Braille Output</Label>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => navigator.clipboard.writeText(result.braille)}
                  >
                    Copy Unicode
                  </Button>
                </div>
                <div className="p-6 bg-white dark:bg-slate-950 border-2 border-slate-300 dark:border-slate-600 rounded-lg shadow-inner overflow-x-auto">
                  <div className="flex flex-wrap gap-x-3 gap-y-4 leading-loose">
                    {result.braille.split('').map((char, index) => (
                      <BrailleCharacter key={index} char={char} />
                    ))}
                  </div>
                </div>
                <div className="flex items-center justify-between text-xs text-slate-500">
                  <div className="flex items-center gap-2">
                    <div className="w-2 h-2 bg-blue-500 rounded-full" />
                    <span>Active dots shown in blue, inactive dots faded</span>
                  </div>
                  <span className="text-slate-400">Unicode Braille (U+2800-U+28FF)</span>
                </div>
              </div>

              {/* Metadata */}
              <div className="grid grid-cols-3 gap-4 text-sm">
                <div className="space-y-1">
                  <p className="text-slate-500 dark:text-slate-400 text-xs font-medium">Table Used</p>
                  <p className="font-mono text-xs bg-slate-100 dark:bg-slate-800 px-2 py-1 rounded">
                    {result.table_used}
                  </p>
                </div>
                <div className="space-y-1">
                  <p className="text-slate-500 dark:text-slate-400 text-xs font-medium">Characters</p>
                  <p className="font-mono text-xs bg-slate-100 dark:bg-slate-800 px-2 py-1 rounded">
                    {result.braille.length}
                  </p>
                </div>
                <div className="space-y-1">
                  <p className="text-slate-500 dark:text-slate-400 text-xs font-medium">OCR Language</p>
                  <p className="font-mono text-xs bg-slate-100 dark:bg-slate-800 px-2 py-1 rounded">
                    {OCR_LANGUAGES.find((l) => l.code === result.language)?.name || result.language}
                  </p>
                </div>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Info Card */}
      <Card className="bg-blue-50 dark:bg-blue-900/20 border-blue-200 dark:border-blue-800">
        <CardContent className="pt-6">
          <p className="text-sm text-blue-900 dark:text-blue-100">
            <strong>Note:</strong> This pipeline uses PaddleOCR PP-OCRv5 for text recognition and
            liblouis for braille translation. Upload a photo of printed text to get braille output
            suitable for refreshable braille displays.
          </p>
        </CardContent>
      </Card>
    </div>
  )
}
