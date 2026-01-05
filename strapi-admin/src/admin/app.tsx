import type { StrapiApp } from '@strapi/strapi/admin';

export default {
  config: {
    locales: ['pt-BR'],
    // Desativação oficial de notificações
    tutorials: false,
    notifications: { release: false },
    
    // Sobrescrevendo chaves de tradução
    translations: {
      'pt-BR': {
        'app.components.HomePage.welcome.autosave': ' ',
        'app.components.HomePage.welcome': 'Bem-vindo ao Painel',
        'admin.pages.MarketplacePage.tab.plugins': ' ',
      },
    },
  },

  bootstrap(app: StrapiApp) {
    // Apenas CSS para organizar o menu - sem manipulação de DOM
    if (typeof document !== 'undefined' && document.head) {
      const style = document.createElement('style');
      style.id = 'organize-menu-style';
      style.innerHTML = `
        /* Organiza o menu - esconde itens desnecessários */
        a[href*="/admin/marketplace"],
        a[href*="/admin/plugins"],
        #strapi-marketplace-menu-link,
        a[href*="/admin/settings/releases"],
        a[href*="/admin/settings/deploy"],
        nav a[href*="/admin/settings/audit-logs"],
        nav a[href*="/admin/settings/webhooks"],
        nav a[href*="/admin/settings/transfer-tokens"],
        nav a[href*="/admin/settings/api-tokens"] {
          display: none !important;
        }
      `;
      document.head.appendChild(style);
    }
  },
};