"use client";

import { clsx } from "clsx";
import {
    Home, LineChart, Newspaper, TrendingUp, GitCompare, Search,
    type LucideProps,
} from "lucide-react";

const MAP = {
    home: Home,
    lineChart: LineChart,
    newspaper: Newspaper,
    trendingUp: TrendingUp,
    compare: GitCompare,
    search: Search,
} as const;

export type IconName = keyof typeof MAP;

export default function Icon({
    name,
    className,
    ...rest
}: { name: IconName } & LucideProps) {
    const Cmp = MAP[name];
    return <Cmp className={clsx("shrink-0", className)} aria-hidden {...rest} />;
}