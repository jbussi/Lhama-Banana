import React, { useState, useEffect } from 'react';
import {
  Box,
  Button,
  Card,
  Flex,
  Grid,
  Typography,
  Table,
  Thead,
  Tbody,
  Tr,
  Th,
  Td,
  Badge,
  IconButton,
  Alert,
} from '@strapi/design-system';
import { Printer, Eye, Cross } from '@strapi/icons';
import { useFetchClient } from '@strapi/helper-plugin';
// Importar componente para remover banners (caminho relativo)
// import HidePromotions from '../../../../admin/components/HidePromotions';

interface EtiquetaFrete {
  id: number;
  codigo_pedido: string;
  status_etiqueta: string;
  transportadora_nome: string;
  codigo_rastreamento: string;
  url_etiqueta: string;
  url_rastreamento: string;
  valor_frete: number;
  peso_total: number;
  venda?: {
    id: number;
    codigo_pedido: string;
    valor_total: number;
    status_pedido: string;
    itens?: Array<{
      id: number;
      quantidade: number;
      preco_unitario: number;
      subtotal: number;
      nome_produto_snapshot: string;
      sku_produto_snapshot: string;
    }>;
  };
}

const App: React.FC = () => {
  const { get } = useFetchClient();
  const [etiquetas, setEtiquetas] = useState<EtiquetaFrete[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedEtiqueta, setSelectedEtiqueta] = useState<EtiquetaFrete | null>(null);
  const [showDetails, setShowDetails] = useState(false);

  useEffect(() => {
    fetchEtiquetas();
  }, []);

  const fetchEtiquetas = async () => {
    try {
      setLoading(true);
      const { data } = await get('/api/etiqueta-fretes?populate[venda][populate][itens]=*');
      setEtiquetas(data.data || []);
    } catch (error) {
      console.error('Erro ao buscar etiquetas:', error);
    } finally {
      setLoading(false);
    }
  };

  const getStatusBadge = (status: string) => {
    const statusConfig: Record<string, { color: string; label: string }> = {
      pendente: { color: 'secondary', label: 'Pendente' },
      criada: { color: 'alternative', label: 'Criada' },
      paga: { color: 'success', label: 'Paga' },
      impressa: { color: 'success', label: 'Impressa' },
      cancelada: { color: 'danger', label: 'Cancelada' },
      erro: { color: 'danger', label: 'Erro' },
      em_transito: { color: 'primary', label: 'Em Trânsito' },
      entregue: { color: 'success', label: 'Entregue' },
    };

    const config = statusConfig[status] || { color: 'secondary', label: status };
    return <Badge variant={config.color as any}>{config.label}</Badge>;
  };

  const handleViewDetails = (etiqueta: EtiquetaFrete) => {
    setSelectedEtiqueta(etiqueta);
    setShowDetails(true);
  };

  const handlePrint = (url: string) => {
    if (url) {
      window.open(url, '_blank');
    }
  };

  const handleTrack = (url: string, codigo: string) => {
    if (url) {
      window.open(url, '_blank');
    } else if (codigo) {
      window.open(`https://www.google.com/search?q=rastreamento+${codigo}`, '_blank');
    }
  };

  if (loading) {
    return (
      <Box padding={8}>
        <Typography variant="alpha">Carregando etiquetas...</Typography>
      </Box>
    );
  }

  return (
    <Box padding={8} background="neutral100">
      <Flex direction="column" gap={4}>
        <Flex justifyContent="space-between" alignItems="center">
          <Typography variant="alpha" fontWeight="bold">
            📦 Gestão de Frete e Embalagem
          </Typography>
          <Button onClick={fetchEtiquetas} variant="secondary">
            Atualizar
          </Button>
        </Flex>

        {showDetails && selectedEtiqueta && (
          <Card padding={6}>
            <Flex direction="column" gap={4}>
              <Flex justifyContent="space-between" alignItems="center">
                <Typography variant="beta">
                  Detalhes do Pedido: {selectedEtiqueta.codigo_pedido}
                </Typography>
                <IconButton
                  onClick={() => setShowDetails(false)}
                  label="Fechar"
                  icon={<Cross />}
                />
              </Flex>

              <Grid.Root gap={4} cols={2}>
                <Grid.Item>
                  <Card padding={4}>
                    <Typography variant="omega" fontWeight="bold">
                      Informações da Etiqueta
                    </Typography>
                    <Box paddingTop={2}>
                      <Typography variant="omega">
                        <strong>Status:</strong> {getStatusBadge(selectedEtiqueta.status_etiqueta)}
                      </Typography>
                      <Typography variant="omega">
                        <strong>Transportadora:</strong> {selectedEtiqueta.transportadora_nome || 'N/A'}
                      </Typography>
                      <Typography variant="omega">
                        <strong>Código de Rastreamento:</strong>{' '}
                        {selectedEtiqueta.codigo_rastreamento || 'N/A'}
                      </Typography>
                      <Typography variant="omega">
                        <strong>Valor do Frete:</strong> R${' '}
                        {selectedEtiqueta.valor_frete?.toFixed(2) || '0.00'}
                      </Typography>
                      <Typography variant="omega">
                        <strong>Peso Total:</strong> {selectedEtiqueta.peso_total || 0} kg
                      </Typography>
                    </Box>
                  </Card>
                </Grid.Item>

                <Grid.Item>
                  <Card padding={4}>
                    <Typography variant="omega" fontWeight="bold">
                      Produtos do Pedido
                    </Typography>
                    <Box paddingTop={2}>
                      {selectedEtiqueta.venda?.itens && selectedEtiqueta.venda.itens.length > 0 ? (
                        <Table colCount={4} rowCount={selectedEtiqueta.venda.itens.length}>
                          <Thead>
                            <Tr>
                              <Th>
                                <Typography variant="sigma">Produto</Typography>
                              </Th>
                              <Th>
                                <Typography variant="sigma">SKU</Typography>
                              </Th>
                              <Th>
                                <Typography variant="sigma">Qtd</Typography>
                              </Th>
                              <Th>
                                <Typography variant="sigma">Subtotal</Typography>
                              </Th>
                            </Tr>
                          </Thead>
                          <Tbody>
                            {selectedEtiqueta.venda.itens.map((item) => (
                              <Tr key={item.id}>
                                <Td>
                                  <Typography variant="omega">{item.nome_produto_snapshot}</Typography>
                                </Td>
                                <Td>
                                  <Typography variant="omega">{item.sku_produto_snapshot}</Typography>
                                </Td>
                                <Td>
                                  <Typography variant="omega">{item.quantidade}</Typography>
                                </Td>
                                <Td>
                                  <Typography variant="omega">
                                    R$ {item.subtotal.toFixed(2)}
                                  </Typography>
                                </Td>
                              </Tr>
                            ))}
                          </Tbody>
                        </Table>
                      ) : (
                        <Alert closeLabel="Fechar" title="Nenhum produto encontrado">
                          Não há produtos associados a este pedido.
                        </Alert>
                      )}
                    </Box>
                  </Card>
                </Grid.Item>
              </Grid.Root>

              <Flex gap={2} justifyContent="flex-end">
                {selectedEtiqueta.url_etiqueta && (
                  <Button
                    onClick={() => handlePrint(selectedEtiqueta.url_etiqueta)}
                    variant="default"
                    startIcon={<Printer />}
                  >
                    Imprimir Etiqueta
                  </Button>
                )}
                {(selectedEtiqueta.url_rastreamento || selectedEtiqueta.codigo_rastreamento) && (
                  <Button
                    onClick={() =>
                      handleTrack(
                        selectedEtiqueta.url_rastreamento,
                        selectedEtiqueta.codigo_rastreamento
                      )
                    }
                    variant="secondary"
                    startIcon={<Eye />}
                  >
                    Rastrear Envio
                  </Button>
                )}
              </Flex>
            </Flex>
          </Card>
        )}

        <Card padding={6}>
          <Typography variant="beta" paddingBottom={4}>
            Etiquetas de Frete
          </Typography>
          <Table colCount={7} rowCount={etiquetas.length}>
            <Thead>
              <Tr>
                <Th>
                  <Typography variant="sigma">Código Pedido</Typography>
                </Th>
                <Th>
                  <Typography variant="sigma">Status</Typography>
                </Th>
                <Th>
                  <Typography variant="sigma">Transportadora</Typography>
                </Th>
                <Th>
                  <Typography variant="sigma">Rastreamento</Typography>
                </Th>
                <Th>
                  <Typography variant="sigma">Valor Frete</Typography>
                </Th>
                <Th>
                  <Typography variant="sigma">Peso</Typography>
                </Th>
                <Th>
                  <Typography variant="sigma">Ações</Typography>
                </Th>
              </Tr>
            </Thead>
            <Tbody>
              {etiquetas.length === 0 ? (
                <Tr>
                  <Td colSpan={7}>
                    <Box padding={4} textAlign="center">
                      <Typography variant="omega">Nenhuma etiqueta encontrada.</Typography>
                    </Box>
                  </Td>
                </Tr>
              ) : (
                etiquetas.map((etiqueta) => (
                  <Tr key={etiqueta.id}>
                    <Td>
                      <Typography variant="omega">{etiqueta.codigo_pedido}</Typography>
                    </Td>
                    <Td>{getStatusBadge(etiqueta.status_etiqueta)}</Td>
                    <Td>
                      <Typography variant="omega">
                        {etiqueta.transportadora_nome || 'N/A'}
                      </Typography>
                    </Td>
                    <Td>
                      <Typography variant="omega">
                        {etiqueta.codigo_rastreamento || 'N/A'}
                      </Typography>
                    </Td>
                    <Td>
                      <Typography variant="omega">
                        R$ {etiqueta.valor_frete?.toFixed(2) || '0.00'}
                      </Typography>
                    </Td>
                    <Td>
                      <Typography variant="omega">{etiqueta.peso_total || 0} kg</Typography>
                    </Td>
                    <Td>
                      <Flex gap={2}>
                        <IconButton
                          onClick={() => handleViewDetails(etiqueta)}
                          label="Ver Detalhes"
                          icon={<Eye />}
                        />
                        {etiqueta.url_etiqueta && (
                          <IconButton
                            onClick={() => handlePrint(etiqueta.url_etiqueta)}
                            label="Imprimir"
                            icon={<Printer />}
                          />
                        )}
                      </Flex>
                    </Td>
                  </Tr>
                ))
              )}
            </Tbody>
          </Table>
        </Card>
      </Flex>
    </Box>
  );
};

export default App;
