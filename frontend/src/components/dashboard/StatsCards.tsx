import * as React from "react";
import { StatsCard } from "@/components/ui/card";

export default function StatsCards() {
  return (
    <>
      <StatsCard value="12" label="Total Projects" />
      <StatsCard value="5" label="Active Agents" />
      <StatsCard value="8" label="Research Tasks" />
      <StatsCard value="24" label="Completed Tasks" />
    </>
  );
}