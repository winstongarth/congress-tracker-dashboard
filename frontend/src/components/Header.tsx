import Link from "next/link";

export default function Header() {
  return (
    <header className="flex items-center gap-6 border-b border-gray-200 bg-white px-4 py-3">
      <Link href="/" className="text-lg font-semibold text-gray-900">
        Congress Portfolio Tracker
      </Link>
      <nav className="flex gap-4 text-sm text-gray-600">
        <Link href="/" className="hover:text-gray-900 hover:underline">
          Trades
        </Link>
        <Link href="/members" className="hover:text-gray-900 hover:underline">
          Members
        </Link>
      </nav>
    </header>
  );
}
