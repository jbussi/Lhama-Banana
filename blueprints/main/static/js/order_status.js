// JavaScript para página de status do pedido
document.addEventListener('DOMContentLoaded', function() {
    console.log('Order Status page loaded');
    
    // Obter token da URL
    const urlParams = new URLSearchParams(window.location.search);
    const token = urlParams.get('token');
    
    if (!token) {
        console.error('Token não fornecido na URL');
        showError('Token de acesso não encontrado. Por favor, acesse esta página através do checkout.');
        return;
    }
    
    // Elementos da página
    const currentStatusIndicator = document.getElementById('currentStatusIndicator');
    const currentStatusText = document.getElementById('currentStatusText');
    const orderCode = document.getElementById('orderCode');
    const orderValue = document.getElementById('orderValue');
    const orderDate = document.getElementById('orderDate');
    const lastUpdate = document.getElementById('lastUpdate');
    const refreshStatusBtn = document.getElementById('refreshStatus');
    const statusLoading = document.getElementById('statusLoading');
    const deliveredMessage = document.getElementById('deliveredMessage');
    const errorMessage = document.getElementById('errorMessage');
    
    let pollingInterval = null;
    
    // Status possíveis em ordem
    const statusOrder = [
        'CRIADO',
        'PENDENTE',
        'PAGO',
        'APROVADO',
        'NA TRANSPORTADORA',
        'ENTREGUE',
        'CANCELADO',
        'EXPIRADO'
    ];
    
    /**
     * Carrega dados do pedido via API
     */
    async function loadOrderData() {
        try {
            if (statusLoading) statusLoading.style.display = 'flex';
            
            const response = await fetch(`/api/orders/${token}`);
            const data = await response.json();
            
            if (!response.ok || !data.success) {
                // Se pedido não encontrado ou token removido (entregue)
                if (response.status === 404) {
                    showDeliveredMessage();
                    stopPolling();
                    return;
                }
                throw new Error(data.erro || data.message || 'Erro ao carregar dados do pedido');
            }
            
            const order = data.order;
            
            // Atualizar informações do pedido
            if (orderCode) {
                orderCode.textContent = order.codigo_pedido || '--';
            }
            
            if (orderValue) {
                orderValue.textContent = formatCurrency(order.valor);
            }
            
            if (orderDate && order.data_venda) {
                const date = new Date(order.data_venda);
                orderDate.textContent = date.toLocaleString('pt-BR');
            }
            
            if (lastUpdate && order.atualizado_em) {
                const date = new Date(order.atualizado_em);
                lastUpdate.textContent = date.toLocaleString('pt-BR');
            }
            
            // Atualizar status
            updateStatus(order.status);
            
            // Se pedido foi entregue, mostrar mensagem e parar polling
            if (order.status === 'ENTREGUE') {
                showDeliveredMessage();
                stopPolling();
            }
            
        } catch (error) {
            console.error('Erro ao carregar dados do pedido:', error);
            showError(`Erro ao carregar dados: ${error.message}`);
            stopPolling();
        } finally {
            if (statusLoading) statusLoading.style.display = 'none';
        }
    }
    
    /**
     * Atualiza o status visual do pedido e timeline
     */
    function updateStatus(status) {
        if (!currentStatusIndicator || !currentStatusText) return;
        
        // Remover todas as classes de status
        currentStatusIndicator.className = 'status-indicator';
        
        // Adicionar classe baseada no status
        const statusClass = status.toLowerCase().replace(/\s+/g, '-');
        currentStatusIndicator.classList.add(`status-${statusClass}`);
        
        // Atualizar texto do status
        const statusTexts = {
            'CRIADO': 'Pedido Criado',
            'PENDENTE': 'Aguardando Pagamento',
            'PAGO': 'Pagamento Confirmado',
            'APROVADO': 'Pedido Aprovado',
            'NA TRANSPORTADORA': 'Na Transportadora',
            'ENTREGUE': 'Entregue',
            'CANCELADO': 'Pedido Cancelado',
            'EXPIRADO': 'Pedido Expirado'
        };
        
        if (currentStatusText) {
            currentStatusText.textContent = statusTexts[status] || status;
        }
        
        // Atualizar timeline
        updateTimeline(status);
    }
    
    /**
     * Atualiza a timeline de status
     */
    function updateTimeline(currentStatus) {
        const timelineItems = document.querySelectorAll('.timeline-item');
        
        timelineItems.forEach(item => {
            const itemStatus = item.getAttribute('data-status');
            if (!itemStatus) return;
            
            // Remover classes anteriores
            item.classList.remove('active', 'completed');
            
            // Encontrar índice do status atual e do item
            const currentIndex = statusOrder.indexOf(currentStatus);
            const itemIndex = statusOrder.indexOf(itemStatus);
            
            if (itemIndex === -1) return;
            
            // Se o item já foi completado
            if (itemIndex < currentIndex) {
                item.classList.add('completed');
            }
            // Se é o status atual
            else if (itemIndex === currentIndex) {
                item.classList.add('active');
            }
            
            // Mostrar/esconder itens de erro
            if (itemStatus === 'CANCELADO' || itemStatus === 'EXPIRADO') {
                if (currentStatus === itemStatus) {
                    item.style.display = 'block';
                } else {
                    item.style.display = 'none';
                }
            }
        });
    }
    
    /**
     * Formata valor monetário
     */
    function formatCurrency(value) {
        return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(value);
    }
    
    /**
     * Faz polling do status do pedido
     */
    function startPolling() {
        // Parar polling anterior se existir
        stopPolling();
        
        // Fazer polling a cada 10 segundos (menos frequente que PIX/Boleto)
        pollingInterval = setInterval(async () => {
            try {
                const response = await fetch(`/api/orders/${token}/status`);
                const data = await response.json();
                
                if (data.success && data.status) {
                    // Verificar se o status mudou
                    const currentStatus = currentStatusText?.textContent || '';
                    const newStatusText = getStatusText(data.status);
                    
                    if (currentStatus !== newStatusText) {
                        // Status mudou, recarregar dados completos
                        await loadOrderData();
                    }
                } else if (response.status === 404) {
                    // Pedido não encontrado (provavelmente entregue e token removido)
                    showDeliveredMessage();
                    stopPolling();
                }
            } catch (error) {
                console.error('Erro ao verificar status:', error);
            }
        }, 10000); // 10 segundos
    }
    
    /**
     * Retorna texto do status
     */
    function getStatusText(status) {
        const statusTexts = {
            'CRIADO': 'Pedido Criado',
            'PENDENTE': 'Aguardando Pagamento',
            'PAGO': 'Pagamento Confirmado',
            'APROVADO': 'Pedido Aprovado',
            'NA TRANSPORTADORA': 'Na Transportadora',
            'ENTREGUE': 'Entregue',
            'CANCELADO': 'Pedido Cancelado',
            'EXPIRADO': 'Pedido Expirado'
        };
        return statusTexts[status] || status;
    }
    
    /**
     * Para o polling
     */
    function stopPolling() {
        if (pollingInterval) {
            clearInterval(pollingInterval);
            pollingInterval = null;
        }
    }
    
    /**
     * Mostra mensagem de pedido entregue
     */
    function showDeliveredMessage() {
        if (deliveredMessage) {
            deliveredMessage.style.display = 'block';
        }
        // Esconder outros elementos
        if (errorMessage) errorMessage.style.display = 'none';
    }
    
    /**
     * Mostra mensagem de erro
     */
    function showError(message) {
        if (errorMessage) {
            errorMessage.style.display = 'block';
            const errorText = errorMessage.querySelector('p');
            if (errorText) {
                errorText.textContent = message;
            }
        }
    }
    
    /**
     * Botão de atualizar status manualmente
     */
    if (refreshStatusBtn) {
        refreshStatusBtn.addEventListener('click', async function() {
            await loadOrderData();
        });
    }
    
    // Carregar dados iniciais
    loadOrderData();
    
    // Iniciar polling
    startPolling();
    
    // Parar polling quando a página for fechada
    window.addEventListener('beforeunload', stopPolling);
});
