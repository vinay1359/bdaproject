"use client";

import { useMemo, useState } from "react";
import dynamic from "next/dynamic";
import { DrawablyUnderline } from "drawably/react";
import type { EChartsOption } from "echarts";
import type { Results } from "@/lib/results";

const Chart = dynamic(() => import("echarts-for-react"), { ssr: false });

const codeName: Record<string, string> = { a: "Public holiday", b: "Easter holiday", c: "Christmas holiday" };
const number = (value: number | null, digits = 0) => value === null ? "N/A" : new Intl.NumberFormat("en-US", { maximumFractionDigits: digits }).format(value);
const signed = (value: number | null, suffix = "") => value === null ? "N/A" : `${value > 0 ? "+" : ""}${number(value, 1)}${suffix}`;
const displayName = (value: string) => value.replace(/[\u2013\u2014]/g, " / ");

export default function Dashboard({ results }: { results: Results | null }) {
  const events = useMemo(() => [...(results?.events ?? [])].sort((a, b) => b.date.localeCompare(a.date)), [results]);
  const [eventId, setEventId] = useState<string | null>(null);
  const [group, setGroup] = useState("all");
  const [code, setCode] = useState("all");
  const [year, setYear] = useState("all");
  const years = [...new Set(events.map((event) => event.date.slice(0, 4)))];
  const shownEvents = events.filter((event) => (code === "all" || event.code === code) && (year === "all" || event.date.startsWith(year)));
  const selected = shownEvents.find((event) => event.id === eventId)
    ?? shownEvents.find((event) => results?.summary.some((item) => item.event_id === event.id && item.group === group && item.included_stores > 0))
    ?? shownEvents[0];
  const row = results?.summary.find((item) => item.event_id === selected?.id && item.group === group);
  const groups = useMemo(() => [...new Set((results?.summary ?? []).map((item) => item.group))].sort(), [results]);
  const series = useMemo(() => (results?.daily ?? []).filter((day) => day.event_id === selected?.id && day.group === group).sort((a, b) => a.day_offset - b.day_offset), [results, selected, group]);

  const option: EChartsOption = {
    backgroundColor: "transparent",
    grid: { left: 50, right: 18, top: 30, bottom: 54 },
    tooltip: { trigger: "axis", valueFormatter: (value) => number(Number(value), 1) },
    xAxis: { type: "category", data: series.map((point) => point.day_offset === 0 ? "Holiday" : `${point.day_offset > 0 ? "+" : ""}${point.day_offset}d`), axisLabel: { color: "#666666", interval: 3 }, axisLine: { lineStyle: { color: "#cccccc" } } },
    yAxis: { type: "value", axisLabel: { color: "#666666" }, splitLine: { lineStyle: { color: "#eeeeee" } } },
    series: [{ type: "line", data: series.map((point) => point.sales_per_store), smooth: 0.22, showSymbol: series.length < 20, symbolSize: 6, lineStyle: { color: "#d32231", width: 3 }, itemStyle: { color: "#d32231" }, areaStyle: { color: "rgba(211,34,49,.07)" }, markArea: { silent: true, itemStyle: { color: "rgba(211,34,49,.05)" }, data: [[{ xAxis: "-3d" }, { xAxis: "+3d" }]] } }],
  };

  return <div className="shell">
    <main className="main">
      <div className="content">
        <div className="heading-row"><div><div className="eyebrow">ROSSMANN SALES STUDY <span className="eyebrow-index">/ RESULTS</span></div><h1>Did sales change<br />for the <em><DrawablyUnderline seed={42} boil={0}>holidays?</DrawablyUnderline></em></h1><p className="subtitle">Explore daily store sales around holidays from 2013 to 2015.</p></div><div className="heading-actions"><div className="run-badge">{results ? `UPDATED ${results.completed_at.slice(0, 10)}` : "AWAITING FIRST RUN"}</div><button className="reset-button" type="button" onClick={() => { setYear("all"); setCode("all"); setGroup("all"); setEventId(null); }}>Reset filters <span aria-hidden="true">↗</span></button></div></div>
        {!results ? <div className="empty panel"><div className="empty-icon">◫</div><h2>No analysis results yet</h2><p>The dashboard will populate after Kafka ingestion and the Hadoop MapReduce job complete. Follow the commands in the project README to run the pipeline.</p><code>docker compose exec job python3 /app/src/jobs/run.py</code></div> : <>
          <section className="filters panel" aria-label="Result filters"><div className="filter-intro">EXPLORE<br /><strong>THE DATA</strong></div><label>YEAR<select value={year} onChange={(e) => { setYear(e.target.value); setEventId(null); }}><option value="all">All years</option>{years.map((item) => <option value={item} key={item}>{item}</option>)}</select></label><label>HOLIDAY TYPE<select value={code} onChange={(e) => { setCode(e.target.value); setEventId(null); }}><option value="all">All holidays</option><option value="a">Public</option><option value="b">Easter</option><option value="c">Christmas</option></select></label><label>HOLIDAY EVENT<select value={selected?.id ?? ""} onChange={(e) => setEventId(e.target.value)}>{shownEvents.map((event) => <option value={event.id} key={event.id}>{displayName(event.name)}</option>)}</select></label><label>STORE GROUP<select value={group} onChange={(e) => setGroup(e.target.value)}>{groups.map((item) => <option value={item} key={item}>{item === "all" ? "All stores" : item.replace(":", " / ").replace("_", " ")}</option>)}</select></label></section>
          <div className="event-line"><span className="event-code">{selected?.code?.toUpperCase() ?? "?"}</span><div><strong>{selected ? displayName(selected.name) : "No event"}</strong><small>{selected?.date} · {codeName[selected?.code ?? ""] ?? ""}</small></div><span className="window-note">7 day window vs previous 30 days</span></div>
          <section className="metrics"><Metric label="01 / HOLIDAY DAILY AVERAGE" value={number(row?.holiday_daily_mean ?? null, 1)} detail="Sales amount per store per day" /><Metric label="02 / BASELINE DAILY AVERAGE" value={number(row?.baseline_daily_mean ?? null, 1)} detail="Previous 30 calendar days" /><Metric label="03 / OBSERVED CHANGE" value={signed(row?.percent_change ?? null, "%")} detail={`${signed(row?.delta_daily ?? null)} per store per day`} highlight /><Metric label="04 / STORE COVERAGE" value={row ? `${row.included_stores}/${row.eligible_stores}` : "N/A"} detail={`${row?.excluded_stores ?? 0} excluded for missing days`} /></section>
          <section className="body-grid"><div className="panel chart-panel"><div className="panel-header"><div><div className="section-kicker">DAILY TREND</div><h2>Sales around the holiday</h2><p>Average sales per included store for each calendar day.</p></div><span className="legend"><i /> Daily sales</span></div>{series.length ? <Chart option={option} style={{ height: 315 }} notMerge /> : <div className="no-series">No complete store-day series for this event.</div>}<div className="chart-caption"><span>30-day baseline</span><span>7-day holiday window</span></div></div><div className="panel context-panel"><div className="section-kicker">READ THE RESULT</div><h2>Context & quality</h2><ContextLine label="Eligible stores" value={number(row?.eligible_stores ?? null)} /><ContextLine label="Complete store records" value={number(row?.included_stores ?? null)} /><ContextLine label="Excluded stores" value={number(row?.excluded_stores ?? null)} /><div className="divider" /><ContextLine label="Holiday promo-days" value={number(row?.holiday_promo_days ?? null)} /><ContextLine label="Holiday closed-days" value={number(row?.holiday_closed_days ?? null)} /><div className="context-note">A missing store-day is never treated as zero. Recorded closed days remain in the calculation.</div></div></section>
          <section className="panel table-panel"><div className="panel-header"><div><div className="section-kicker">EVENT COMPARISON</div><h2>Holiday results</h2><p>All events for the selected store group.</p></div></div><div className="table-wrap"><table><thead><tr><th>HOLIDAY</th><th>DATE</th><th>STORES</th><th>BASELINE / DAY</th><th>HOLIDAY / DAY</th><th>CHANGE</th></tr></thead><tbody>{shownEvents.map((event) => { const item = results.summary.find((summary) => summary.event_id === event.id && summary.group === group); return <tr key={event.id} className={selected?.id === event.id ? "selected-row" : ""}><td><button className="event-button" onClick={() => setEventId(event.id)}>{displayName(event.name)}</button></td><td>{event.date}</td><td>{item ? `${item.included_stores}/${item.eligible_stores}` : "N/A"}</td><td>{number(item?.baseline_daily_mean ?? null, 1)}</td><td>{number(item?.holiday_daily_mean ?? null, 1)}</td><td className={(item?.percent_change ?? 0) >= 0 ? "positive" : "negative"}>{signed(item?.percent_change ?? null, "%")}</td></tr>; })}</tbody></table></div></section>
          <footer>Source: Rossmann Store Sales · Measure: store daily sales amount · Last completed: {results.completed_at.slice(0, 19).replace("T", " ")} UTC<br />These are observed comparisons. Rossmann does not contain product-category sales or item quantities.</footer>
        </>}
      </div>
    </main>
  </div>;
}

function Metric({ label, value, detail, highlight = false }: { label: string; value: string; detail: string; highlight?: boolean }) { return <div className={`metric panel ${highlight ? "metric-highlight" : ""}`}><div className="metric-label">{label}</div><div className="metric-value">{value}</div><div className="metric-detail">{detail}</div></div>; }
function ContextLine({ label, value }: { label: string; value: string }) { return <div className="context-line"><span>{label}</span><strong>{value}</strong></div>; }

