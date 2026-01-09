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
    
    // Elementos de rastreio
    const trackingCard = document.getElementById('trackingCard');
    const trackingCode = document.getElementById('trackingCode');
    const trackingCodeRow = document.getElementById('trackingCodeRow');
    const transportadora = document.getElementById('transportadora');
    const transportadoraRow = document.getElementById('transportadoraRow');
    const trackingLink = document.getElementById('trackingLink');
    const trackingAction = document.getElementById('trackingAction');
    const trackingStatus = document.getElementById('trackingStatus');
    const trackingStatusText = document.getElementById('trackingStatusText');
    
    let pollingInterval = null;
    let lastKnownStatus = null; // Rastrear último status conhecido para detectar mudanças
    
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
            
            // Verificar se a resposta é JSON
            const contentType = response.headers.get('content-type');
            if (!contentType || !contentType.includes('application/json')) {
                const text = await response.text();
                console.error('Resposta não é JSON:', text.substring(0, 200));
                throw new Error('Resposta inválida do servidor. Tente novamente.');
            }
            
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
            
            // Verificar se o status mudou
            if (lastKnownStatus !== order.status) {
                console.log(`Status mudou: ${lastKnownStatus} -> ${order.status}`);
                lastKnownStatus = order.status;
                // Atualizar status visual
                updateStatus(order.status);
            } else if (!lastKnownStatus) {
                // Primeira carga
                lastKnownStatus = order.status;
                updateStatus(order.status);
            }
            
            // Se pedido foi entregue, mostrar mensagem e parar polling
            if (order.status === 'ENTREGUE') {
                showDeliveredMessage();
                stopPolling();
            }
            
            // Atualizar informações de rastreio se disponíveis
            updateTrackingInfo(order);
            
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
        
        console.log('Atualizando status para:', status);
        
        // Remover todas as classes de status existentes
        const statusClasses = ['status-criado', 'status-pendente', 'status-pago', 'status-aprovado', 
                              'status-na-transportadora', 'status-entregue', 'status-cancelado', 'status-expirado'];
        statusClasses.forEach(cls => currentStatusIndicator.classList.remove(cls));
        
        // Adicionar classe baseada no status
        const statusClass = status.toLowerCase().replace(/\s+/g, '-');
        const fullStatusClass = `status-${statusClass}`;
        currentStatusIndicator.classList.add(fullStatusClass);
        
        console.log('Classe CSS aplicada:', fullStatusClass);
        
        // Adicionar animação de atualização
        currentStatusIndicator.style.animation = 'none';
        setTimeout(() => {
            currentStatusIndicator.style.animation = 'pulse 0.5s ease-in-out';
        }, 10);
        
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
     * Atualiza as informações de rastreio do pedido
     */
    function updateTrackingInfo(order) {
        if (!trackingCard) return;
        
        const urlRastreamento = order.url_rastreamento;
        const codigoRastreamento = order.codigo_rastreamento;
        const transportadoraNome = order.transportadora_nome;
        const statusEtiqueta = order.status_etiqueta;
        
        // Verificar se há informações de rastreio
        const hasTrackingInfo = urlRastreamento || codigoRastreamento || statusEtiqueta;
        
        if (!hasTrackingInfo) {
            // Não há informações de rastreio ainda
            trackingCard.style.display = 'none';
            return;
        }
        
        // Mostrar card de rastreio
        trackingCard.style.display = 'block';
        
        // Exibir código de rastreamento se disponível
        if (codigoRastreamento) {
            if (trackingCode) {
                trackingCode.textContent = codigoRastreamento;
            }
            if (trackingCodeRow) {
                trackingCodeRow.style.display = 'flex';
            }
        } else {
            if (trackingCodeRow) {
                trackingCodeRow.style.display = 'none';
            }
        }
        
        // Exibir transportadora se disponível
        if (transportadoraNome) {
            if (transportadora) {
                transportadora.textContent = transportadoraNome;
            }
            if (transportadoraRow) {
                transportadoraRow.style.display = 'flex';
            }
        } else {
            if (transportadoraRow) {
                transportadoraRow.style.display = 'none';
            }
        }
        
        // Configurar link de rastreamento
        if (urlRastreamento && trackingLink) {
            trackingLink.href = urlRastreamento;
            trackingLink.style.display = 'inline-flex';
            if (trackingAction) {
                trackingAction.style.display = 'block';
            }
        } else if (codigoRastreamento && trackingLink) {
            // Se não houver URL, criar link genérico com código de rastreamento
            // Pode usar um serviço de rastreamento genérico ou o código diretamente
            const genericTrackingUrl = `https://www.google.com/search?q=rastreamento+${encodeURIComponent(codigoRastreamento)}`;
            trackingLink.href = genericTrackingUrl;
            trackingLink.style.display = 'inline-flex';
            if (trackingAction) {
                trackingAction.style.display = 'block';
            }
        } else {
            if (trackingAction) {
                trackingAction.style.display = 'none';
            }
        }
        
        // Atualizar status da etiqueta
        if (statusEtiqueta) {
            const statusMessages = {
                'pendente': 'Aguardando criação da etiqueta',
                'criada': 'Etiqueta criada',
                'paga': 'Etiqueta paga e pronta para envio',
                'impressa': 'Etiqueta impressa',
                'em_transito': 'Pedido em trânsito',
                'entregue': 'Pedido entregue',
                'cancelada': 'Etiqueta cancelada',
                'erro': 'Erro ao processar etiqueta'
            };
            
            const statusMessage = statusMessages[statusEtiqueta] || `Status: ${statusEtiqueta}`;
            
            if (trackingStatusText) {
                trackingStatusText.textContent = statusMessage;
            }
            
            // Mostrar status apenas se a etiqueta ainda não foi impressa/enviada
            if (['pendente', 'criada', 'paga'].includes(statusEtiqueta)) {
                if (trackingStatus) {
                    trackingStatus.style.display = 'block';
                }
            } else {
                if (trackingStatus) {
                    trackingStatus.style.display = 'none';
                }
            }
        } else {
            if (trackingStatus) {
                trackingStatus.style.display = 'none';
            }
        }
    }
    
    /**
     * Faz polling do status do pedido
     */
    function startPolling() {
        // Parar polling anterior se existir
        stopPolling();
        
        // Fazer polling a cada 5 segundos para detectar mudanças mais rapidamente
        pollingInterval = setInterval(async () => {
            try {
                console.log('[Polling] Verificando status do pedido...');
                const response = await fetch(`/api/orders/${token}/status`);
                
                // Verificar se a resposta é JSON
                const contentType = response.headers.get('content-type');
                if (!contentType || !contentType.includes('application/json')) {
                    console.warn('Resposta de status não é JSON, ignorando...');
                    return;
                }
                
                const data = await response.json();
                
                if (data.success && data.status) {
                    // Verificar se o status mudou comparando com o último status conhecido
                    if (lastKnownStatus !== data.status) {
                        console.log(`[Polling] ⚠️ Status mudou detectado: ${lastKnownStatus} -> ${data.status}`);
                        // Status mudou, recarregar dados completos
                        await loadOrderData();
                    } else {
                        console.log(`[Polling] Status mantido: ${data.status}`);
                    }
                } else if (response.status === 404) {
                    // Pedido não encontrado (provavelmente entregue e token removido)
                    console.log('[Polling] Pedido não encontrado (404)');
                    showDeliveredMessage();
                    stopPolling();
                }
            } catch (error) {
                console.error('[Polling] Erro ao verificar status:', error);
            }
        }, 5000); // 5 segundos para detectar mudanças mais rapidamente
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
