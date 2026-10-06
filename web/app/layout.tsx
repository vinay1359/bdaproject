import type { Metadata } from "next";
import "drawably/style.css";
import "./globals.css";
import SiteHeader from "@/components/site-header";

export const metadata: Metadata = {
  title: "Holiday Impact | Rossmann Sales",
  description: "Observed holiday sales comparisons from Rossmann store-day data.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="en"><body><SiteHeader />{children}</body></html>;
}
