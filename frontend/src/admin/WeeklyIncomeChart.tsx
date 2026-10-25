import { useEffect, useState } from "react";
import { format, parseISO } from "date-fns";
import { fetchWeeklyIncome, type WeeklyIncome } from "./api";

const WIDTH = 720;
const HEIGHT = 260;
const PAD = { top: 16, right: 12, bottom: 28, left: 44 };
const PLOT_W = WIDTH - PAD.left - PAD.right;
const PLOT_H = HEIGHT - PAD.top - PAD.bottom;

/** Sept 1 of the current season: this year from September on, else last year. */
function seasonStart(today: Date): string {
  const year = today.getMonth() >= 8 ? today.getFullYear() : today.getFullYear() - 1;
  return `${year}-09-01`;
}

/** Round the max up to a tidy axis value and split it into 4 gridlines. */
function niceTicks(max: number): number[] {
  if (max <= 0) return [0, 50, 100, 150, 200];
  const step = Math.pow(10, Math.floor(Math.log10(max / 4)));
  const nice = [1, 2, 2.5, 5, 10].map((m) => m * step).find((s) => s * 4 >= max)!;
  return [0, 1, 2, 3, 4].map((i) => i * nice);
}

const euro = (n: number) =>
  `€${n.toLocaleString("de-DE", { maximumFractionDigits: 2 })}`;

export function WeeklyIncomeChart() {
  const [weeks, setWeeks] = useState<WeeklyIncome[]>([]);
  const [loading, setLoading] = useState(true);
  const [hover, setHover] = useState<number | null>(null);

  useEffect(() => {
    fetchWeeklyIncome(seasonStart(new Date()))
      .then(setWeeks)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const total = weeks.reduce((sum, w) => sum + w.income, 0);
  const thisWeek = weeks.at(-1)?.income ?? 0;
  const ticks = niceTicks(Math.max(...weeks.map((w) => w.income), 0));
  const yMax = ticks[ticks.length - 1];
  const slot = weeks.length ? PLOT_W / weeks.length : PLOT_W;
  const barW = Math.max(Math.min(slot - 2, 40), 2);
  const y = (v: number) => PAD.top + PLOT_H - (v / yMax) * PLOT_H;
  // Label every Nth week so x-axis labels don't collide.
  const labelEvery = Math.ceil(weeks.length / 10);
  const hovered = hover !== null ? weeks[hover] : null;

  return (
    <div className="bg-card border border-border rounded-xl p-6 mb-6">
      <h3 className="text-lg font-semibold mb-1">Weekly Income</h3>
      <p className="text-sm text-muted-foreground mb-4">
        Past booked and completed appointments since{" "}
        {format(parseISO(seasonStart(new Date())), "MMMM d, yyyy")}
      </p>
      {loading ? (
        <div className="flex items-center justify-center py-8">
          <div className="w-6 h-6 border-2 border-primary border-t-transparent rounded-full animate-spin" />
        </div>
      ) : (
        <>
          <div className="flex gap-8 mb-4">
            <div>
              <div className="text-sm text-muted-foreground">Total</div>
              <div className="text-2xl font-bold">{euro(total)}</div>
            </div>
            <div>
              <div className="text-sm text-muted-foreground">This week</div>
              <div className="text-2xl font-bold">{euro(thisWeek)}</div>
            </div>
          </div>
          <div className="relative">
            <svg
              viewBox={`0 0 ${WIDTH} ${HEIGHT}`}
              className="w-full h-auto"
              role="img"
              aria-label="Bar chart of income per week"
              onMouseLeave={() => setHover(null)}
            >
              {ticks.map((t) => (
                <g key={t}>
                  <line
                    x1={PAD.left}
                    x2={WIDTH - PAD.right}
                    y1={y(t)}
                    y2={y(t)}
                    stroke="var(--color-border)"
                  />
                  <text
                    x={PAD.left - 6}
                    y={y(t)}
                    textAnchor="end"
                    dominantBaseline="middle"
                    fontSize="11"
                    fill="var(--color-muted-foreground)"
                  >
                    €{t}
                  </text>
                </g>
              ))}
              {weeks.map((w, i) => {
                const x = PAD.left + i * slot + (slot - barW) / 2;
                const h = PAD.top + PLOT_H - y(w.income);
                const r = Math.min(4, h, barW / 2);
                const top = y(w.income);
                const bottom = PAD.top + PLOT_H;
                return (
                  <g key={w.week_start}>
                    {h > 0 && (
                      // Rounded top corners only, flat on the baseline.
                      <path
                        d={`M${x},${bottom} V${top + r} Q${x},${top} ${x + r},${top} H${x + barW - r} Q${x + barW},${top} ${x + barW},${top + r} V${bottom} Z`}
                        fill="var(--color-primary)"
                        opacity={hover === null || hover === i ? 1 : 0.5}
                      />
                    )}
                    {i % labelEvery === 0 && (
                      <text
                        x={x + barW / 2}
                        y={HEIGHT - 8}
                        textAnchor="middle"
                        fontSize="11"
                        fill="var(--color-muted-foreground)"
                      >
                        {format(parseISO(w.week_start), "MMM d")}
                      </text>
                    )}
                    {/* Full-height hit target, wider than the bar. */}
                    <rect
                      x={PAD.left + i * slot}
                      y={PAD.top}
                      width={slot}
                      height={PLOT_H}
                      fill="transparent"
                      onMouseEnter={() => setHover(i)}
                      onClick={() => setHover(i)}
                    />
                  </g>
                );
              })}
            </svg>
            {hovered && hover !== null && (
              <div
                className="absolute pointer-events-none bg-card border border-border rounded-lg shadow-md px-3 py-2 text-sm whitespace-nowrap -translate-x-1/2"
                style={{
                  left: `${((PAD.left + (hover + 0.5) * slot) / WIDTH) * 100}%`,
                  top: 0,
                }}
              >
                <div className="text-muted-foreground">
                  Week of {format(parseISO(hovered.week_start), "MMM d")}
                </div>
                <div className="font-semibold">{euro(hovered.income)}</div>
                <div className="text-muted-foreground">
                  {hovered.appointments} appointment{hovered.appointments === 1 ? "" : "s"}
                </div>
              </div>
            )}
          </div>
          <table className="sr-only">
            <caption>Income per week</caption>
            <thead>
              <tr>
                <th>Week of</th>
                <th>Income</th>
                <th>Appointments</th>
              </tr>
            </thead>
            <tbody>
              {weeks.map((w) => (
                <tr key={w.week_start}>
                  <td>{w.week_start}</td>
                  <td>{euro(w.income)}</td>
                  <td>{w.appointments}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </>
      )}
    </div>
  );
}
