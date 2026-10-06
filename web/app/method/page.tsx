import Link from "next/link";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "How the comparison works | Holiday Impact",
  description: "The dates, calculations, and data quality rules behind the Rossmann holiday sales dashboard.",
};

export default function MethodPage() {
  return <main className="story-page method-page">
    <div className="story-container">
      <div className="story-kicker"><span className="story-kicker-line" /> THE METHOD / 03</div>
      <section className="story-hero method-hero"><div><h1>From dates<br />to <em>meaning.</em></h1><p>Every number on the results page comes from the same 37 day comparison for each eligible store.</p><div className="story-actions"><Link className="story-action" href="/">View the results <span aria-hidden="true">↗</span></Link><Link className="story-text-link" href="/about">Project overview</Link></div></div><div className="method-motif" aria-hidden="true"><span>30</span><i>+</i><span>7</span></div></section>
      <section className="story-section"><div className="story-section-head"><div><span className="story-kicker">THE TWO WINDOWS</span><h2>A fair daily comparison.</h2></div><p>Using daily averages lets us compare a month with a week without confusing window length with sales performance.</p></div><div className="window-grid"><div className="window-card"><span>01 / BASELINE</span><strong>30 days</strong><p>The 30 calendar days immediately before the holiday window.</p></div><div className="window-card accent"><span>02 / HOLIDAY</span><strong>7 days</strong><p>Three days before the holiday, the holiday itself, and three days after.</p></div></div><div className="example-line"><strong>Example for 25 December</strong><span>22 November to 21 December: baseline</span><span>22 December to 28 December: holiday window</span></div></section>
      <section className="formula-section"><div><span className="story-kicker">THE CALCULATION</span><h2>Compare averages,<br />then find the change.</h2></div><div className="formula-card"><div><span>BASELINE DAILY AVERAGE</span><strong>8,000</strong></div><div><span>HOLIDAY DAILY AVERAGE</span><strong>10,000</strong></div><div className="formula-answer"><span>OBSERVED CHANGE</span><strong>+25%</strong><small>(10,000 minus 8,000) divided by 8,000</small></div></div></section>
      <section className="story-section"><div className="story-section-head"><div><span className="story-kicker">DATA QUALITY</span><h2>What counts, and what does not.</h2></div></div><div className="rule-grid"><article><span>01</span><h3>Closed day</h3><p>A recorded closed day with zero sales stays in the comparison. It is a real observation.</p></article><article><span>02</span><h3>Missing day</h3><p>A missing store day is never invented as zero. That store is excluded for that event.</p></article><article><span>03</span><h3>Repeated row</h3><p>The first MapReduce stage chooses one record per store and date before sales are counted.</p></article><article><span>04</span><h3>Holiday eligibility</h3><p>Only stores marked with the holiday code on the central date enter that event.</p></article></div></section>
      <section className="truth-card"><span className="story-kicker">INTERPRETING THE RESULT</span><h2>A measured difference, not a cause.</h2><p>Promotions, store closures, weekdays, and nearby events may influence sales too. The dashboard reports an observed comparison from historical data, not a causal claim or a forecast.</p><Link href="/">Return to results <span aria-hidden="true">↗</span></Link></section>
      <footer className="story-footer">For implementation details and data limits, see the project documentation in the repository.</footer>
    </div>
  </main>;
}
