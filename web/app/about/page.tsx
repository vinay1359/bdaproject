import Link from "next/link";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "About the project | Holiday Impact",
  description: "Learn what the Rossmann holiday sales project measures and how its data moves through the system.",
};

const stages = [
  { number: "01", name: "Read", tool: "Python", detail: "Validate each daily sales row from the Rossmann CSV file." },
  { number: "02", name: "Pass", tool: "Kafka", detail: "Publish the historical rows as messages in a named topic." },
  { number: "03", name: "Keep", tool: "HDFS", detail: "Save those messages as durable raw batches." },
  { number: "04", name: "Calculate", tool: "MapReduce", detail: "Compare holiday days with the previous month." },
  { number: "05", name: "Show", tool: "Next.js", detail: "Read the finished result file and draw the dashboard." },
];

export default function AboutPage() {
  return <main className="story-page">
    <div className="story-container">
      <div className="story-kicker"><span className="story-kicker-line" /> ABOUT THE PROJECT / 02</div>
      <section className="story-hero">
        <div><h1>A sales question,<br /><em>made visible.</em></h1><p>This project asks a simple question: how did store sales change around a holiday compared with the days before it?</p><div className="story-actions"><Link className="story-action" href="/">Explore results <span aria-hidden="true">↗</span></Link><Link className="story-text-link" href="/method">See the method</Link></div></div>
        <div className="hero-stamp" aria-hidden="true"><span>37</span><small>DAYS IN EACH<br />COMPARISON</small><i /></div>
      </section>
      <section className="statement-grid">
        <div className="statement-label">THE IDEA<br />IN ONE MINUTE</div>
        <div className="statement-copy"><h2>First, collect daily sales. Then compare two windows.</h2><p>The seven days centered on a holiday are measured against the 30 calendar days immediately before that window. We compare daily averages because the windows are different lengths.</p><p>The result tells us what happened in the records. It does not prove the holiday caused the change.</p></div>
      </section>
      <section className="story-section">
        <div className="story-section-head"><div><span className="story-kicker">THE JOURNEY / 01 TO 05</span><h2>One row, five stops.</h2></div><p>Each tool has a distinct job. The dashboard is the last stop, after the calculations finish.</p></div>
        <div className="stage-list">{stages.map((stage) => <div className="stage-row" key={stage.number}><span className="stage-number">{stage.number}</span><strong>{stage.name}</strong><span className="stage-tool">{stage.tool}</span><p>{stage.detail}</p></div>)}</div>
      </section>
      <section className="truth-card"><span className="story-kicker">WHAT THE DATA CAN SAY</span><h2>Store sales, not product sales.</h2><p>Rossmann provides a daily sales amount for each store from 2013 to 2015. It does not tell us how many items were sold or which product category earned the money. Store type and assortment are store attributes, so they are useful filters but not product category results.</p><Link href="/method">Read how we handle missing days <span aria-hidden="true">↗</span></Link></section>
      <footer className="story-footer">A local learning project using historical Rossmann Store Sales data.</footer>
    </div>
  </main>;
}
