import { syncConteudoContatoToPostgres } from '../../../../services/strapi-sync-service';

function coerceJsonField(value: any, fallback: any) {
  if (value === undefined) return undefined;
  if (value === null) return fallback;
  if (value === '') return fallback;
  if (typeof value === 'string') {
    try {
      const parsed = JSON.parse(value);
      return parsed ?? fallback;
    } catch {
      return fallback;
    }
  }
  return value;
}

async function ensureDocumentIdForSingleType(data: any) {
  // Se document_id vier vazio, o Strapi pode acabar "criando" sempre e depois recarregar o registro antigo.
  // Vamos garantir um document_id estável pegando o existente no banco.
  if (!data) return;
  const docId = data.document_id;
  if (docId && docId !== '') return;

  const row = await strapi.db.connection('conteudo_contato')
    .select('document_id')
    .whereNotNull('document_id')
    .andWhere('document_id', '!=', '')
    .orderBy('id', 'asc')
    .first();

  if (row?.document_id) {
    data.document_id = row.document_id;
  }
}

export default {
  async beforeCreate(event: any) {
    const data = event?.params?.data;
    if (!data) return;

    // Strapi às vezes envia '' para campos JSON quando ficam "em branco" no admin.
    // Postgres JSON não aceita '' -> normalize.
    data.informacoes_contato = coerceJsonField(data.informacoes_contato, []);
    data.redes_sociais = coerceJsonField(data.redes_sociais, {});

    await ensureDocumentIdForSingleType(data);
  },

  async beforeUpdate(event: any) {
    const data = event?.params?.data;
    if (!data) return;

    data.informacoes_contato = coerceJsonField(data.informacoes_contato, []);
    data.redes_sociais = coerceJsonField(data.redes_sociais, {});

    await ensureDocumentIdForSingleType(data);
  },

  async afterCreate(event: any) {
    const { result } = event;
    strapi.log.info(`[LIFECYCLE] Conteudo Contato criado: ${result.id}`);
    await syncConteudoContatoToPostgres(result);
  },
  
  async afterUpdate(event: any) {
    const { result } = event;
    strapi.log.info(`[LIFECYCLE] Conteudo Contato atualizado: ${result.id}`);
    await syncConteudoContatoToPostgres(result);
  },
  
  async afterDelete(event: any) {
    const { result } = event;
    strapi.log.info(`[LIFECYCLE] Conteudo Contato deletado: ${result.id}`);
    await syncConteudoContatoToPostgres({ ...result, ativo: false });
  }
};
