import React, { useEffect, useState } from 'react';
import {
  Box,
  Card,
  Flex,
  Grid,
  Typography,
  Button,
  Link,
} from '@strapi/design-system';

interface Stats {
  totalVendas: number;
  totalPedidos: number;
  totalEtiquetas: number;
  receitaTotal: number;
  produtosBaixoEstoque: number;
  totalProdutos: number;
}

const DashboardWidget: React.FC = () => {
  const [stats, setStats] = useState<Stats>({
    totalVendas: 0,
    totalPedidos: 0,
    totalEtiquetas: 0,
    receitaTotal: 0,
    produtosBaixoEstoque: 0,
    totalProdutos: 0,
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchStats();
  }, []);

  const fetchStats = async () => {
    try {
      const baseURL = window.location.origin;
      
      const [vendasRes, etiquetasRes, produtosRes] = await Promise.all([
        fetch(`${baseURL}/api/vendas?pagination[pageSize]=1`).then(r => r.json()),
        fetch(`${baseURL}/api/etiqueta-fretes?pagination[pageSize]=1`).then(r => r.json()),
        fetch(`${baseURL}/api/produtos?pagination[pageSize]=1`).then(r => r.json()),
      ]);

      const totalVendas = vendasRes?.meta?.pagination?.total || 0;
      const totalEtiquetas = etiquetasRes?.meta?.pagination?.total || 0;
      const totalProdutos = produtosRes?.meta?.pagination?.total || 0;

      const produtosCompletoRes = await fetch(`${baseURL}/api/produtos?pagination[pageSize]=100`);
      const produtosCompleto = await produtosCompletoRes.json();
      const produtosBaixoEstoque = produtosCompleto?.data?.filter(
        (produto: any) => produto.estoque <= (produto.estoque_minimo || 0)
      ).length || 0;

      const vendasCompletasRes = await fetch(`${baseURL}/api/vendas?pagination[pageSize]=100`);
      const vendasCompletas = await vendasCompletasRes.json();
      const receitaTotal = vendasCompletas?.data?.reduce(
        (acc: number, venda: any) => acc + (parseFloat(venda.valor_total) || 0),
        0
      ) || 0;

      setStats({
        totalVendas,
        totalPedidos: totalVendas,
        totalEtiquetas,
        receitaTotal,
        produtosBaixoEstoque,
        totalProdutos,
      });
    } catch (error) {
      console.error('Erro ao buscar estatísticas:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <Box padding={8} textAlign="center">
        <Typography variant="omega">Carregando estatísticas...</Typography>
      </Box>
    );
  }

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('pt-BR', {
      style: 'currency',
      currency: 'BRL',
    }).format(value);
  };

  return (
    <Box padding={8} background="neutral100" style={{ minHeight: '100vh' }}>
        <Flex direction="column" gap={6} style={{ maxWidth: '1400px', margin: '0 auto' }}>
        {/* Cabeçalho melhorado */}
        <Flex justifyContent="space-between" alignItems="center" paddingBottom={2}>
          <Typography variant="alpha" fontWeight="bold" style={{ fontSize: '32px', color: '#40e0d0' }}>
            🦙 Dashboard LhamaBanana
          </Typography>
          <Button onClick={fetchStats} variant="secondary" size="M" style={{ borderRadius: '8px' }}>
            🔄 Atualizar
          </Button>
        </Flex>

        {/* Cards de Estatísticas - Melhor alinhamento e espaçamento */}
        <Grid.Root gap={4} cols={4}>
          <Grid.Item col={1}>
            <Card
              padding={6}
              style={{
                background: 'linear-gradient(135deg, #40e0d0 0%, #36d1c4 100%)',
                color: 'white',
                borderRadius: '16px',
                boxShadow: '0 4px 16px rgba(64, 224, 208, 0.25)',
                height: '100%',
                minHeight: '140px',
              }}
            >
              <Flex direction="column" gap={3} alignItems="flex-start" style={{ height: '100%' }}>
                <Flex alignItems="center" gap={2}>
                  <Typography variant="omega" fontWeight="bold" textColor="neutral0" style={{ fontSize: '32px' }}>
                    🛒
                  </Typography>
                  <Typography variant="omega" fontWeight="bold" textColor="neutral0" style={{ fontSize: '14px', lineHeight: '1.4' }}>
                    Total de Vendas
                  </Typography>
                </Flex>
                <Typography variant="alpha" textColor="neutral0" fontWeight="bold" style={{ fontSize: '36px', lineHeight: '1.2' }}>
                  {stats.totalVendas}
                </Typography>
              </Flex>
            </Card>
          </Grid.Item>

          <Grid.Item col={1}>
            <Card
              padding={6}
              style={{
                background: 'linear-gradient(135deg, #FFE135 0%, #ffd700 100%)',
                color: '#000',
                borderRadius: '16px',
                boxShadow: '0 4px 16px rgba(255, 225, 53, 0.25)',
                height: '100%',
                minHeight: '140px',
              }}
            >
              <Flex direction="column" gap={3} alignItems="flex-start" style={{ height: '100%' }}>
                <Flex alignItems="center" gap={2}>
                  <Typography variant="omega" fontWeight="bold" style={{ fontSize: '32px' }}>
                    💰
                  </Typography>
                  <Typography variant="omega" fontWeight="bold" style={{ fontSize: '14px', lineHeight: '1.4' }}>
                    Receita Total
                  </Typography>
                </Flex>
                <Typography variant="alpha" fontWeight="bold" style={{ fontSize: '28px', lineHeight: '1.2' }}>
                  {formatCurrency(stats.receitaTotal)}
                </Typography>
              </Flex>
            </Card>
          </Grid.Item>

          <Grid.Item col={1}>
            <Card
              padding={6}
              style={{
                background: 'linear-gradient(135deg, #36d1c4 0%, #2bb3a8 100%)',
                color: 'white',
                borderRadius: '16px',
                boxShadow: '0 4px 16px rgba(54, 209, 196, 0.25)',
                height: '100%',
                minHeight: '140px',
              }}
            >
              <Flex direction="column" gap={3} alignItems="flex-start" style={{ height: '100%' }}>
                <Flex alignItems="center" gap={2}>
                  <Typography variant="omega" fontWeight="bold" textColor="neutral0" style={{ fontSize: '32px' }}>
                    📦
                  </Typography>
                  <Typography variant="omega" fontWeight="bold" textColor="neutral0" style={{ fontSize: '14px', lineHeight: '1.4' }}>
                    Etiquetas
                  </Typography>
                </Flex>
                <Typography variant="alpha" textColor="neutral0" fontWeight="bold" style={{ fontSize: '36px', lineHeight: '1.2' }}>
                  {stats.totalEtiquetas}
                </Typography>
              </Flex>
            </Card>
          </Grid.Item>

          <Grid.Item col={1}>
            <Card
              padding={6}
              style={{
                background: stats.produtosBaixoEstoque > 0
                  ? 'linear-gradient(135deg, #ff6b6b 0%, #ee5a6f 100%)'
                  : 'linear-gradient(135deg, #40e0d0 0%, #36d1c4 100%)',
                color: 'white',
                borderRadius: '16px',
                boxShadow: stats.produtosBaixoEstoque > 0 
                  ? '0 4px 16px rgba(255, 107, 107, 0.25)'
                  : '0 4px 16px rgba(64, 224, 208, 0.25)',
                height: '100%',
                minHeight: '140px',
              }}
            >
              <Flex direction="column" gap={3} alignItems="flex-start" style={{ height: '100%' }}>
                <Flex alignItems="center" gap={2}>
                  <Typography variant="omega" fontWeight="bold" textColor="neutral0" style={{ fontSize: '32px' }}>
                    ⚠️
                  </Typography>
                  <Typography variant="omega" fontWeight="bold" textColor="neutral0" style={{ fontSize: '14px', lineHeight: '1.4' }}>
                    Estoque Baixo
                  </Typography>
                </Flex>
                <Typography variant="alpha" textColor="neutral0" fontWeight="bold" style={{ fontSize: '36px', lineHeight: '1.2' }}>
                  {stats.produtosBaixoEstoque}
                </Typography>
              </Flex>
            </Card>
          </Grid.Item>
        </Grid.Root>

        {/* Ações Rápidas - Melhor alinhamento e design */}
        <Card padding={6} style={{ borderRadius: '16px', boxShadow: '0 2px 8px rgba(0,0,0,0.1)' }}>
          <Typography variant="beta" fontWeight="bold" paddingBottom={4} style={{ fontSize: '22px', color: '#40e0d0' }}>
            ⚡ Ações Rápidas
          </Typography>
          <Grid.Root gap={4} cols={3}>
            <Grid.Item col={1}>
              <Card
                padding={5}
                style={{
                  border: '2px solid #40e0d0',
                  borderRadius: '12px',
                  cursor: 'pointer',
                  transition: 'all 0.3s ease',
                  height: '100%',
                  background: 'white',
                }}
                onClick={() => window.location.href = '/admin/content-manager/collection-types/api::produto.produto'}
                onMouseEnter={(e) => {
                  e.currentTarget.style.transform = 'translateY(-4px)';
                  e.currentTarget.style.boxShadow = '0 8px 20px rgba(64, 224, 208, 0.3)';
                  e.currentTarget.style.borderColor = '#36d1c4';
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.transform = 'translateY(0)';
                  e.currentTarget.style.boxShadow = 'none';
                  e.currentTarget.style.borderColor = '#40e0d0';
                }}
              >
                <Flex direction="column" gap={3} alignItems="center" style={{ textAlign: 'center', height: '100%' }}>
                  <Typography variant="omega" fontWeight="bold" style={{ fontSize: '48px', lineHeight: '1' }}>
                    📦
                  </Typography>
                  <Typography variant="omega" fontWeight="bold" style={{ fontSize: '16px', color: '#40e0d0' }}>
                    Gerenciar Estoque
                  </Typography>
                  <Typography variant="omega" textColor="neutral600" style={{ fontSize: '13px', lineHeight: '1.5' }}>
                    Atualizar estoque de produtos
                  </Typography>
                  <Button
                    variant="secondary"
                    size="M"
                    style={{ marginTop: '8px', width: '100%', borderRadius: '8px' }}
                  >
                    Acessar →
                  </Button>
                </Flex>
              </Card>
            </Grid.Item>

            <Grid.Item col={1}>
              <Card
                padding={5}
                style={{
                  border: '2px solid #FFE135',
                  borderRadius: '12px',
                  cursor: 'pointer',
                  transition: 'all 0.3s ease',
                  height: '100%',
                  background: 'white',
                }}
                onClick={() => window.location.href = '/admin/content-manager/collection-types/api::produto.produto/create'}
                onMouseEnter={(e) => {
                  e.currentTarget.style.transform = 'translateY(-4px)';
                  e.currentTarget.style.boxShadow = '0 8px 20px rgba(255, 225, 53, 0.3)';
                  e.currentTarget.style.borderColor = '#ffd700';
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.transform = 'translateY(0)';
                  e.currentTarget.style.boxShadow = 'none';
                  e.currentTarget.style.borderColor = '#FFE135';
                }}
              >
                <Flex direction="column" gap={3} alignItems="center" style={{ textAlign: 'center', height: '100%' }}>
                  <Typography variant="omega" fontWeight="bold" style={{ fontSize: '48px', lineHeight: '1' }}>
                    ➕
                  </Typography>
                  <Typography variant="omega" fontWeight="bold" style={{ fontSize: '16px', color: '#FFE135' }}>
                    Criar Produto
                  </Typography>
                  <Typography variant="omega" textColor="neutral600" style={{ fontSize: '13px', lineHeight: '1.5' }}>
                    Adicionar novo produto ao catálogo
                  </Typography>
                  <Button
                    variant="secondary"
                    size="M"
                    style={{ marginTop: '8px', width: '100%', borderRadius: '8px' }}
                  >
                    Criar →
                  </Button>
                </Flex>
              </Card>
            </Grid.Item>

            <Grid.Item col={1}>
              <Card
                padding={5}
                style={{
                  border: '2px solid #40e0d0',
                  borderRadius: '12px',
                  cursor: 'pointer',
                  transition: 'all 0.3s ease',
                  height: '100%',
                  background: 'white',
                }}
                onClick={() => window.location.href = '/admin/plugins/frete-management'}
                onMouseEnter={(e) => {
                  e.currentTarget.style.transform = 'translateY(-4px)';
                  e.currentTarget.style.boxShadow = '0 8px 20px rgba(64, 224, 208, 0.3)';
                  e.currentTarget.style.borderColor = '#36d1c4';
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.transform = 'translateY(0)';
                  e.currentTarget.style.boxShadow = 'none';
                  e.currentTarget.style.borderColor = '#40e0d0';
                }}
              >
                <Flex direction="column" gap={3} alignItems="center" style={{ textAlign: 'center', height: '100%' }}>
                  <Typography variant="omega" fontWeight="bold" style={{ fontSize: '48px', lineHeight: '1' }}>
                    🚚
                  </Typography>
                  <Typography variant="omega" fontWeight="bold" style={{ fontSize: '16px', color: '#40e0d0' }}>
                    Gestão de Frete
                  </Typography>
                  <Typography variant="omega" textColor="neutral600" style={{ fontSize: '13px', lineHeight: '1.5' }}>
                    Ver e imprimir etiquetas
                  </Typography>
                  <Button
                    variant="secondary"
                    size="M"
                    style={{ marginTop: '8px', width: '100%', borderRadius: '8px' }}
                  >
                    Acessar →
                  </Button>
                </Flex>
              </Card>
            </Grid.Item>
          </Grid.Root>
        </Card>

        {/* Links Rápidos - Melhor organização e alinhamento */}
        <Card padding={5} style={{ borderRadius: '16px', boxShadow: '0 2px 8px rgba(0,0,0,0.1)' }}>
          <Typography variant="beta" fontWeight="bold" paddingBottom={3} style={{ fontSize: '20px', color: '#40e0d0' }}>
            🔗 Links Rápidos
          </Typography>
          <Flex direction="row" gap={3} wrap="wrap" justifyContent="flex-start" alignItems="center">
            <Link href="/admin/content-manager/collection-types/api::venda.venda">
              <Button variant="tertiary" size="M" style={{ borderRadius: '8px', padding: '10px 20px' }}>
                🛒 Ver Pedidos
              </Button>
            </Link>
            <Link href="/admin/content-manager/collection-types/api::etiqueta-frete.etiqueta-frete">
              <Button variant="tertiary" size="M" style={{ borderRadius: '8px', padding: '10px 20px' }}>
                🏷️ Etiquetas de Frete
              </Button>
            </Link>
            <Link href="/admin/content-manager/collection-types/api::produto.produto">
              <Button variant="tertiary" size="M" style={{ borderRadius: '8px', padding: '10px 20px' }}>
                📦 Produtos
              </Button>
            </Link>
            <Link href="/admin/content-manager/collection-types/api::usuario.usuario">
              <Button variant="tertiary" size="M" style={{ borderRadius: '8px', padding: '10px 20px' }}>
                👥 Usuários
              </Button>
            </Link>
            <Link href="/admin/content-manager/collection-types/api::cupom.cupom">
              <Button variant="tertiary" size="M" style={{ borderRadius: '8px', padding: '10px 20px' }}>
                🎟️ Cupons
              </Button>
            </Link>
            <Link href="/admin/content-manager/collection-types/api::categoria.categoria">
              <Button variant="tertiary" size="M" style={{ borderRadius: '8px', padding: '10px 20px' }}>
                📁 Categorias
              </Button>
            </Link>
          </Flex>
        </Card>
        </Flex>
      </Box>
  );
};

export default DashboardWidget;
