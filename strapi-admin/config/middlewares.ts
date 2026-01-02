export default [
  'strapi::logger',
  'strapi::errors',
  'strapi::security',
  'strapi::cors',
  'strapi::poweredBy',
  'strapi::query',
  'strapi::body',
  'strapi::session',
  'strapi::favicon',
  'strapi::public',
  // Desabilitado temporariamente para configuração inicial
  // Reative após criar os Content Types
  // {
  //   name: 'global::flask-auth',
  //   config: {},
  // },
];
