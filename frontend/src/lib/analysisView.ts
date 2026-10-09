import type { DealContext } from './contracts';
export type GraphTarget = { kind: 'node' | 'edge'; id: string };

export function explanationGroups(lines: string[]) {
  const groups: Record<'FAKTA' | 'INTERPRETASI' | 'SKENARIO' | 'PENJELASAN', string[]> = { FAKTA: [], INTERPRETASI: [], SKENARIO: [], PENJELASAN: [] };
  for (const line of lines) {
    const prefix = /^(FAKTA|INTERPRETASI|SKENARIO)\s*\|/.exec(line);
    groups[prefix ? prefix[1] as keyof typeof groups : 'PENJELASAN'].push(line);
  }
  return groups; // Keep the entire original text, including its prefix.
}

export function evidenceGraphLinks(context: DealContext, evidenceId: string) {
  const evidence = context.evidence.find(record => record.id === evidenceId);
  if (!evidence) return { node: null, edges: [] };
  const nodes = new Set(context.graph.nodes.map(node => node.id));
  const edges = context.graph.edges.filter(edge => edge.evidence_ids.includes(evidenceId) && nodes.has(edge.source) && nodes.has(edge.target));
  // An exact source ID must also be an endpoint of a citing edge. No guessed aliases.
  const node = context.graph.nodes.find(node => node.id === evidence.source_id
    && edges.some(edge => edge.source === node.id || edge.target === node.id)) ?? null;
  return { node, edges };
}
