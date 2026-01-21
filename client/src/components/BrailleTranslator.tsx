import { useState, useEffect } from 'react'
import { useQuery, useMutation } from '@tanstack/react-query'
import {
  listTablesApiTablesGetOptions,
  translateToBrailleApiTranslatePostMutation,
} from '@/lib/client/@tanstack/react-query.gen'
import type { BrailleTable, TranslationResponse } from '@/lib/client'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
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
import { Loader2, Languages, Type } from 'lucide-react'

// Function to convert braille Unicode to dot pattern
function getBrailleDots(char: string): number[] {
  const codePoint = char.charCodeAt(0)
  if (codePoint < 0x2800 || codePoint > 0x28ff) return []

  const offset = codePoint - 0x2800
  const dots: number[] = []

  // Braille Unicode encoding uses bits 0-7 for dots 1-8
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

// Component to display a single braille character with visual dot representation
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
                title={`Dot ${row} (space)`}
              />
              <div
                key={`right-${row}`}
                className="w-3 h-3 rounded-full bg-slate-100 dark:bg-slate-800 opacity-20 border border-slate-300 dark:border-slate-600"
                title={`Dot ${row + 3} (space)`}
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
      {/* Visual 6-dot cell representation */}
      <div className="grid grid-cols-2 gap-x-2.5 gap-y-2">
        {/* Left column: dots 1, 2, 3 */}
        <div
          className={`w-3 h-3 rounded-full transition-all ${
            isDotActive(1)
              ? 'bg-blue-600 dark:bg-blue-500 shadow-md'
              : 'bg-slate-200 dark:bg-slate-700 opacity-30'
          }`}
          title="Dot 1"
        />
        {/* Right column: dots 4, 5, 6 */}
        <div
          className={`w-3 h-3 rounded-full transition-all ${
            isDotActive(4)
              ? 'bg-blue-600 dark:bg-blue-500 shadow-md'
              : 'bg-slate-200 dark:bg-slate-700 opacity-30'
          }`}
          title="Dot 4"
        />

        <div
          className={`w-3 h-3 rounded-full transition-all ${
            isDotActive(2)
              ? 'bg-blue-600 dark:bg-blue-500 shadow-md'
              : 'bg-slate-200 dark:bg-slate-700 opacity-30'
          }`}
          title="Dot 2"
        />
        <div
          className={`w-3 h-3 rounded-full transition-all ${
            isDotActive(5)
              ? 'bg-blue-600 dark:bg-blue-500 shadow-md'
              : 'bg-slate-200 dark:bg-slate-700 opacity-30'
          }`}
          title="Dot 5"
        />

        <div
          className={`w-3 h-3 rounded-full transition-all ${
            isDotActive(3)
              ? 'bg-blue-600 dark:bg-blue-500 shadow-md'
              : 'bg-slate-200 dark:bg-slate-700 opacity-30'
          }`}
          title="Dot 3"
        />
        <div
          className={`w-3 h-3 rounded-full transition-all ${
            isDotActive(6)
              ? 'bg-blue-600 dark:bg-blue-500 shadow-md'
              : 'bg-slate-200 dark:bg-slate-700 opacity-30'
          }`}
          title="Dot 6"
        />
      </div>
    </div>
  )
}

export function BrailleTranslator() {
  const [selectedTable, setSelectedTable] = useState<string>(() => {
    return localStorage.getItem('speech2braille_table') || 'en-ueb-g2.ctb'
  })
  const [inputText, setInputText] = useState<string>('')
  const [translation, setTranslation] = useState<TranslationResponse | null>(null)

  // Persist selected table to localStorage
  useEffect(() => {
    localStorage.setItem('speech2braille_table', selectedTable)
  }, [selectedTable])

  // Fetch available braille tables using generated query options
  const { data: tables, isLoading: tablesLoading } = useQuery(listTablesApiTablesGetOptions())

  // Translation mutation using generated mutation
  const translateMutation = useMutation({
    ...translateToBrailleApiTranslatePostMutation(),
    onSuccess: (data) => {
      setTranslation(data)
    },
  })

  const handleTranslate = () => {
    if (inputText.trim()) {
      translateMutation.mutate({
        body: {
          text: inputText,
          table: selectedTable,
        },
      })
    }
  }

  // Group tables by language
  const groupedTables = tables?.reduce(
    (acc, table) => {
      const lang = table.language || 'other'
      if (!acc[lang]) {
        acc[lang] = []
      }
      acc[lang].push(table)
      return acc
    },
    {} as Record<string, BrailleTable[]>,
  )

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Language Selection Card */}
      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <Languages className="w-5 h-5" />
            <CardTitle>Language Selection</CardTitle>
          </div>
          <CardDescription>
            Choose the braille translation table for your preferred language and grade
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            <Label htmlFor="table-select">Braille Table</Label>
            {tablesLoading ? (
              <div className="flex items-center gap-2 text-sm text-slate-500">
                <Loader2 className="w-4 h-4 animate-spin" />
                Loading available tables...
              </div>
            ) : (
              <Select value={selectedTable} onValueChange={setSelectedTable}>
                <SelectTrigger id="table-select" className="w-full">
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
            <p className="text-xs text-slate-500">
              {tables?.length || 0} translation tables available
            </p>
          </div>
        </CardContent>
      </Card>

      {/* Translation Card */}
      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <Type className="w-5 h-5" />
            <CardTitle>Text to Braille Translation</CardTitle>
          </div>
          <CardDescription>
            Enter text below to translate it to braille using the selected table
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Input Text */}
          <div className="space-y-2">
            <Label htmlFor="input-text">Input Text</Label>
            <Textarea
              id="input-text"
              placeholder="Type or paste text here to translate to braille..."
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              rows={4}
              className="resize-none font-mono"
            />
          </div>

          {/* Translate Button */}
          <Button
            onClick={handleTranslate}
            disabled={!inputText.trim() || translateMutation.isPending}
            className="w-full"
            size="lg"
          >
            {translateMutation.isPending ? (
              <>
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                Translating...
              </>
            ) : (
              'Translate to Braille'
            )}
          </Button>

          {/* Error Display */}
          {translateMutation.isError && (
            <div className="p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
              <p className="text-sm text-red-600 dark:text-red-400">
                <strong>Error:</strong> {String(translateMutation.error)}
              </p>
            </div>
          )}

          {/* Translation Result */}
          {translation && (
            <div className="space-y-4 pt-4 border-t">
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <Label htmlFor="braille-output">Visual Braille Output</Label>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => {
                      navigator.clipboard.writeText(translation.braille)
                    }}
                  >
                    Copy Unicode
                  </Button>
                </div>
                <div
                  id="braille-output"
                  className="p-6 bg-white dark:bg-slate-950 border-2 border-slate-300 dark:border-slate-600 rounded-lg shadow-inner overflow-x-auto"
                >
                  <div className="flex flex-wrap gap-x-3 gap-y-4 leading-loose">
                    {translation.braille.split('').map((char, index) => (
                      <BrailleCharacter key={index} char={char} />
                    ))}
                  </div>
                </div>
                <div className="flex items-center justify-between text-xs text-slate-500">
                  <div className="flex items-center gap-2">
                    <div className="w-2 h-2 bg-blue-500 rounded-full" />
                    <span>Active dots shown in blue, inactive dots faded</span>
                  </div>
                  <span className="text-slate-400">Unicode Braille (U+2800–U+28FF)</span>
                </div>
              </div>

              <div className="grid grid-cols-3 gap-4 text-sm">
                <div className="space-y-1">
                  <p className="text-slate-500 dark:text-slate-400 text-xs font-medium">Table Used</p>
                  <p className="font-mono text-xs bg-slate-100 dark:bg-slate-800 px-2 py-1 rounded">
                    {translation.table_used}
                  </p>
                </div>
                <div className="space-y-1">
                  <p className="text-slate-500 dark:text-slate-400 text-xs font-medium">Characters</p>
                  <p className="font-mono text-xs bg-slate-100 dark:bg-slate-800 px-2 py-1 rounded">
                    {translation.braille.length}
                  </p>
                </div>
                <div className="space-y-1">
                  <p className="text-slate-500 dark:text-slate-400 text-xs font-medium">Original Length</p>
                  <p className="font-mono text-xs bg-slate-100 dark:bg-slate-800 px-2 py-1 rounded">
                    {translation.original_text.length}
                  </p>
                </div>
              </div>

              {/* Visual comparison */}
              <div className="p-4 bg-blue-50 dark:bg-blue-900/10 border border-blue-200 dark:border-blue-800 rounded-lg">
                <div className="space-y-2">
                  <p className="text-xs font-medium text-blue-900 dark:text-blue-100">
                    Original Text:
                  </p>
                  <p className="text-sm text-blue-800 dark:text-blue-200 font-mono break-words">
                    "{translation.original_text}"
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
            <strong>Note:</strong> This system works completely offline using liblouis for
            high-quality braille translation. The Unicode braille characters displayed above can be
            sent to a refreshable braille display or copied for use in other applications.
          </p>
        </CardContent>
      </Card>
    </div>
  )
}
