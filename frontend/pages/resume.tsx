import { useState } from 'react'

// Simple resume upload page with a file input and placeholder text
export default function ResumePage() {
  const [fileName, setFileName] = useState<string>("")

  function handleFileChange(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0]
    setFileName(file ? file.name : "")
    // Note: No upload yet; this is just UI scaffolding.
  }

  return (
    <main className="min-h-screen flex items-center justify-center p-6">
      <div className="w-full max-w-xl">
        <h1 className="text-2xl sm:text-3xl font-semibold text-center">Upload a resume to start</h1>
        <p className="mt-2 text-gray-600 text-center">Choose a PDF or DOCX to begin.</p>

        <div className="mt-6 rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
          <label className="block">
            <span className="sr-only">Choose file</span>
            <input
              type="file"
              accept=".pdf,.doc,.docx"
              onChange={handleFileChange}
              className="block w-full text-sm text-gray-700 file:mr-4 file:rounded-md file:border-0 file:bg-blue-600 file:px-4 file:py-2 file:text-white hover:file:bg-blue-700"
            />
          </label>

          {fileName && (
            <p className="mt-3 text-sm text-gray-700">Selected: {fileName}</p>
          )}

          <button
            type="button"
            className="mt-4 w-full rounded-md bg-gray-900 px-4 py-2 text-white hover:bg-black disabled:opacity-50"
            disabled={!fileName}
            onClick={() => alert('Upload not implemented yet')}
          >
            Continue
          </button>
        </div>
      </div>
    </main>
  )
}


