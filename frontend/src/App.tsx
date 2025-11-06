import React, { useState } from 'react'

// The parsed document shape comes from the backend and can be arbitrary.
// Use `any` here for flexibility; disable the explicit-any lint rule for this alias.
// eslint-disable-next-line @typescript-eslint/no-explicit-any
type ParsedDocument = any


export default function App() {
  const [file, setFile] = useState<File | null>(null)
  const [userId, setUserId] = useState<string>('')
  const [tags, setTags] = useState<Record<string, boolean>>({
    women_in_tech: false,
    '1_2_generation': false,
    open_to_relocation: false,
  })
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<ParsedDocument | null>(null)
  const [error, setError] = useState<string | null>(null)

  async function handleUpload(e: React.FormEvent) {
    e.preventDefault()
    setError(null)
    if (!file) {
      setError('Seleziona un file prima di inviare')
      return
    }

  const fd = new FormData()
  fd.append('file', file)
  if (userId) fd.append('user_id', userId)
  // Append tags as a JSON string so backend can parse them if desired
  fd.append('Tags', JSON.stringify(tags))

    setLoading(true)
    setResult(null)

    try {
      // Assumiamo che il backend esponga l'endpoint /api/parse
      // Call the backend upload endpoint. Use background=false to request synchronous parse
      const res = await fetch('/api/parse/upload?background=false', {
        method: 'POST',
        body: fd
      })

      if (!res.ok) {
        const txt = await res.text()
        throw new Error(txt || `HTTP ${res.status}`)
      }

      const data = await res.json()
      // il backend potrebbe restituire { parsed: {...} } o direttamente l'oggetto
      setResult(data.parsed || data)
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err)
      setError(msg || 'Errore durante upload')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gray-100 text-gray-900">
      <div className="max-w-6xl mx-auto p-6">
        <h1 className="text-2xl font-bold mb-4">PiazzaTi — Parser UI</h1>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <section className="bg-white p-4 rounded shadow">
            <h2 className="font-semibold mb-2">Upload CV</h2>
            <form onSubmit={handleUpload}>
              <label className="block mb-2 text-sm">
                User ID (opzionale)
                <input
                  type="text"
                  value={userId}
                  onChange={(e) => setUserId(e.target.value)}
                  placeholder="USER_0016"
                  className="mt-1 block w-full border rounded px-2 py-1"
                />
              </label>

              <fieldset className="mb-3">
                <legend className="text-sm font-medium">Tags (opzionali)</legend>
                <div className="flex gap-3 mt-2 flex-wrap">
                  {Object.keys(tags).map((key) => (
                    <label key={key} className="inline-flex items-center text-sm mr-3">
                      <input
                        type="checkbox"
                        checked={!!tags[key]}
                        onChange={(e) => setTags({ ...tags, [key]: e.target.checked })}
                        className="mr-2"
                      />
                      {key}
                    </label>
                  ))}
                </div>
              </fieldset>

              <input
                type="file"
                accept="application/pdf"
                onChange={(e) => setFile(e.target.files?.[0] ?? null)}
                className="mb-3"
              />

              <div className="flex items-center gap-2">
                <button
                  type="submit"
                  disabled={loading}
                  className="px-3 py-2 bg-indigo-600 text-white rounded disabled:opacity-50"
                >
                  {loading ? 'Parsing...' : 'Upload & Parse'}
                </button>
                <span className="text-sm text-gray-500">{file?.name}</span>
              </div>
              {error && <p className="text-red-600 mt-2">{error}</p>}
            </form>

            <div className="mt-4 text-sm text-gray-600">
              <p>
                Il parser è lato backend. Questo form invia il PDF a <code>/api/parse</code>.
              </p>
              <p>
                Se stai sviluppando localmente con Vite, configura un proxy in <code>vite.config.ts</code>
                verso <code>http://localhost:8000</code>.
              </p>
            </div>
          </section>

          <section className="bg-white p-4 rounded shadow">
            <h2 className="font-semibold mb-2">Parsed Result</h2>
            {loading && <div>Parsing in corso…</div>}
            {!loading && !result && <div className="text-sm text-gray-500">Nessun risultato</div>}

            {result && (
              <div className="overflow-auto max-h-[60vh] text-xs">
                <pre className="whitespace-pre-wrap">{JSON.stringify(result, null, 2)}</pre>
              </div>
            )}
          </section>
        </div>
      </div>
    </div>
  )
}
