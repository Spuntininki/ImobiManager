// Centralized query keys so mutations can invalidate related queries.

export const queryKeys = {
  owners: ["owners"] as const,
  owner: (ownerId: number) => ["owners", String(ownerId)] as const,
  ownerDocuments: (ownerId: number) =>
    ["owners", String(ownerId), "documents"] as const,
  renters: (ownerId: number) =>
    ["owners", String(ownerId), "renters"] as const,
  renterDocuments: (renterId: number) =>
    ["renters", String(renterId), "documents"] as const,
  addresses: (ownerId: number) =>
    ["owners", String(ownerId), "addresses"] as const,
  contracts: (ownerId: number) =>
    ["owners", String(ownerId), "contracts"] as const,
  revenueTimeline: (ownerId: number, range: Record<string, string>) =>
    ["owners", String(ownerId), "revenue-timeline", range] as const,
  revenueSummary: (ownerId: number, range: Record<string, string>) =>
    ["owners", String(ownerId), "revenue-timeline", "summary", range] as const,
};
