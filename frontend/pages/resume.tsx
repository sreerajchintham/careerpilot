import { useState } from 'react'

// Resume upload page with file input, upload progress, and success/error states
export default function ResumePage() {
  const [fileName, setFileName] = useState<string>("")
  const [fileObj, setFileObj] = useState<File | null>(null)
  const [uploading, setUploading] = useState(false)
  const [uploadProgress, setUploadProgress] = useState(0)
  const [resultPath, setResultPath] = useState<string>("")
  const [error, setError] = useState<string>("")
  const [success, setSuccess] = useState(false)

  // Handle file selection from input
  function handleFileChange(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0]
    setFileName(file ? file.name : "")
    setFileObj(file ?? null)
    // Reset previous states when new file is selected
    setError("")
    setResultPath("")
    setSuccess(false)
    setUploadProgress(0)
  }

  // Handle file upload to backend
  async function handleSubmit() {
    if (!fileObj) {
      setError("Please select a file first")
      return
    }

    // Reset states
    setError("")
    setResultPath("")
    setSuccess(false)
    setUploadProgress(0)

    try {
      setUploading(true)
      const form = new FormData()
      // Backend expects field name 'file'
      form.append('file', fileObj)

      // Create XMLHttpRequest for upload progress tracking
      const xhr = new XMLHttpRequest()
      
      // Track upload progress
      xhr.upload.addEventListener('progress', (e) => {
        if (e.lengthComputable) {
          const percentComplete = Math.round((e.loaded / e.total) * 100)
          setUploadProgress(percentComplete)
        }
      })

      // Handle response
      xhr.addEventListener('load', () => {
        if (xhr.status >= 200 && xhr.status < 300) {
          try {
            const data = JSON.parse(xhr.responseText)
            setResultPath(data.path || '')
            setSuccess(true)
            setUploadProgress(100)
          } catch (parseError) {
            setError('Invalid response from server')
          }
        } else {
          setError(`Upload failed: ${xhr.status} ${xhr.statusText}`)
        }
        setUploading(false)
      })

      // Handle network errors
      xhr.addEventListener('error', () => {
        setError('Network error - please check if backend is running')
        setUploading(false)
      })

      // Handle timeout
      xhr.addEventListener('timeout', () => {
        setError('Upload timeout - file may be too large')
        setUploading(false)
      })

      // Configure and send request
      xhr.open('POST', 'http://127.0.0.1:8001/upload-resume')
      xhr.timeout = 30000 // 30 second timeout
      xhr.send(form)

    } catch (e: any) {
      setError(e?.message || 'Upload failed')
      setUploading(false)
    }
  }

  return (
    <main className="min-h-screen flex items-center justify-center p-6">
      <div className="w-full max-w-xl">
        <h1 className="text-2xl sm:text-3xl font-semibold text-center">Upload a resume to start</h1>
        <p className="mt-2 text-gray-600 text-center">Choose a PDF or DOCX to begin.</p>

        <div className="mt-6 rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
          {/* File input */}
          <label className="block">
            <span className="sr-only">Choose file</span>
            <input
              type="file"
              accept=".pdf,.doc,.docx"
              onChange={handleFileChange}
              disabled={uploading}
              className="block w-full text-sm text-gray-700 file:mr-4 file:rounded-md file:border-0 file:bg-blue-600 file:px-4 file:py-2 file:text-white hover:file:bg-blue-700 disabled:opacity-50"
            />
          </label>

          {/* Selected file info */}
          {fileName && (
            <div className="mt-3 p-3 bg-gray-50 rounded-md">
              <p className="text-sm text-gray-700">
                <span className="font-medium">Selected:</span> {fileName}
              </p>
              <p className="text-xs text-gray-500 mt-1">
                Size: {fileObj ? `${(fileObj.size / 1024 / 1024).toFixed(2)} MB` : 'Unknown'}
              </p>
            </div>
          )}

          {/* Upload progress bar */}
          {uploading && (
            <div className="mt-4">
              <div className="flex justify-between text-sm text-gray-600 mb-1">
                <span>Uploading...</span>
                <span>{uploadProgress}%</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div 
                  className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                  style={{ width: `${uploadProgress}%` }}
                ></div>
              </div>
            </div>
          )}

          {/* Upload button */}
          <button
            type="button"
            className="mt-4 w-full rounded-md bg-gray-900 px-4 py-2 text-white hover:bg-black disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            disabled={!fileName || uploading}
            onClick={handleSubmit}
          >
            {uploading ? 'Uploading...' : 'Upload Resume'}
          </button>

          {/* Success message */}
          {success && resultPath && (
            <div className="mt-4 p-3 bg-green-50 border border-green-200 rounded-md">
              <p className="text-sm text-green-800 font-medium">✅ Upload successful!</p>
              <p className="text-xs text-green-700 mt-1 break-all">
                Saved to: {resultPath}
              </p>
            </div>
          )}

          {/* Error message */}
          {error && (
            <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-md">
              <p className="text-sm text-red-800 font-medium">❌ Upload failed</p>
              <p className="text-xs text-red-700 mt-1">{error}</p>
            </div>
          )}
        </div>
      </div>
    </main>
  )
}


