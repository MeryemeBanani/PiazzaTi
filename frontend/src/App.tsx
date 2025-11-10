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
        console.log(`🔍 Checking task status for: ${id} (attempt ${attempts + 1}/${maxAttempts})`)
        console.log(`🌐 Full URL: ${window.location.origin}/parse/task/${id}`)
        const res = await fetch(`/parse/task/${id}`)
        console.log(`📡 Response status: ${res.status} ${res.statusText}`)
        if (!res.ok) {
          const errorText = await res.text()
          console.error(`❌ Task check failed: ${res.status} - ${errorText}`)
          throw new Error(`Failed to check task status: ${res.status} - ${errorText}`)
        }
        
        const taskData = await res.json()
        console.log(`📊 Full task data:`, JSON.stringify(taskData, null, 2))
        
        if (taskData.status === 'completed' && taskData.result) {
          console.log('✅ Parsing completed! ParsedDocument received:', taskData.result)
          setResult(taskData.result)  // This is the ParsedDocument from ollama_cv_parser
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
        } else if (taskData.status === 'processing' || taskData.status === 'parsing') {
          // Update result with progress info
          console.log('📊 Progress update:', taskData)
          setResult({
            status: 'processing',
            task_id: id,
            message: `Parsing in corso... (${taskData.elapsed_seconds || 0}s trascorsi)`,
            estimated_remaining: taskData.estimated_remaining || 180,
            elapsed_seconds: taskData.elapsed_seconds || 0,
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
          <h1 className="text-4xl font-bold text-indigo-900 mb-2">🚀 PiazzaTi CV Parser</h1>
          <p className="text-lg text-indigo-600">Intelligent CV Parser with AI</p>
          <div className="mt-4">
            <a 
              href="/home" 
              className="inline-flex items-center text-sm text-indigo-600 hover:text-indigo-800 underline"
            >
              ← Torna alla Home
            </a>
          </div>
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
                    <p className="text-sm text-gray-600 mb-1 py-8">
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
                
                <div className="space-y-4">
                  <p className="text-blue-700">{result.message}</p>
                  
                  {result.filename && (
                    <div className="flex items-center text-sm text-blue-600">
                      <span className="mr-2">📄</span>
                      <span className="font-medium">{result.filename}</span>
                    </div>
                  )}
                  
                  {/* Progress Bar */}
                  <div className="space-y-2">
                    {result.elapsed_seconds && result.estimated_remaining ? (
                      // Progress bar con dati reali
                      <>
                        <div className="flex justify-between text-sm text-indigo-700 font-semibold">
                          <span>🎯 Progresso CV Parsing</span>
                          <span className="bg-indigo-100 px-2 py-1 rounded text-xs">
                            {Math.round((result.elapsed_seconds / (result.elapsed_seconds + result.estimated_remaining)) * 100)}%
                          </span>
                        </div>
                        <div className="w-full bg-gray-200 rounded-full h-4 border border-gray-300">
                          <div 
                            className="bg-gradient-to-r from-blue-500 via-indigo-500 to-purple-600 h-full rounded-full transition-all duration-1000 ease-out relative overflow-hidden"
                            style={{
                              width: `${Math.min(95, (result.elapsed_seconds / (result.elapsed_seconds + result.estimated_remaining)) * 100)}%`
                            }}
                          >
                            <div className="absolute inset-0 bg-white opacity-20 animate-pulse"></div>
                          </div>
                        </div>
                        <div className="flex justify-between text-sm text-gray-600 bg-white rounded p-2 border">
                          <span>⏱️ Trascorsi: <strong>{result.elapsed_seconds}s</strong></span>
                          <span>⌛ Rimanenti: <strong>~{Math.round(result.estimated_remaining)}s</strong></span>
                        </div>
                      </>
                    ) : (
                      // Progress bar animata di fallback
                      <>
                        <div className="flex justify-between text-sm text-indigo-700 font-semibold">
                          <span>🎯 Parsing in corso...</span>
                          <span className="bg-yellow-100 px-2 py-1 rounded text-xs animate-pulse">AI Working</span>
                        </div>
                        <div className="w-full bg-gray-200 rounded-full h-4 border border-gray-300">
                          <div className="bg-gradient-to-r from-blue-500 via-indigo-500 to-purple-600 h-full rounded-full animate-pulse">
                            <div className="h-full bg-gradient-to-r from-transparent via-white to-transparent opacity-30 animate-bounce"></div>
                          </div>
                        </div>
                        <div className="text-center text-sm text-gray-600 bg-white rounded p-2 border">
                          <span>🧠 Ollama AI sta analizzando il documento...</span>
                        </div>
                      </>
                    )}
                  </div>
                  
                  {taskId && (
                    <div className="flex items-center text-xs text-blue-500">
                      <span className="mr-2">🔄</span>
                      <span>Task ID: {taskId}</span>
                    </div>
                  )}
                  
                  <div className="p-3 bg-white rounded-lg border">
                    <div className="flex items-center justify-between text-sm">
                      <div className="flex items-center text-indigo-700">
                        <span className="mr-2">🧠</span>
                        <span>Ollama AI sta analizzando il CV...</span>
                      </div>
                      <div className="text-xs text-gray-500">
                        Modello: llama3.2:3b
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {result && result.status !== 'processing' && (
              <div className="space-y-4">
                <div className="flex items-center justify-between p-3 bg-green-50 border border-green-200 rounded-lg">
                  <div className="flex items-center text-green-800">
                    <span className="mr-2">✅</span>
                    <span className="font-medium">CV Parserato con successo!</span>
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
                
                {/* CV Structured Data Display */}
                <div className="border-2 border-blue-200 bg-gradient-to-r from-blue-50 to-indigo-50 rounded-xl overflow-hidden shadow-lg">
                  <div className="bg-gradient-to-r from-blue-100 to-indigo-100 px-4 py-3 text-sm font-semibold text-blue-800 flex items-center justify-between border-b border-blue-200">
                    <span className="flex items-center">
                      <span className="mr-2">�</span>
                      <span>Dati CV Estratti</span>
                    </span>
                    <div className="flex gap-2">
                      <button 
                        onClick={() => navigator.clipboard.writeText(JSON.stringify(result, null, 2))}
                        className="text-xs text-blue-600 hover:text-blue-800 font-medium bg-white px-2 py-1 rounded border border-blue-200 hover:bg-blue-50 transition-colors"
                      >
                        📋 Copia JSON
                      </button>
                    </div>
                  </div>
                  <div className="p-5 bg-white">
                    {result?.personal_info?.full_name && (
                      <div className="mb-4 p-3 bg-blue-50 rounded-lg border border-blue-200">
                        <h3 className="font-semibold text-blue-900 text-lg mb-1">
                          {result.personal_info.full_name}
                        </h3>
                        {result.personal_info.email && (
                          <p className="text-sm text-blue-700">📧 {result.personal_info.email}</p>
                        )}
                        {result.personal_info.phone && (
                          <p className="text-sm text-blue-700">📱 {result.personal_info.phone}</p>
                        )}
                        {result.personal_info.address && (
                          <p className="text-sm text-blue-700">� {result.personal_info.address}</p>
                        )}
                        {result.personal_info.linkedin && (
                          <p className="text-sm text-blue-700">🔗 LinkedIn: {result.personal_info.linkedin}</p>
                        )}
                      </div>
                    )}
                    
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                      {result?.skills && result.skills.length > 0 && (
                        <div className="p-3 bg-green-50 rounded-lg border border-green-200">
                          <h4 className="font-semibold text-green-800 mb-2">🔧 Competenze</h4>
                          <div className="flex flex-wrap gap-1">
                            {result.skills.map((skill: any, index: number) => (
                              <span key={index} className="px-2 py-1 bg-green-200 text-green-800 rounded-full text-xs">
                                {typeof skill === 'string' ? skill : skill.name}
                              </span>
                            ))}
                          </div>
                        </div>
                      )}
                      
                      {result?.languages && result.languages.length > 0 && (
                        <div className="p-3 bg-purple-50 rounded-lg border border-purple-200">
                          <h4 className="font-semibold text-purple-800 mb-2">🌍 Lingue</h4>
                          <div className="space-y-1">
                            {result.languages.map((lang: any, index: number) => (
                              <div key={index} className="text-sm text-purple-700">
                                {lang.name} {lang.proficiency && `(${lang.proficiency})`}
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                    
                    {result?.experience && result.experience.length > 0 && (
                      <div className="mb-4 p-3 bg-orange-50 rounded-lg border border-orange-200">
                        <h4 className="font-semibold text-orange-800 mb-2">💼 Esperienze Lavorative</h4>
                        <div className="space-y-2">
                          {result.experience.slice(0, 3).map((exp: any, index: number) => (
                            <div key={index} className="text-sm text-orange-700 border-l-2 border-orange-300 pl-3">
                              <div className="font-medium">{exp.title}</div>
                              <div className="text-orange-600">
                                {exp.company} {exp.city && `• ${exp.city}`}
                              </div>
                              <div className="text-xs text-orange-500">
                                {exp.start_date} {exp.end_date ? `- ${exp.end_date}` : '- Attuale'}
                              </div>
                            </div>
                          ))}
                          {result.experience.length > 3 && (
                            <div className="text-xs text-orange-600">
                              ... e altre {result.experience.length - 3} esperienze
                            </div>
                          )}
                        </div>
                      </div>
                    )}
                    
                    {result?.education && result.education.length > 0 && (
                      <div className="mb-4 p-3 bg-indigo-50 rounded-lg border border-indigo-200">
                        <h4 className="font-semibold text-indigo-800 mb-2">🎓 Formazione</h4>
                        <div className="space-y-2">
                          {result.education.map((edu: any, index: number) => (
                            <div key={index} className="text-sm text-indigo-700">
                              <div className="font-medium">{edu.degree} {edu.field_of_study && `in ${edu.field_of_study}`}</div>
                              <div className="text-indigo-600">
                                {edu.institution} {edu.city && `• ${edu.city}`}
                              </div>
                              {edu.graduation_year && (
                                <div className="text-xs text-indigo-500">Anno: {edu.graduation_year}</div>
                              )}
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {result?.summary && (
                      <div className="mb-4 p-3 bg-gray-50 rounded-lg border border-gray-200">
                        <h4 className="font-semibold text-gray-800 mb-2">📝 Riassunto Professionale</h4>
                        <p className="text-sm text-gray-700">{result.summary}</p>
                      </div>
                    )}

                    {result?.certifications && result.certifications.length > 0 && (
                      <div className="mb-4 p-3 bg-yellow-50 rounded-lg border border-yellow-200">
                        <h4 className="font-semibold text-yellow-800 mb-2">🏆 Certificazioni</h4>
                        <div className="space-y-1">
                          {result.certifications.map((cert: any, index: number) => (
                            <div key={index} className="text-sm text-yellow-700">
                              <span className="font-medium">{cert.name}</span>
                              {cert.issuer && <span className="text-yellow-600"> • {cert.issuer}</span>}
                              {cert.date_obtained && <span className="text-xs text-yellow-500"> ({cert.date_obtained})</span>}
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                    
                    {/* Raw JSON fallback */}
                    <details className="mt-4">
                      <summary className="cursor-pointer text-sm font-medium text-gray-600 hover:text-gray-800">
                        📄 Visualizza JSON completo
                      </summary>
                      <div className="mt-2 p-3 bg-gray-50 rounded border overflow-auto max-h-[30vh]">
                        <pre className="text-xs text-gray-800 whitespace-pre-wrap font-mono">
                          {JSON.stringify(result, null, 2)}
                        </pre>
                      </div>
                    </details>
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
