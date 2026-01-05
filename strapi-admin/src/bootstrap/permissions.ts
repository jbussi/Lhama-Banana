/**
 * Configuração de permissões por role
 * Este arquivo é executado no bootstrap do Strapi
 */

export async function setupPermissions(strapi: any) {
  try {
    // Buscar roles existentes usando a API correta do Strapi 5
    const roleService = strapi.service('admin::role');
    
    // Buscar role de admin
    const adminRole = await roleService.findOne({ code: 'strapi-super-admin' });

    if (!adminRole) {
      console.log('⚠️  Role de admin não encontrado. Configure manualmente no painel.');
      return;
    }

    // Lista de Content Types e suas ações
    const contentTypes = [
      'api::categoria.categoria',
      'api::tamanho.tamanho',
      'api::estampa.estampa',
      'api::nome-produto.nome-produto',
      'api::produto.produto',
      'api::imagem-produto.imagem-produto',
      'api::venda.venda',
      'api::item-venda.item-venda',
      'api::venda-status-historico.venda-status-historico',
      'api::usuario.usuario',
      'api::endereco.endereco',
      'api::cupom.cupom',
      'api::cupom-usado.cupom-usado',
      'api::pagamento.pagamento',
      'api::pagamento-status-historico.pagamento-status-historico',
      'api::etiqueta-frete.etiqueta-frete',
      'api::configuracao.configuracao',
    ];

    const actions = ['create', 'read', 'update', 'delete'];

    // Usar strapi.db.query para buscar e criar permissões (API correta do Strapi 5)
    const permissionQuery = strapi.db.query('admin::permission');

    // Garantir permissões para admin
    for (const contentType of contentTypes) {
      for (const action of actions) {
        try {
          const actionName = `${contentType}.${action}`;
          
          // Verificar se a permissão já existe
          const existingPermission = await permissionQuery.findOne({
            where: {
              action: actionName,
              role: { id: adminRole.id },
            },
          });

          if (!existingPermission) {
            await permissionQuery.create({
              data: {
                action: actionName,
                role: adminRole.id,
              },
            });
          }
        } catch (error: any) {
          // Ignorar erros de permissão já existente
          if (!error.message?.includes('already exists') && !error.message?.includes('duplicate')) {
            console.error(`Erro ao criar permissão ${contentType}.${action}:`, error.message);
          }
        }
      }
    }

    // Permissão para o plugin de frete
    try {
      const actionName = 'plugin::frete-management.read';
      const existingFretePermission = await permissionQuery.findOne({
        where: {
          action: actionName,
          role: { id: adminRole.id },
        },
      });

      if (!existingFretePermission) {
        await permissionQuery.create({
          data: {
            action: actionName,
            role: adminRole.id,
          },
        });
      }
    } catch (error: any) {
      if (!error.message?.includes('already exists') && !error.message?.includes('duplicate')) {
        console.error('Erro ao criar permissão do plugin frete-management:', error.message);
      }
    }

    console.log('✅ Permissões configuradas com sucesso');
  } catch (error: any) {
    console.error('❌ Erro ao configurar permissões:', error.message);
  }
}




