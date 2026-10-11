/**
 * Sample city impact telemetry fixtures for unit testing and offline development (T-056).
 * Recorded from deployed API historical test query (2024-11-01).
 * Strictly labelled test fixtures per agents.md Standing Rule 11.
 */
import type { Impact } from '../types/api'

export const SAMPLE_IMPACTS: Impact[] = [
  {
    cityId: 'karnal',
    cityName: 'Karnal',
    nClusters: 41,
    totalFrp: 484.2,
    nearestKm: 47.9,
    minEtaHours: 4.5,
    severity: 'Medium',
    affectedByClusterIds: ['29.7500_76.4000', '29.8000_76.1500'],
  },
  {
    cityId: 'jalandhar',
    cityName: 'Jalandhar',
    nClusters: 25,
    totalFrp: 339.8,
    nearestKm: 19.1,
    minEtaHours: 3.3,
    severity: 'Medium',
    affectedByClusterIds: ['31.1500_74.8500', '31.2000_74.7000'],
  },
  {
    cityId: 'patiala',
    cityName: 'Patiala',
    nClusters: 30,
    totalFrp: 315.8,
    nearestKm: 16.7,
    minEtaHours: 1.7,
    severity: 'Medium',
    affectedByClusterIds: ['30.4000_75.7500', '30.4000_75.8500'],
  },
  {
    cityId: 'ambala',
    cityName: 'Ambala',
    nClusters: 35,
    totalFrp: 314.9,
    nearestKm: 26.3,
    minEtaHours: 2.8,
    severity: 'Medium',
    affectedByClusterIds: ['30.4500_76.2000', '30.4500_76.5000'],
  },
  {
    cityId: 'panipat',
    cityName: 'Panipat',
    nClusters: 19,
    totalFrp: 262.5,
    nearestKm: 44.6,
    minEtaHours: 4.6,
    severity: 'Medium',
    affectedByClusterIds: ['29.6000_76.4000'],
  },
  {
    cityId: 'hisar',
    cityName: 'Hisar',
    nClusters: 16,
    totalFrp: 160.5,
    nearestKm: 61.7,
    minEtaHours: 6.8,
    severity: 'Medium',
    affectedByClusterIds: ['29.5500_75.2500'],
  },
  {
    cityId: 'delhi',
    cityName: 'Delhi',
    nClusters: 4,
    totalFrp: 8.2,
    nearestKm: 33.2,
    minEtaHours: 3.4,
    severity: 'Low',
    affectedByClusterIds: ['28.7000_76.9000'],
  },
]
