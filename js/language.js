// Language Mode Toggle Functionality
document.addEventListener('DOMContentLoaded', () => {
    // Translations object
    const translations = {
        es: {
            // Navigation
            nav: {
                inicio: 'Inicio',
                dashboard: 'Dashboard',
                noticias: 'Noticias',
                reglas: 'Reglas',
                account: 'Account'
            },
            // Hero Section
            hero: {
                title: 'Tu Asesor Financiero con IA:',
                titleHighlight: 'Inteligencia que Impulsa',
                titleEnd: 'tus Inversiones',
                description: 'Recibe alertas personalizadas por email y resúmenes de mercado adaptados a ti.',
                login: 'Iniciar Sesión',
                register: 'Registrarse',
                noCard: 'No se requiere tarjeta de crédito.'
            },
            // Features Section
            features: {
                title: 'Inteligencia que trabaja para ti',
                alertas: {
                    title: 'Alertas Personalizadas',
                    description: 'Recibe notificaciones inteligentes sobre movimientos importantes en tus activos favoritos.'
                },
                resumenes: {
                    title: 'Resúmenes Diarios',
                    description: 'Análisis del mercado adaptados a tu perfil de inversión, directo en tu email.'
                },
                analisis: {
                    title: 'Análisis Avanzado',
                    description: 'Métricas y análisis profundos impulsados por IA para decisiones más informadas.'
                }
            },
            // Pricing Section
            pricing: {
                title: '💰 Planes y Precios',
                subtitle: 'Elige el plan perfecto para tus necesidades de inversión',
                basic: {
                    name: 'Plan Básico',
                    price: 'Gratis',
                    features: {
                        dashboard: 'Dashboard básico',
                        assets: 'Seguimiento de hasta 10 activos personalizados',
                        alerts: 'Alertas por email',
                        rules: '3 reglas máximo',
                        summary: 'Resumen general (blog)',
                        ai: 'Asistente de IA'
                    },
                    cta: 'Empezar Gratis'
                },
                plus: {
                    name: 'Plan Plus',
                    price: '$9.99',
                    period: '/mes',
                    badge: 'Más Popular',
                    features: {
                        all: 'Todo del Plan Básico',
                        unlimited: 'Seguimiento ilimitado',
                        telegram: 'Alertas por Telegram',
                        rules: '8 reglas máximo',
                        indicators: '+ 25 indicadores técnicos',
                        summaries: 'Resúmenes personalizados',
                        ai: 'Asistente de IA con la configuración de reglas'
                    },
                    cta: 'Comenzar Ahora'
                },
                pro: {
                    name: 'Plan Pro',
                    price: '$19.99',
                    period: '/mes',
                    features: {
                        all: 'Todo del Plan Plus',
                        unlimited: 'Reglas ilimitadas',
                        broker: 'Integración con tu broker (coming soon)',
                        summaries: 'Resúmenes personalizados diarios + semanales',
                        ai: 'Asistente de IA con tus listas de activos',
                        support: 'Soporte prioritario (enviame un Whatsapp)'
                    },
                    cta: 'Conviertete en Pro'
                }
            },
            // Footer
            footer: {
                copyright: '© 2025'
            }
        },
        en: {
            // Navigation
            nav: {
                inicio: 'Home',
                dashboard: 'Dashboard',
                noticias: 'News',
                reglas: 'Rules',
                account: 'Account'
            },
            // Hero Section
            hero: {
                title: 'Your AI Financial Advisor:',
                titleHighlight: 'Intelligence that Drives',
                titleEnd: 'your Investments',
                description: 'Receive personalized email alerts and market summaries tailored to you.',
                login: 'Sign In',
                register: 'Sign Up',
                noCard: 'No credit card required.'
            },
            // Features Section
            features: {
                title: 'Intelligence that works for you',
                alertas: {
                    title: 'Personalized Alerts',
                    description: 'Receive intelligent notifications about important movements in your favorite assets.'
                },
                resumenes: {
                    title: 'Daily Summaries',
                    description: 'Market analysis tailored to your investment profile, straight to your email.'
                },
                analisis: {
                    title: 'Advanced Analysis',
                    description: 'Deep metrics and analysis powered by AI for more informed decisions.'
                }
            },
            // Pricing Section
            pricing: {
                title: '💰 Plans and Pricing',
                subtitle: 'Choose the perfect plan for your investment needs',
                basic: {
                    name: 'Basic Plan',
                    price: 'Free',
                    features: {
                        dashboard: 'Basic dashboard',
                        assets: 'Track up to 10 custom assets',
                        alerts: 'Email alerts',
                        rules: 'Maximum 3 rules',
                        summary: 'General summary (blog)',
                        ai: 'AI Assistant'
                    },
                    cta: 'Start Free'
                },
                plus: {
                    name: 'Plus Plan',
                    price: '$9.99',
                    period: '/month',
                    badge: 'Most Popular',
                    features: {
                        all: 'Everything in Basic Plan',
                        unlimited: 'Unlimited tracking',
                        telegram: 'Telegram alerts',
                        rules: 'Maximum 8 rules',
                        indicators: '+ 25 technical indicators',
                        summaries: 'Personalized summaries',
                        ai: 'AI Assistant with rule configuration'
                    },
                    cta: 'Get Started Now'
                },
                pro: {
                    name: 'Pro Plan',
                    price: '$19.99',
                    period: '/month',
                    features: {
                        all: 'Everything in Plus Plan',
                        unlimited: 'Unlimited rules',
                        broker: 'Broker integration (coming soon)',
                        summaries: 'Daily + weekly personalized summaries',
                        ai: 'AI Assistant with your asset lists',
                        support: 'Priority support (send me a WhatsApp)'
                    },
                    cta: 'Become Pro'
                }
            },
            // Footer
            footer: {
                copyright: '© 2025'
            }
        },
        pt: {
            // Navigation
            nav: {
                inicio: 'Início',
                dashboard: 'Dashboard',
                noticias: 'Notícias',
                reglas: 'Regras',
                account: 'Conta'
            },
            // Hero Section
            hero: {
                title: 'Seu Consultor Financeiro com IA:',
                titleHighlight: 'Inteligência que Impulsiona',
                titleEnd: 'seus Investimentos',
                description: 'Receba alertas personalizados por e-mail e resumos de mercado adaptados a você.',
                login: 'Entrar',
                register: 'Cadastrar',
                noCard: 'Não é necessário cartão de crédito.'
            },
            // Features Section
            features: {
                title: 'Inteligência que trabalha para você',
                alertas: {
                    title: 'Alertas Personalizados',
                    description: 'Receba notificações inteligentes sobre movimentos importantes em seus ativos favoritos.'
                },
                resumenes: {
                    title: 'Resumos Diários',
                    description: 'Análises de mercado adaptadas ao seu perfil de investimento, direto no seu e-mail.'
                },
                analisis: {
                    title: 'Análise Avançada',
                    description: 'Métricas e análises profundas impulsionadas por IA para decisões mais informadas.'
                }
            },
            // Pricing Section
            pricing: {
                title: '💰 Planos e Preços',
                subtitle: 'Escolha o plano perfeito para suas necessidades de investimento',
                basic: {
                    name: 'Plano Básico',
                    price: 'Grátis',
                    features: {
                        dashboard: 'Dashboard básico',
                        assets: 'Acompanhamento de até 10 ativos personalizados',
                        alerts: 'Alertas por e-mail',
                        rules: 'Máximo de 3 regras',
                        summary: 'Resumo geral (blog)',
                        ai: 'Assistente de IA'
                    },
                    cta: 'Começar Grátis'
                },
                plus: {
                    name: 'Plano Plus',
                    price: '$9.99',
                    period: '/mês',
                    badge: 'Mais Popular',
                    features: {
                        all: 'Tudo do Plano Básico',
                        unlimited: 'Acompanhamento ilimitado',
                        telegram: 'Alertas por Telegram',
                        rules: 'Máximo de 8 regras',
                        indicators: '+ 25 indicadores técnicos',
                        summaries: 'Resumos personalizados',
                        ai: 'Assistente de IA com configuração de regras'
                    },
                    cta: 'Começar Agora'
                },
                pro: {
                    name: 'Plano Pro',
                    price: '$19.99',
                    period: '/mês',
                    features: {
                        all: 'Tudo do Plano Plus',
                        unlimited: 'Regras ilimitadas',
                        broker: 'Integração com seu corretor (em breve)',
                        summaries: 'Resumos personalizados diários + semanais',
                        ai: 'Assistente de IA com suas listas de ativos',
                        support: 'Suporte prioritário (envie-me um WhatsApp)'
                    },
                    cta: 'Torne-se Pro'
                }
            },
            // Footer
            footer: {
                copyright: '© 2025'
            }
        }
    };

    // Get saved language preference or default to Spanish
    const savedLang = localStorage.getItem('language') || 'es';
    
    // Apply language on load
    applyLanguage(savedLang);

    // Language button event listeners
    const langButtons = document.querySelectorAll('.lang-btn');
    langButtons.forEach(button => {
        button.addEventListener('click', () => {
            const lang = button.getAttribute('data-lang');
            applyLanguage(lang);
            localStorage.setItem('language', lang);
            
            // Update active button style
            langButtons.forEach(btn => {
                btn.classList.remove('bg-green-500', 'text-white', 'font-semibold');
                btn.classList.add('text-gray-600', 'dark:text-gray-400');
            });
            button.classList.remove('text-gray-600', 'dark:text-gray-400');
            button.classList.add('bg-green-500', 'text-white', 'font-semibold');
        });
    });

    // Set initial active button
    const activeButton = document.querySelector(`.lang-btn[data-lang="${savedLang}"]`);
    if (activeButton) {
        activeButton.classList.remove('text-gray-600', 'dark:text-gray-400');
        activeButton.classList.add('bg-green-500', 'text-white', 'font-semibold');
    }

    // Function to apply language
    function applyLanguage(lang) {
        const t = translations[lang];
        if (!t) return;

        // Update HTML lang attribute
        document.documentElement.setAttribute('lang', lang);

        // Update navigation
        const navLinks = {
            inicio: document.querySelector('a[href="index.html"]'),
            dashboard: document.querySelector('a[href="dashboard.html"]'),
            noticias: document.querySelector('a[href="news.html"]'),
            reglas: document.querySelector('a[href="rules.html"]'),
            account: document.querySelector('a[href="account.html"]')
        };

        if (navLinks.inicio) navLinks.inicio.textContent = t.nav.inicio;
        if (navLinks.dashboard) navLinks.dashboard.textContent = t.nav.dashboard;
        if (navLinks.noticias) navLinks.noticias.textContent = t.nav.noticias;
        if (navLinks.reglas) navLinks.reglas.textContent = t.nav.reglas;
        if (navLinks.account) navLinks.account.textContent = t.nav.account;

        // Update hero section - more robust selector
        const heroSection = document.querySelector('section.pt-24');
        if (heroSection) {
            const heroTitle = heroSection.querySelector('h1.text-5xl, h1.text-6xl');
            if (heroTitle) {
                heroTitle.innerHTML = `${t.hero.title} <span class="bg-gradient-to-r from-green-500 to-green-600 bg-clip-text text-transparent">${t.hero.titleHighlight}</span> ${t.hero.titleEnd}`;
            }

            const heroDescription = heroSection.querySelector('p.text-xl');
            if (heroDescription) {
                heroDescription.textContent = t.hero.description;
            }

            // Update login/register buttons
            const loginButtons = heroSection.querySelectorAll('a[href="login.html"]');
            if (loginButtons.length >= 2) {
                // First button is login (green gradient)
                if (loginButtons[0]) loginButtons[0].textContent = t.hero.login;
                // Second button is register (outlined)
                if (loginButtons[1]) loginButtons[1].textContent = t.hero.register;
            }

            // Update "no credit card" text
            const noCardText = heroSection.querySelector('p.text-sm');
            if (noCardText) {
                noCardText.textContent = t.hero.noCard;
            }
        }

        // Update features section
        const featuresSection = document.querySelector('section.bg-white.dark\\:bg-gray-800');
        if (featuresSection) {
            const featuresTitle = featuresSection.querySelector('h2');
            if (featuresTitle) {
                featuresTitle.textContent = t.features.title;
            }

            // Update feature cards
            const featureCards = featuresSection.querySelectorAll('.grid > div');
            if (featureCards.length >= 3) {
                // First card - Alertas
                const card1Title = featureCards[0].querySelector('h3');
                const card1Desc = featureCards[0].querySelector('p.text-gray-600, p.dark\\:text-gray-300');
                if (card1Title) card1Title.textContent = t.features.alertas.title;
                if (card1Desc) card1Desc.textContent = t.features.alertas.description;

                // Second card - Resúmenes
                const card2Title = featureCards[1].querySelector('h3');
                const card2Desc = featureCards[1].querySelector('p.text-gray-600, p.dark\\:text-gray-300');
                if (card2Title) card2Title.textContent = t.features.resumenes.title;
                if (card2Desc) card2Desc.textContent = t.features.resumenes.description;

                // Third card - Análisis
                const card3Title = featureCards[2].querySelector('h3');
                const card3Desc = featureCards[2].querySelector('p.text-gray-600, p.dark\\:text-gray-300');
                if (card3Title) card3Title.textContent = t.features.analisis.title;
                if (card3Desc) card3Desc.textContent = t.features.analisis.description;
            }
        }

        // Update pricing section
        const pricingSection = document.querySelector('#pricing');
        if (pricingSection) {
            const pricingTitle = pricingSection.querySelector('h2');
            if (pricingTitle) pricingTitle.textContent = t.pricing.title;

            const pricingSubtitle = pricingSection.querySelector('p.text-xl');
            if (pricingSubtitle) pricingSubtitle.textContent = t.pricing.subtitle;

            // Get all plan cards
            const allPlans = pricingSection.querySelectorAll('.rounded-2xl');
            
            // Update Basic Plan (first card, not green gradient)
            const basicPlan = Array.from(allPlans).find(plan => 
                !plan.classList.contains('from-green-500') && 
                plan.querySelector('h3') && 
                (plan.querySelector('h3').textContent.includes('Básico') || 
                 plan.querySelector('h3').textContent.includes('Basic') ||
                 plan.querySelector('h3').textContent.includes('Básico') ||
                 plan.querySelector('h3').textContent.includes('Gratis') ||
                 plan.querySelector('h3').textContent.includes('Free') ||
                 plan.querySelector('h3').textContent.includes('Grátis'))
            );
            
            if (basicPlan) {
                const basicTitle = basicPlan.querySelector('h3');
                const basicPrice = basicPlan.querySelector('.text-4xl');
                if (basicTitle) basicTitle.textContent = t.pricing.basic.name;
                if (basicPrice) basicPrice.textContent = t.pricing.basic.price;

                const basicFeatures = basicPlan.querySelectorAll('li');
                if (basicFeatures.length >= 6) {
                    basicFeatures[0].innerHTML = `✅ ${t.pricing.basic.features.dashboard}`;
                    basicFeatures[1].innerHTML = `✅ ${t.pricing.basic.features.assets}`;
                    basicFeatures[2].innerHTML = `✅ ${t.pricing.basic.features.alerts}`;
                    basicFeatures[3].innerHTML = `✅ ${t.pricing.basic.features.rules}`;
                    basicFeatures[4].innerHTML = `✅ ${t.pricing.basic.features.summary}`;
                    basicFeatures[5].innerHTML = `❌ ${t.pricing.basic.features.ai}`;
                }

                const basicCTA = basicPlan.querySelector('a');
                if (basicCTA) basicCTA.textContent = t.pricing.basic.cta;
            }

            // Update Plus Plan (green gradient card)
            const plusPlan = pricingSection.querySelector('.bg-gradient-to-br.from-green-500');
            if (plusPlan) {
                const plusBadge = plusPlan.querySelector('.bg-yellow-400');
                if (plusBadge) plusBadge.textContent = t.pricing.plus.badge;

                const plusTitle = plusPlan.querySelector('h3');
                const plusPrice = plusPlan.querySelector('.text-4xl');
                if (plusTitle) plusTitle.textContent = t.pricing.plus.name;
                if (plusPrice) plusPrice.innerHTML = `${t.pricing.plus.price}<span class="text-lg font-normal">${t.pricing.plus.period}</span>`;

                const plusFeatures = plusPlan.querySelectorAll('li');
                if (plusFeatures.length >= 7) {
                    plusFeatures[0].innerHTML = `✅ ${t.pricing.plus.features.all}`;
                    plusFeatures[1].innerHTML = `✅ ${t.pricing.plus.features.unlimited}`;
                    plusFeatures[2].innerHTML = `✅ ${t.pricing.plus.features.telegram}`;
                    plusFeatures[3].innerHTML = `✅ ${t.pricing.plus.features.rules}`;
                    plusFeatures[4].innerHTML = `✅ ${t.pricing.plus.features.indicators}`;
                    plusFeatures[5].innerHTML = `✅ ${t.pricing.plus.features.summaries}`;
                    plusFeatures[6].innerHTML = `✅ ${t.pricing.plus.features.ai}`;
                }

                const plusCTA = plusPlan.querySelector('button');
                if (plusCTA) plusCTA.textContent = t.pricing.plus.cta;
            }

            // Update Pro Plan (last card, not green gradient)
            const proPlan = Array.from(allPlans).find(plan => 
                !plan.classList.contains('from-green-500') && 
                plan !== basicPlan &&
                plan.querySelector('h3') &&
                (plan.querySelector('h3').textContent.includes('Pro') ||
                 plan.querySelector('h3').textContent.includes('$19.99'))
            );
            
            if (proPlan) {
                const proTitle = proPlan.querySelector('h3');
                const proPrice = proPlan.querySelector('.text-4xl');
                if (proTitle) proTitle.textContent = t.pricing.pro.name;
                if (proPrice) proPrice.innerHTML = `${t.pricing.pro.price}<span class="text-lg font-normal">${t.pricing.pro.period}</span>`;

                const proFeatures = proPlan.querySelectorAll('li');
                if (proFeatures.length >= 6) {
                    proFeatures[0].innerHTML = `✅ ${t.pricing.pro.features.all}`;
                    proFeatures[1].innerHTML = `✅ ${t.pricing.pro.features.unlimited}`;
                    proFeatures[2].innerHTML = `✅ ${t.pricing.pro.features.broker}`;
                    proFeatures[3].innerHTML = `✅ ${t.pricing.pro.features.summaries}`;
                    proFeatures[4].innerHTML = `✅ ${t.pricing.pro.features.ai}`;
                    proFeatures[5].innerHTML = `✅ ${t.pricing.pro.features.support}`;
                }

                const proCTA = proPlan.querySelector('button');
                if (proCTA) proCTA.textContent = t.pricing.pro.cta;
            }
        }

        // Update footer
        const footerText = document.querySelector('footer p');
        if (footerText) {
            footerText.innerHTML = `${t.footer.copyright} <span class="font-semibold text-green-500">BullAnalytics</span>.`;
        }
    }
});

