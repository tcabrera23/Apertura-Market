import { Vexor } from 'npm:vexor'
import { createClient } from 'npm:@supabase/supabase-js'

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
}

// Función para obtener la tasa de cambio USD → ARS
async function getExchangeRate(): Promise<number> {
  try {
    // Usar API gratuita para obtener tasa de cambio
    const response = await fetch('https://api.exchangerate-api.com/v4/latest/USD')
    const data = await response.json()
    
    // Retornar tasa ARS, con fallback a 1000 si falla
    return data.rates?.ARS || 1000
  } catch (error) {
    console.error('Error obteniendo tasa de cambio, usando fallback:', error)
    // Fallback: tasa aproximada si falla la API
    return 1000
  }
}

Deno.serve(async (req) => {
  // Handle CORS
  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers: corsHeaders })
  }

  try {
    const { plan_name, platform, user_id, coupon_code } = await req.json()
    
    // Initialize Vexor
    const vexor = new Vexor({
      publishableKey: Deno.env.get('VEXOR_PUBLISHABLE_KEY')!,
      projectId: Deno.env.get('VEXOR_PROJECT_ID')!,
      secretKey: Deno.env.get('VEXOR_SECRET_KEY')!,
    })

    // Initialize Supabase Admin Client
    const supabaseClient = createClient(
      Deno.env.get('SUPABASE_URL') ?? '',
      Deno.env.get('SUPABASE_SERVICE_ROLE_KEY') ?? ''
    )

    // 1. Obtener detalles del plan desde Supabase
    const { data: plan, error: planError } = await supabaseClient
      .from('subscription_plans')
      .select('*')
      .eq('name', plan_name)
      .single()

    if (planError || !plan) {
      throw new Error(`Plan ${plan_name} no encontrado en la base de datos.`)
    }

    // 2. Obtener información del usuario para el email
    const { data: user, error: userError } = await supabaseClient
      .from('user_profiles')
      .select('email')
      .eq('id', user_id)
      .single()

    if (userError || !user) {
      throw new Error(`Usuario ${user_id} no encontrado.`)
    }

    // 3. Determinar moneda y precio según la plataforma
    let currency = 'USD'
    let finalPrice = parseFloat(plan.price)
    
    // Mercado Pago: siempre en ARS (pesos argentinos)
    // PayPal: siempre en USD
    if (platform === 'mercadopago') {
      currency = 'ARS'
      // Convertir USD a ARS (obtener tasa de cambio actual)
      const exchangeRate = await getExchangeRate()
      finalPrice = Math.round(parseFloat(plan.price) * exchangeRate) // Redondear a entero para ARS
    }

    // 4. Construir el objeto de suscripción según la documentación de Vexor
    // Vexor crea el plan dinámicamente en el proveedor
    const subscriptionBody = {
      name: plan.display_name || `Plan ${plan.name}`,
      description: plan.description || `Suscripción ${plan.name}`,
      interval: plan.billing_interval, // 'month' o 'year'
      price: finalPrice,
      currency: currency,
      successRedirect: `${Deno.env.get('FRONTEND_URL')}/subscription-success.html`,
      failureRedirect: `${Deno.env.get('FRONTEND_URL')}/pricing.html`,
      customer: {
        email: user.email,
        name: user.email.split('@')[0] // Nombre básico desde el email
      },
      metadata: {
        user_id: user_id,
        plan_id: plan.id,
        coupon_code: coupon_code || null,
        original_price_usd: plan.price, // Guardar precio original en USD
        currency: currency
      }
    }

    // 5. Crear la suscripción en Vexor (que la crea en PayPal o MercadoPago)
    console.log('Creando suscripción con Vexor:', {
      platform,
      subscriptionBody: {
        ...subscriptionBody,
        price: finalPrice,
        currency: currency
      }
    })
    
    let response
    try {
      if (platform === 'paypal') {
        response = await vexor.subscribe.paypal(subscriptionBody)
      } else if (platform === 'mercadopago') {
        // Para Mercado Pago, asegurarnos de que el precio sea válido (mínimo $10 ARS según MP)
        if (currency === 'ARS' && finalPrice < 10) {
          console.warn(`Precio ${finalPrice} ARS es muy bajo. Mercado Pago requiere mínimo $10 ARS. Ajustando a $10 ARS.`)
          subscriptionBody.price = 10
          finalPrice = 10
        }
        response = await vexor.subscribe.mercadopago(subscriptionBody)
      } else {
        throw new Error(`Plataforma ${platform} no soportada`)
      }
      
      console.log('Respuesta de Vexor:', {
        identifier: response.identifier,
        payment_url: response.payment_url,
        has_payment_url: !!response.payment_url
      })
    } catch (vexorError) {
      console.error('Error de Vexor:', vexorError)
      throw new Error(`Error creando suscripción en Vexor: ${vexorError.message}`)
    }

    // 6. Retornar la URL de checkout de Vexor al frontend
    if (!response.payment_url) {
      console.error('Vexor no retornó payment_url. Respuesta completa:', response)
      throw new Error('Vexor no retornó URL de pago. Verifica la configuración.')
    }
    
    return new Response(
      JSON.stringify({ 
        success: true, 
        approval_url: response.payment_url, // Vexor usa payment_url
        vexor_id: response.identifier,
        currency: currency, // Informar al frontend la moneda usada
        final_price: finalPrice // Informar el precio final
      }),
      { 
        headers: { ...corsHeaders, 'Content-Type': 'application/json' }, 
        status: 200 
      },
    )

  } catch (error) {
    console.error('Error in vexor-payments function:', error)
    return new Response(
      JSON.stringify({ success: false, error: error.message }),
      { 
        headers: { ...corsHeaders, 'Content-Type': 'application/json' }, 
        status: 400 
      },
    )
  }
})
