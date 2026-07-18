import type { QueryAnswer } from "@/lib/types";

interface ResultTableProps {
  answer: QueryAnswer | null;
}

export function ResultTable({ answer }: ResultTableProps) {
  if (!answer) {
    return <p className="text-sm text-slate-500 dark:text-slate-400">No query result yet.</p>;
  }

  if (!answer.rows.length) {
    return <p className="text-sm text-slate-500 dark:text-slate-400">The query ran successfully but returned no rows.</p>;
  }

  return (
    <div className="overflow-hidden rounded-2xl border border-slate-200 dark:border-slate-800">
      <div className="overflow-x-auto">
        <table className="min-w-full border-collapse text-left text-sm">
          <thead className="bg-slate-100/80 dark:bg-slate-900">
            <tr>
              {answer.columns.map((column) => (
                <th key={column} className="px-4 py-3 font-medium text-slate-700 dark:text-slate-200">
                  {column}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {answer.rows.map((row, rowIndex) => (
              <tr
                key={rowIndex}
                className="border-t border-slate-200 bg-white/70 even:bg-slate-50/70 dark:border-slate-800 dark:bg-slate-950/60 dark:even:bg-slate-900/50"
              >
                {row.map((cell, cellIndex) => (
                  <td key={`${rowIndex}-${cellIndex}`} className="px-4 py-3 text-slate-700 dark:text-slate-200">
                    {String(cell)}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
