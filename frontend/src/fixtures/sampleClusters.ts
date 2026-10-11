/**
 * Sample cluster telemetry fixtures for unit testing and offline development (T-054).
 * Strictly labelled test fixtures per agents.md Standing Rule 11.
 */
import type { Cluster } from '../types/api'

export const SAMPLE_CLUSTERS: Cluster[] = [
  {
    clusterId: 'cl-pb-01',
    lat: 30.91,
    lon: 75.85,
    count: 14,
    totalFrp: 620.5,
    maxFrp: 185.0,
    firstSeenUtc: '2026-10-11T06:30:00Z',
    lastSeenUtc: '2026-10-11T09:45:00Z',
    windSpeedKmh: 14.2,
    windDirDeg: 310, // NW wind towards Delhi
  },
  {
    clusterId: 'cl-pb-02',
    lat: 30.34,
    lon: 76.38,
    count: 8,
    totalFrp: 280.0,
    maxFrp: 92.4,
    firstSeenUtc: '2026-10-11T07:10:00Z',
    lastSeenUtc: '2026-10-11T10:15:00Z',
    windSpeedKmh: 11.8,
    windDirDeg: 295,
  },
  {
    clusterId: 'cl-hr-01',
    lat: 29.69,
    lon: 76.99,
    count: 3,
    totalFrp: 75.2,
    maxFrp: 38.0,
    firstSeenUtc: '2026-10-11T08:00:00Z',
    lastSeenUtc: '2026-10-11T09:20:00Z',
    windSpeedKmh: 9.5,
    windDirDeg: 320,
  },
  {
    clusterId: 'cl-pb-03',
    lat: 31.32,
    lon: 75.58,
    count: 19,
    totalFrp: 890.3,
    maxFrp: 240.1,
    firstSeenUtc: '2026-10-11T05:45:00Z',
    lastSeenUtc: '2026-10-11T10:30:00Z',
    windSpeedKmh: 16.0,
    windDirDeg: 305,
  },
  {
    clusterId: 'cl-hr-02',
    lat: 29.15,
    lon: 75.70,
    count: 4,
    totalFrp: 110.0,
    maxFrp: 45.0,
    firstSeenUtc: '2026-10-11T08:30:00Z',
    lastSeenUtc: '2026-10-11T09:50:00Z',
    windSpeedKmh: 8.2,
    windDirDeg: 290,
  },
]
