import Link from "next/link";

export default function Pagination({
  page,
  pageSize,
  total,
  searchParamsString,
}: {
  page: number;
  pageSize: number;
  total: number;
  searchParamsString: string;
}) {
  const totalPages = Math.max(1, Math.ceil(total / pageSize));

  const hrefForPage = (p: number) => {
    const params = new URLSearchParams(searchParamsString);
    params.set("page", String(p));
    return `?${params.toString()}`;
  };

  return (
    <div className="flex items-center justify-between py-3 text-sm text-gray-600">
      <span>
        Showing page {page} of {totalPages} ({total} trades)
      </span>
      <div className="flex gap-2">
        <Link
          href={hrefForPage(Math.max(1, page - 1))}
          className={`rounded border px-3 py-1 ${page <= 1 ? "pointer-events-none text-gray-300" : "hover:bg-gray-50"}`}
        >
          Previous
        </Link>
        <Link
          href={hrefForPage(Math.min(totalPages, page + 1))}
          className={`rounded border px-3 py-1 ${page >= totalPages ? "pointer-events-none text-gray-300" : "hover:bg-gray-50"}`}
        >
          Next
        </Link>
      </div>
    </div>
  );
}
