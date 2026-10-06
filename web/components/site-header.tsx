import Link from "next/link";

export default function SiteHeader() {
  return <header className="site-header">
    <div className="site-header-inner">
      <Link className="site-brand" href="/" aria-label="Holiday Impact home">
        <span className="site-brand-mark" aria-hidden="true">H<span>.</span></span>
        <span>HOLIDAY IMPACT</span>
      </Link>
      <nav className="site-nav" aria-label="Main navigation">
        <Link href="/">Results</Link>
        <Link href="/about">About</Link>
        <Link href="/method">Method</Link>
      </nav>
      <span className="site-edition">AN OPEN DATA STUDY</span>
    </div>
  </header>;
}
