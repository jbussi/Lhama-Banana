/**
 * Customizações do painel admin
 * Cores da marca LhamaBanana: Turquesa (#40e0d0) e Amarelo (#FFE135)
 * Aplicadas em TODO o painel administrativo
 */

export const customizations = {
  // Desabilitar tutoriais
  tutorials: false,
  
  // Desabilitar notificações desnecessárias
  notifications: {
    releases: false,
    // Remover todas as notificações de atualização e promoções
  },
  
  // Configurações de tema com cores da marca LhamaBanana aplicadas em TODO o painel
  theme: {
    light: {
      colors: {
        // Cores principais baseadas na marca
        primary100: '#e6faf8', // Turquesa muito claro
        primary200: '#b3f0e8', // Turquesa claro
        primary500: '#40e0d0', // Turquesa principal da marca
        primary600: '#36d1c4', // Turquesa escuro
        primary700: '#2bb3a8', // Turquesa mais escuro
        secondary100: '#fff9e6', // Amarelo muito claro
        secondary200: '#fff3b3', // Amarelo claro
        secondary500: '#FFE135', // Amarelo principal da marca
        secondary600: '#ffd700', // Amarelo escuro
        danger700: '#b72b1a',
        success500: '#40e0d0', // Usar turquesa para sucesso
        warning500: '#FFE135', // Usar amarelo para avisos
        // Cores adicionais para aplicar em todo o painel
        neutral0: '#FFFFFF',
        neutral100: '#f6f6f9',
        neutral200: '#eaeaef',
        neutral500: '#8e8ea9',
        neutral600: '#6b6b7f',
        neutral700: '#494950',
        neutral800: '#32324d',
        neutral900: '#212134',
      },
    },
    dark: {
      colors: {
        // Versão dark mantendo identidade da marca
        primary100: '#e6faf8',
        primary200: '#b3f0e8',
        primary500: '#40e0d0',
        primary600: '#36d1c4',
        primary700: '#2bb3a8',
        secondary100: '#fff9e6',
        secondary200: '#fff3b3',
        secondary500: '#FFE135',
        secondary600: '#ffd700',
        danger700: '#b72b1a',
        success500: '#40e0d0',
        warning500: '#FFE135',
        neutral0: '#0c0d0e',
        neutral100: '#1c1d24',
        neutral200: '#2a2d3a',
        neutral500: '#8e8ea9',
        neutral600: '#a5a5ba',
        neutral700: '#c0c0d1',
        neutral800: '#dcdce4',
        neutral900: '#ffffff',
      },
    },
  },
};
