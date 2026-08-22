import type { Context } from '@deepseek-ai/cordis'
import { defineTool } from '@deepseek-ai/dsh-tools'

export const name = 'editorial-brief-gate'
export const inject = ['tools']

const REQUIRED_LANES = ['topology', 'state', 'handoff'] as const
type Lane = typeof REQUIRED_LANES[number]

function isHttpUrl(value: string): boolean {
  try {
    const url = new URL(value)
    return url.protocol === 'http:' || url.protocol === 'https:'
  } catch {
    return false
  }
}

export function apply(ctx: Context): void {
  ctx.tools.register(defineTool({
    name: 'brief_gate',
    description: 'Check whether research cards cover topology, state, and handoff exactly once with traceable sources.',
    parameters: {
      cards: {
        type: 'array',
        required: true,
        description: 'The complete set of research cards returned by delegated workers.',
        items: {
          type: 'object',
          additionalProperties: false,
          properties: {
            worker_id: { type: 'string', required: true },
            lane: {
              type: 'string',
              required: true,
              enum: [...REQUIRED_LANES],
            },
            claim: { type: 'string', required: true },
            source_id: { type: 'string', required: true },
            source_url: { type: 'string', required: true },
          },
        },
      },
    },
    output: {
      schema: {
        type: 'object',
        additionalProperties: false,
        properties: {
          accepted: { type: 'boolean', required: true },
          coverage: { type: 'integer', required: true },
          duplicate_lanes: {
            type: 'array',
            required: true,
            items: { type: 'string', enum: [...REQUIRED_LANES] },
          },
          missing_lanes: {
            type: 'array',
            required: true,
            items: { type: 'string', enum: [...REQUIRED_LANES] },
          },
          invalid_workers: {
            type: 'array',
            required: true,
            items: { type: 'string' },
          },
        },
      },
      render: (_args, value) => [{ type: 'text', text: JSON.stringify(value, null, 2) }],
    },
    async execute(args) {
      const counts = new Map<Lane, number>(REQUIRED_LANES.map(lane => [lane, 0]))
      const invalidWorkers: string[] = []

      for (const card of args.cards) {
        counts.set(card.lane, (counts.get(card.lane) ?? 0) + 1)
        if (
          card.worker_id.trim().length === 0
          || card.claim.trim().length === 0
          || card.source_id.trim().length === 0
          || !isHttpUrl(card.source_url)
        ) {
          invalidWorkers.push(card.worker_id || '<missing-worker>')
        }
      }

      const missingLanes = REQUIRED_LANES.filter(lane => counts.get(lane) === 0)
      const duplicateLanes = REQUIRED_LANES.filter(lane => (counts.get(lane) ?? 0) > 1)
      return {
        accepted: missingLanes.length === 0 && duplicateLanes.length === 0 && invalidWorkers.length === 0,
        coverage: REQUIRED_LANES.length - missingLanes.length,
        duplicate_lanes: duplicateLanes,
        missing_lanes: missingLanes,
        invalid_workers: invalidWorkers,
      }
    },
  }))
}
