export default {
  async beforeDelete(event: any) {
    strapi.log.info('[LIFECYCLE] beforeDelete Categoria - Event recebido:', JSON.stringify(event, null, 2));
    
    const { params, model } = event;
    const { where } = params || {};
    
    strapi.log.info('[LIFECYCLE] beforeDelete Categoria - params:', JSON.stringify(params, null, 2));
    strapi.log.info('[LIFECYCLE] beforeDelete Categoria - where:', JSON.stringify(where, null, 2));
    strapi.log.info('[LIFECYCLE] beforeDelete Categoria - model:', model);
    
    let categoriaId = null;
    
    // Tentar múltiplas formas de obter o ID
    // 1. Tentar via where.id
    if (where && where.id) {
      if (Array.isArray(where.id.$in)) {
        categoriaId = where.id.$in[0];
      } else if (typeof where.id === 'object' && where.id.$eq) {
        categoriaId = where.id.$eq;
      } else if (typeof where.id === 'number') {
        categoriaId = where.id;
      }
      strapi.log.info(`[LIFECYCLE] beforeDelete Categoria - ID extraído de where.id: ${categoriaId}`);
    }
    
    // 2. Tentar via where.documentId
    if (!categoriaId && where && where.documentId) {
      strapi.log.info(`[LIFECYCLE] beforeDelete Categoria - Tentando buscar por documentId: ${where.documentId}`);
      try {
        const categoria = await strapi.db.query('api::categoria.categoria').findOne({
          where: { documentId: where.documentId },
        });
        if (categoria) {
          categoriaId = categoria.id;
          strapi.log.info(`[LIFECYCLE] beforeDelete Categoria - ID encontrado via documentId: ${categoriaId}`);
        } else {
          strapi.log.warn(`[LIFECYCLE] beforeDelete Categoria - Categoria não encontrada com documentId: ${where.documentId}`);
        }
      } catch (error) {
        strapi.log.error('[LIFECYCLE] beforeDelete Categoria - Erro ao buscar por documentId:', error);
      }
    }
    
    // 3. Tentar buscar diretamente se temos um documentId em outro formato
    if (!categoriaId && where) {
      // Tentar buscar todos os campos do where para encontrar o ID
      for (const [key, value] of Object.entries(where)) {
        if (key === 'documentId' && typeof value === 'string') {
          try {
            const categoria = await strapi.db.query('api::categoria.categoria').findOne({
              where: { documentId: value },
            });
            if (categoria) {
              categoriaId = categoria.id;
              strapi.log.info(`[LIFECYCLE] beforeDelete Categoria - ID encontrado via documentId (loop): ${categoriaId}`);
              break;
            }
          } catch (error) {
            strapi.log.error(`[LIFECYCLE] beforeDelete Categoria - Erro ao buscar por ${key}:`, error);
          }
        }
      }
    }
    
    if (!categoriaId) {
      strapi.log.warn('[LIFECYCLE] beforeDelete Categoria - Não foi possível extrair ID de nenhuma forma');
      strapi.log.warn('[LIFECYCLE] beforeDelete Categoria - Estrutura completa do where:', JSON.stringify(where, null, 2));
    }
    
    if (categoriaId) {
      // Verificar se a categoria realmente existe no banco de dados
      try {
        const categoriaExists = await strapi.db.query('api::categoria.categoria').findOne({
          where: { id: categoriaId },
        });
        
        if (!categoriaExists) {
          strapi.log.warn(`[LIFECYCLE] beforeDelete Categoria ${categoriaId} - Categoria não existe no banco de dados (registro órfão). Permitindo exclusão sem limpar referências.`);
          // Retornar sem fazer nada - permite que o Strapi continue com a exclusão
          return;
        }
      } catch (error) {
        strapi.log.error(`[LIFECYCLE] beforeDelete Categoria ${categoriaId} - Erro ao verificar existência:`, error);
        // Continuar mesmo com erro na verificação
      }
      
      strapi.log.info(`[LIFECYCLE] beforeDelete Categoria ${categoriaId} - Categoria existe no banco. Iniciando limpeza de referências`);
      try {
        // Limpar referências nas tabelas de link antes de deletar
        strapi.log.info(`[LIFECYCLE] beforeDelete Categoria ${categoriaId} - Deletando de estampa_categoria_lnk`);
        const result1 = await strapi.db.connection.raw(
          `DELETE FROM estampa_categoria_lnk WHERE categoria_id = $1`,
          [categoriaId]
        );
        strapi.log.info(`[LIFECYCLE] beforeDelete Categoria ${categoriaId} - Resultado estampa_categoria_lnk:`, result1.rowCount);
        
        strapi.log.info(`[LIFECYCLE] beforeDelete Categoria ${categoriaId} - Deletando de nome_produto_categoria_lnk`);
        const result2 = await strapi.db.connection.raw(
          `DELETE FROM nome_produto_categoria_lnk WHERE categoria_id = $1`,
          [categoriaId]
        );
        strapi.log.info(`[LIFECYCLE] beforeDelete Categoria ${categoriaId} - Resultado nome_produto_categoria_lnk:`, result2.rowCount);
        
        // Limpar categoria_id nas colunas diretas (já que temos ON DELETE SET NULL, mas vamos garantir)
        strapi.log.info(`[LIFECYCLE] beforeDelete Categoria ${categoriaId} - Atualizando estampa.categoria_id`);
        const result3 = await strapi.db.connection.raw(
          `UPDATE estampa SET categoria_id = NULL WHERE categoria_id = $1`,
          [categoriaId]
        );
        strapi.log.info(`[LIFECYCLE] beforeDelete Categoria ${categoriaId} - Resultado UPDATE estampa:`, result3.rowCount);
        
        strapi.log.info(`[LIFECYCLE] beforeDelete Categoria ${categoriaId} - Atualizando nome_produto.categoria_id`);
        const result4 = await strapi.db.connection.raw(
          `UPDATE nome_produto SET categoria_id = NULL WHERE categoria_id = $1`,
          [categoriaId]
        );
        strapi.log.info(`[LIFECYCLE] beforeDelete Categoria ${categoriaId} - Resultado UPDATE nome_produto:`, result4.rowCount);
        
        strapi.log.info(`[LIFECYCLE] beforeDelete Categoria ${categoriaId} - Referências limpas com sucesso antes da exclusão`);
      } catch (error) {
        strapi.log.error(`[LIFECYCLE] beforeDelete Categoria ${categoriaId} - Erro ao limpar referências:`, error);
        strapi.log.error(`[LIFECYCLE] beforeDelete Categoria ${categoriaId} - Stack trace:`, error?.stack);
        // Não lançar erro para não bloquear a exclusão
      }
    } else {
      strapi.log.warn('[LIFECYCLE] beforeDelete Categoria - categoriaId é null. Registro pode não existir no banco. Permitindo exclusão sem limpar referências.');
      // Não fazer nada - permite que o Strapi continue mesmo sem ID
    }
  },
};
