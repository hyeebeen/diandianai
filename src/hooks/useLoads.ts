import { useState, useEffect } from 'react'
import { supabase } from '@/integrations/supabase/client'
import { Load, LoadStatus } from '@/types/logistics'

export function useLoads() {
  const [loads, setLoads] = useState<Load[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchLoads = async () => {
    try {
      setLoading(true)
      const { data, error } = await supabase
        .from('loads')
        .select('*')
        .order('created_at', { ascending: false })

      if (error) throw error

      const transformedLoads: Load[] = data.map(load => ({
        id: load.id,
        origin: load.origin_city,
        destination: load.destination_city,
        status: load.status as LoadStatus,
        date: load.date,
        customer: load.customer,
        mode: '公路运输',
        equipment: load.vehicle,
        weight: load.weight,
        commodity: load.cargo_type,
        packingType: '标准包装',
        pickupCoords: [load.pickup_lat, load.pickup_lng] as [number, number],
        deliveryCoords: [load.delivery_lat, load.delivery_lng] as [number, number],
        notes: load.loading_notes || '',
        stops: [
          {
            id: `${load.id}_pickup`,
            type: 'pickup' as const,
            address: load.pickup_address,
            city: load.origin_city,
            state: '',
            zipCode: '',
            date: load.date,
            timeWindow: '08:00-10:00',
            coordinates: [load.pickup_lat, load.pickup_lng] as [number, number]
          },
          {
            id: `${load.id}_delivery`,
            type: 'delivery' as const,
            address: load.delivery_address,
            city: load.destination_city,
            state: '',
            zipCode: '',
            date: load.date,
            timeWindow: '16:00-18:00',
            coordinates: [load.delivery_lat, load.delivery_lng] as [number, number]
          }
        ]
      }))

      setLoads(transformedLoads)
    } catch (err) {
      setError(err instanceof Error ? err.message : '加载运单数据失败')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchLoads()
  }, [])

  return { loads, loading, error, refetch: fetchLoads }
}