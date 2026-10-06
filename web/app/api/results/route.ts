import { NextResponse } from "next/server";
import { readResults } from "@/lib/results";

export const dynamic = "force-dynamic";

export async function GET() {
  const results = await readResults();
  return NextResponse.json(results ?? { error: "No completed MapReduce run yet" }, { status: results ? 200 : 404 });
}
