export default () => ({
  // Desabilitar sistema de usuários padrão (usamos Flask)
  'users-permissions': {
    enabled: false,
  },
  
  // Desabilitar internacionalização se não usar
  'i18n': {
    enabled: false,
  },
  
  // Desabilitar documentação se não precisar
  'documentation': {
    enabled: false,
  },
  
  // Desabilitar plugin de cloud/deploy
  'cloud': {
    enabled: false,
  },
  
  // Desabilitar marketplace se existir
  'marketplace': {
    enabled: false,
  },
});
