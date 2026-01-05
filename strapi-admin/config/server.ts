export default ({ env }) => ({
  host: env('HOST', '0.0.0.0'),
  port: env.int('PORT', 1337),
  app: {
    keys: env.array('APP_KEYS'),
  },
  url: env('PUBLIC_URL', 'http://localhost:1337'),
  proxy: false,
  cron: {
    enabled: false,
  },
  admin: {
    autoOpen: false,
    watchIgnoreFiles: [
      '**/config/sync/**',
    ],
    // Habilitar hot reload em desenvolvimento
    watchAdminFiles: env('NODE_ENV') === 'development',
  },
  // Configurações de desenvolvimento
  dirs: {
    public: env('PUBLIC_DIR', './public'),
  },
});
