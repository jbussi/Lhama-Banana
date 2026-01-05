import { Initializer } from './components/Initializer';
import { PluginIcon } from './components/PluginIcon';
import { Truck } from '@strapi/icons';

export default {
  register(app: any) {
    // Registrar o plugin primeiro
    app.registerPlugin({
      id: 'frete-management',
      initializer: Initializer,
      isReady: false,
      name: 'frete-management',
    });

    // Adicionar link no menu - usando API correta do Strapi 5
    app.addMenuLink({
      to: '/plugins/frete-management',
      icon: Truck,
      intlLabel: {
        id: 'frete-management.plugin.name',
        defaultMessage: 'Gestão de Frete',
      },
      Component: () => import('./pages/App'),
      // Remover permissões por enquanto para garantir que apareça
      // permissions: [
      //   {
      //     action: 'plugin::frete-management.read',
      //     subject: null,
      //   },
      // ],
    });
  },

  bootstrap() {},
};




