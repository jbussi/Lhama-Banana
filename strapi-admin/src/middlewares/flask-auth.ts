import type { Core } from '@strapi/strapi';
import axios from 'axios';

export default (config: any, { strapi }: { strapi: Core.Strapi }) => {
  return async (ctx: any, next: () => Promise<any>) => {
    // Rotas públicas do Strapi que não precisam autenticação
    const publicRoutes = [
      '/admin/auth',
      '/api/auth',
      '/admin/plugins',
      '/admin/init',
      '/_health',
      '/favicon.ico',
      '/admin/strapi',
      '/admin/strapi/',
    ];

    const isPublicRoute = publicRoutes.some((route) =>
      ctx.request.url.startsWith(route)
    );

    if (isPublicRoute) {
      return next();
    }

    // Verificar se há token de autenticação Flask
    const flaskToken = ctx.request.headers['x-flask-auth-token'];
    const flaskUid = ctx.request.headers['x-flask-uid'];

    if (!flaskToken || !flaskUid) {
      strapi.log.warn('Tentativa de acesso sem token Flask');
      return ctx.unauthorized('Token de autenticação Flask necessário');
    }

    // Validar token com Flask (via API interna)
    try {
      const flaskUrl = process.env.FLASK_URL || 'http://localhost:5000';

      const response = await axios.post(
        `${flaskUrl}/api/admin/validate-strapi-access`,
        {
          uid: flaskUid,
          mfa_verified: true,
        },
        {
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${flaskToken}`,
          },
          timeout: 5000,
        }
      );

      if (response.status !== 200) {
        strapi.log.warn('Validação Flask falhou');
        return ctx.unauthorized('Acesso negado pelo Flask');
      }

      const userData = response.data;

      // Armazenar dados do usuário no contexto
      ctx.state.flaskUser = userData;

      // Verificar se é admin
      if (userData.role !== 'admin') {
        strapi.log.warn(
          `Usuário ${userData.email} tentou acessar sem ser admin`
        );
        return ctx.forbidden('Apenas administradores podem acessar');
      }

      strapi.log.info(`Acesso autorizado para admin: ${userData.email}`);
      return next();
    } catch (error: any) {
      strapi.log.error('Erro ao validar autenticação Flask:', error.message);

      if (error.response) {
        // Resposta do Flask com erro
        return ctx.unauthorized('Acesso negado pelo Flask');
      } else if (error.code === 'ECONNREFUSED') {
        // Flask não está rodando
        strapi.log.error('Flask não está acessível');
        return ctx.serviceUnavailable('Serviço de autenticação indisponível');
      } else {
        return ctx.unauthorized('Erro ao validar autenticação');
      }
    }
  };
};

