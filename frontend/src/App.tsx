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
  const [taskId, setTaskId] = useState<string | null>(null)
  const [polling, setPolling] = useState(false)

  // Polling function to check task status
  async function pollTaskStatus(id: string) {
    setPolling(true)
    let attempts = 0
    const maxAttempts = 60 // Poll for up to 5 minutes (5s interval)
    
    const poll = async () => {
      try {
        const res = await fetch(`/parse/task/${id}`)
        if (!res.ok) {
          throw new Error(`Failed to check task status: ${res.status}`)
        }
        
        const taskData = await res.json()
        
        if (taskData.status === 'completed' && taskData.result) {
          setResult(taskData.result)
          setLoading(false)
          setPolling(false)
          setTaskId(null)
          return
        } else if (taskData.status === 'failed') {
          setError(`Parsing failed: ${taskData.error}`)
          setLoading(false)
          setPolling(false)
          setTaskId(null)
          return
        } else if (taskData.status === 'processing') {
          // Update result with progress info
          setResult({
            status: 'processing',
            task_id: id,
            message: `Parsing in corso... (${taskData.elapsed_seconds || 0}s trascorsi)`,
            estimated_remaining: taskData.estimated_remaining || 180,
            filename: taskData.filename
          })
          
          attempts++
          if (attempts < maxAttempts) {
            setTimeout(poll, 5000) // Poll every 5 seconds
          } else {
            setError('Timeout: il parsing sta impiegando troppo tempo')
            setLoading(false)
            setPolling(false)
            setTaskId(null)
          }
        }
      } catch (err) {
        console.error('Polling error:', err)
        attempts++
        if (attempts < maxAttempts) {
          setTimeout(poll, 5000)
        } else {
          setError('Errore nel controllo dello stato del task')
          setLoading(false)
          setPolling(false)
          setTaskId(null)
        }
      }
    }
    
    poll()
  }

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
      // Use background=true for async parsing (default behavior)
      const res = await fetch('/parse/upload?background=true', {
        method: 'POST',
        body: fd
      })

      if (!res.ok) {
        const txt = await res.text()
        throw new Error(txt || `HTTP ${res.status}`)
      }

      const data = await res.json()
      
      if (data.task_id) {
        // Background parsing started - start polling
        setTaskId(data.task_id)
        setResult({
          status: 'parsing',
          task_id: data.task_id,
          message: 'Parsing avviato in background. Monitoraggio automatico in corso...',
          timestamp: new Date().toISOString()
        })
        // Start polling for results
        pollTaskStatus(data.task_id)
      } else {
        // Synchronous response (fallback)
        setResult(data.parsed || data)
        setLoading(false)
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err)
      setError(msg || 'Errore durante upload')
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 text-gray-900">
      <div className="max-w-6xl mx-auto p-6">
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-indigo-900 mb-2">🚀 PiazzaTi</h1>
          <p className="text-lg text-indigo-600">Intelligent CV Parser with AI</p>
        </div>
        
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          <section className="bg-white p-6 rounded-xl shadow-lg border border-gray-200">
            <div className="flex items-center mb-4">
              <div className="w-8 h-8 bg-indigo-100 rounded-full flex items-center justify-center mr-3">
                <span className="text-indigo-600 font-semibold">📤</span>
              </div>
              <h2 className="text-xl font-semibold text-gray-800">Upload CV</h2>
            </div>
            <form onSubmit={handleUpload}>
              <div className="space-y-4">
                <label className="block">
                  <span className="text-sm font-medium text-gray-700 mb-2 block">👤 User ID (opzionale)</span>
                  <input
                    type="text"
                    value={userId}
                    onChange={(e) => setUserId(e.target.value)}
                    placeholder="USER_0016"
                    className="w-full border border-gray-300 rounded-lg px-4 py-2 focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-colors"
                  />
                </label>

                <fieldset className="border border-gray-200 rounded-lg p-4">
                  <legend className="text-sm font-medium text-gray-700 px-2">🏷️ Tags (opzionali)</legend>
                  <div className="flex gap-4 mt-3 flex-wrap">
                    {Object.keys(tags).map((key) => (
                      <label key={key} className="inline-flex items-center text-sm">
                        <input
                          type="checkbox"
                          checked={!!tags[key]}
                          onChange={(e) => setTags({ ...tags, [key]: e.target.checked })}
                          className="rounded border-gray-300 text-indigo-600 focus:ring-indigo-500 mr-2"
                        />
                        <span className="text-gray-600">{key.replace(/_/g, ' ')}</span>
                      </label>
                    ))}
                  </div>
                </fieldset>

                <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center hover:border-indigo-400 transition-colors">
                  <input
                    type="file"
                    accept="application/pdf"
                    onChange={(e) => setFile(e.target.files?.[0] ?? null)}
                    className="hidden"
                    id="file-upload"
                  />
                  <label htmlFor="file-upload" className="cursor-pointer">
                    <div className="text-gray-400 mb-2">
                      <svg className="w-12 h-12 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                      </svg>
                    </div>
                    <p className="text-sm text-gray-600 mb-1">
                      {file ? `📄 ${file.name}` : '📎 Clicca per selezionare un PDF'}
                    </p>
                    <p className="text-xs text-gray-400">Supporto solo file PDF</p>
                  </label>
                </div>

                <button
                  type="submit"
                  disabled={loading || !file}
                  className="w-full bg-gradient-to-r from-indigo-600 to-purple-600 text-white py-3 px-6 rounded-lg font-semibold 
                           disabled:opacity-50 disabled:cursor-not-allowed hover:from-indigo-700 hover:to-purple-700 
                           transform hover:scale-105 transition-all duration-200 shadow-lg"
                >
                  {loading ? (
                    <span className="flex items-center justify-center">
                      <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-2"></div>
                      Parsing in corso...
                    </span>
                  ) : (
                    <span className="flex items-center justify-center">
                      🚀 Upload & Parse CV
                    </span>
                  )}
                </button>
              </div>

              {error && (
                <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-lg">
                  <p className="text-red-700 text-sm flex items-center">
                    <span className="mr-2">❌</span>
                    {error}
                  </p>
                </div>
              )}
            </form>

            <div className="mt-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
              <h3 className="text-sm font-medium text-blue-800 mb-2">💡 Come funziona</h3>
              <ul className="text-xs text-blue-600 space-y-1">
                <li>• Il parsing avviene in <strong>background</strong> per evitare timeout</li>
                <li>• Utilizziamo <strong>Ollama + LLM</strong> per un parsing intelligente</li>
                <li>• Tempo stimato: <strong>2-3 minuti</strong> per CV complessi</li>
              </ul>
            </div>
          </section>

          <section className="bg-white p-6 rounded-xl shadow-lg border border-gray-200">
            <div className="flex items-center mb-4">
              <div className="w-8 h-8 bg-green-100 rounded-full flex items-center justify-center mr-3">
                <span className="text-green-600 font-semibold">📊</span>
              </div>
              <h2 className="text-xl font-semibold text-gray-800">Risultati Parsing</h2>
            </div>
            
            {loading && !polling && (
              <div className="flex items-center justify-center p-8 text-indigo-600">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600 mr-3"></div>
                <span className="text-lg font-medium">Avvio parsing...</span>
              </div>
            )}
            
            {!loading && !result && (
              <div className="text-center p-8 text-gray-500">
                <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-3">
                  <span className="text-2xl">📄</span>
                </div>
                <p className="text-sm">Carica un CV per iniziare il parsing</p>
              </div>
            )}
            
            {result?.status === 'processing' && (
              <div className="p-6 bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-200 rounded-xl">
                <div className="flex items-center mb-4">
                  <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600 mr-3"></div>
                  <span className="font-semibold text-blue-900 text-lg">Parsing in corso...</span>
                </div>
                
                <div className="space-y-3">
                  <p className="text-blue-700">{result.message}</p>
                  
                  {result.filename && (
                    <div className="flex items-center text-sm text-blue-600">
                      <span className="mr-2">📄</span>
                      <span className="font-medium">{result.filename}</span>
                    </div>
                  )}
                  
                  {taskId && (
                    <div className="flex items-center text-xs text-blue-500">
                      <span className="mr-2">🔄</span>
                      <span>Task ID: {taskId}</span>
                    </div>
                  )}
                  
                  {result.estimated_remaining && (
                    <div className="flex items-center justify-between p-3 bg-white rounded-lg border">
                      <div className="flex items-center text-sm text-indigo-700">
                        <span className="mr-2">⏱️</span>
                        <span>Tempo rimanente: ~{Math.round(result.estimated_remaining)}s</span>
                      </div>
                      <div className="text-xs text-gray-500">
                        {result.elapsed_seconds && `${result.elapsed_seconds}s trascorsi`}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            )}

            {result && result.status !== 'processing' && (
              <div className="space-y-4">
                <div className="flex items-center justify-between p-3 bg-green-50 border border-green-200 rounded-lg">
                  <div className="flex items-center text-green-800">
                    <span className="mr-2">✅</span>
                    <span className="font-medium">Parsing completato!</span>
                  </div>
                  <button 
                    onClick={() => {
                      setResult(null)
                      setTaskId(null)
                      setFile(null)
                      setError(null)
                    }}
                    className="text-xs text-green-600 hover:text-green-800 underline"
                  >
                    Nuovo parsing
                  </button>
                </div>
                
                <div className="bg-gray-50 rounded-lg overflow-hidden">
                  <div className="bg-gray-200 px-4 py-2 text-sm font-medium text-gray-700 flex items-center justify-between">
                    <span>📋 Dati estratti (JSON)</span>
                    <button 
                      onClick={() => navigator.clipboard.writeText(JSON.stringify(result, null, 2))}
                      className="text-xs text-gray-600 hover:text-gray-800 underline"
                    >
                      Copia
                    </button>
                  </div>
                  <div className="overflow-auto max-h-[50vh] p-4">
                    <pre className="text-xs text-gray-800 whitespace-pre-wrap">
                      {JSON.stringify(result, null, 2)}
                    </pre>
                  </div>
                </div>
              </div>
            )}
          </section>
        </div>
      </div>
    </div>
  )
}
