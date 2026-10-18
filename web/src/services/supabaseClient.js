import { createClient } from '@supabase/supabase-js'

const url = import.meta.env.VITE_SUPABASE_URL ?? ''
const publishableKey = import.meta.env.VITE_SUPABASE_PUBLISHABLE_KEY ?? ''

/** Sole browser createClient — pages must use authApi / meApi, never this module's SDK import path. */
export const supabase = createClient(url || 'http://127.0.0.1:54321', publishableKey || 'public-anon-key')
