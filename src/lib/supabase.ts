import { createClient } from '@supabase/supabase-js'

const supabaseUrl = 'https://your-project.supabase.co'
const supabaseAnonKey = 'your-anon-key'

export const supabase = createClient(supabaseUrl, supabaseAnonKey)

export type Database = {
  public: {
    Tables: {
      loads: {
        Row: {
          id: string
          origin_city: string
          destination_city: string
          status: string
          date: string
          customer: string
          vehicle: string
          driver: string
          weight: string
          cargo_type: string
          temperature_control: string | null
          loading_notes: string | null
          pickup_address: string
          pickup_lat: number
          pickup_lng: number
          delivery_address: string
          delivery_lat: number
          delivery_lng: number
          created_at: string
          updated_at: string
        }
        Insert: {
          id?: string
          origin_city: string
          destination_city: string
          status: string
          date: string
          customer: string
          vehicle: string
          driver: string
          weight: string
          cargo_type: string
          temperature_control?: string | null
          loading_notes?: string | null
          pickup_address: string
          pickup_lat: number
          pickup_lng: number
          delivery_address: string
          delivery_lat: number
          delivery_lng: number
          created_at?: string
          updated_at?: string
        }
        Update: {
          id?: string
          origin_city?: string
          destination_city?: string
          status?: string
          date?: string
          customer?: string
          vehicle?: string
          driver?: string
          weight?: string
          cargo_type?: string
          temperature_control?: string | null
          loading_notes?: string | null
          pickup_address?: string
          pickup_lat?: number
          pickup_lng?: number
          delivery_address?: string
          delivery_lat?: number
          delivery_lng?: number
          created_at?: string
          updated_at?: string
        }
      }
      chat_messages: {
        Row: {
          id: string
          load_id: string
          role: 'human' | 'agent' | 'system'
          content: string
          timestamp: string
          created_at: string
        }
        Insert: {
          id?: string
          load_id: string
          role: 'human' | 'agent' | 'system'
          content: string
          timestamp?: string
          created_at?: string
        }
        Update: {
          id?: string
          load_id?: string
          role?: 'human' | 'agent' | 'system'
          content?: string
          timestamp?: string
          created_at?: string
        }
      }
    }
  }
}