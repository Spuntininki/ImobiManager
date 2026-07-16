// Centralized query keys so mutations can invalidate related queries.

export const queryKeys = {
  owners: ["owners"],
  owner: (ownerId) => ["owners", String(ownerId)],
  ownerDocuments: (ownerId) => ["owners", String(ownerId), "documents"],
  renters: (ownerId) => ["owners", String(ownerId), "renters"],
  renterDocuments: (renterId) => ["renters", String(renterId), "documents"],
  addresses: (ownerId) => ["owners", String(ownerId), "addresses"],
  contracts: (ownerId) => ["owners", String(ownerId), "contracts"],
  revenueTimeline: (ownerId, range) => [
    "owners",
    String(ownerId),
    "revenue-timeline",
    range,
  ],
  revenueSummary: (ownerId, range) => [
    "owners",
    String(ownerId),
    "revenue-timeline",
    "summary",
    range,
  ],
};