export default function NotFound() {
  return (
    <div className="min-h-[60vh] flex items-center justify-center">
      <div className="text-center space-y-4">
        <h1 className="text-6xl font-black text-gradient-purple">404</h1>
        <p className="text-xl text-muted">Page not found. The resource you're looking for might have moved.</p>
        <a href="/" className="inline-block mt-4 rounded-3xl border border-white/10 bg-slate-900/70 px-6 py-3 font-semibold">Go home</a>
      </div>
    </div>
  );
}
