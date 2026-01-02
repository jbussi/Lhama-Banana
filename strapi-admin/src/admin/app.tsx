import type { StrapiApp } from '@strapi/strapi/admin';

export default {
  config: {
    locales: ['pt-BR'],
    // Desabilitar tutoriais e notificações
    tutorials: false,
    notifications: { releases: false },
  },
  bootstrap(app: StrapiApp) {
    // Customização do menu - Strapi 5 tem estrutura diferente
    // O menu já é mais limpo por padrão
    console.log('Strapi Admin inicializado - Interface simplificada');
  },
};

