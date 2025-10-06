import Link from 'next/link'

// Landing page with a simple header and link to /resume
export default function HomePage() {
  return (
    <main className="min-h-screen flex items-center justify-center p-6">
      <div className="max-w-xl w-full text-center">
        <h1 className="text-2xl sm:text-3xl font-semibold">CareerPilot Agent — Dev</h1>
        <p className="mt-2 text-gray-600">Monorepo scaffold is ready.</p>
        <div className="mt-6">
          <Link
            href="/resume"
            className="inline-block rounded-md bg-blue-600 px-4 py-2 text-white hover:bg-blue-700 transition"
          >
            Go to Resume Upload
          </Link>
        </div>
      </div>
    </main>
  )
}


