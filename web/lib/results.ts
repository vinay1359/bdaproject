import { readFile } from "node:fs/promises";
import path from "node:path";

export type Event = { id: string; date: string; code: string; name: string };
export type Summary = {
  event_id: string; group: string; eligible_stores: number; included_stores: number; excluded_stores: number;
  baseline_sales: number; holiday_sales: number; baseline_daily_mean: number | null;
  holiday_daily_mean: number | null; delta_daily: number | null; percent_change: number | null;
  baseline_promo_days: number; holiday_promo_days: number;
  baseline_closed_days: number; holiday_closed_days: number;
};
export type Daily = { event_id: string; group: string; day_offset: number; window: string; sales_total: number; stores: number; sales_per_store: number | null };
export type Results = { run_id: string; completed_at: string; source: string; measure: string; events: Event[]; summary: Summary[]; daily: Daily[] };

export async function readResults(): Promise<Results | null> {
  const file = process.env.RESULTS_FILE ?? path.resolve(process.cwd(), "../data/results/latest.json");
  try {
    return JSON.parse(await readFile(file, "utf8")) as Results;
  } catch (error) {
    if ((error as NodeJS.ErrnoException).code === "ENOENT") return null;
    throw error;
  }
}
