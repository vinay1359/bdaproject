import { readResults } from "@/lib/results";
import Dashboard from "@/components/dashboard";

export const dynamic = "force-dynamic";

export default async function Home() {
  const results = await readResults();
  return <Dashboard results={results} />;
}
