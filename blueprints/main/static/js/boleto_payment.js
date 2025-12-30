// JavaScript para página de pagamento Boleto
document.addEventListener('DOMContentLoaded', function() {
    console.log('Boleto Payment page loaded');
    
    // Obter token da URL
    const urlParams = new URLSearchParams(window.location.search);
    const token = urlParams.get('token');
    
    if (!token) {
        console.error('Token não fornecido na URL');
        showError('Token de acesso não encontrado. Por favor, acesse esta página através do checkout.');
        return;
    }
    
    // Elementos da página
    const paymentAmount = document.getElementById('paymentAmount');
    const paymentExpiry = document.getElementById('paymentExpiry');
    const orderCode = document.getElementById('orderCode');
    const barcode = document.getElementById('barcode');
    const barcodeInput = document.getElementById('barcodeInput');
    const copyBarcodeBtn = document.getElementById('copyBarcode');
    const viewBoletoBtn = document.getElementById('viewBoleto');
    const downloadBoletoBtn = document.getElementById('downloadBoleto');
    const statusText = document.getElementById('statusText');
    const statusIndicator = document.querySelector('.status-indicator');
    const refreshStatusBtn = document.getElementById('refreshStatus');
    const statusLink = document.getElementById('statusLink');
    const paymentLoading = document.getElementById('paymentLoading');
    
    let pollingInterval = null;
    
    /**
     * Carrega dados do pedido via API
     */
    async function loadOrderData() {
        try {
            if (paymentLoading) paymentLoading.style.display = 'flex';
            
            const response = await fetch(`/api/orders/${token}`);
            const data = await response.json();
            
            if (!response.ok || !data.success) {
                throw new Error(data.erro || data.message || 'Erro ao carregar dados do pedido');
            }
            
            const order = data.order;
            
            // Atualizar informações do pedido
            if (paymentAmount) {
                paymentAmount.textContent = formatCurrency(order.valor);
            }
            
            if (orderCode) {
                orderCode.textContent = order.codigo_pedido || '--';
            }
            
            // Atualizar status
            updateStatus(order.status);
            
            // Atualizar link de status
            if (statusLink) {
                statusLink.href = `/status-pedido?token=${token}`;
            }
            
            // Se for Boleto, carregar dados do boleto
            if (order.boleto) {
                // Código de barras
                if (barcode && order.boleto.barcode) {
                    barcode.textContent = order.boleto.barcode;
                }
                
                if (barcodeInput && order.boleto.barcode) {
                    barcodeInput.value = order.boleto.barcode.replace(/\s/g, '');
                }
                
                // Link do boleto
                if (viewBoletoBtn && order.boleto.link) {
                    viewBoletoBtn.href = order.boleto.link;
                    viewBoletoBtn.target = '_blank';
                }
                
                if (downloadBoletoBtn && order.boleto.link) {
                    downloadBoletoBtn.href = order.boleto.link;
                    downloadBoletoBtn.download = `boleto-${order.codigo_pedido}.pdf`;
                }
                
                // Data de vencimento
                if (paymentExpiry && order.boleto.expires_at) {
                    const expiryDate = new Date(order.boleto.expires_at);
                    paymentExpiry.textContent = `Vencimento: ${expiryDate.toLocaleDateString('pt-BR')}`;
                }
            }
            
            // Se o pagamento já foi aprovado, parar polling e redirecionar
            if (order.status === 'PAGO' || order.status === 'APROVADO') {
                stopPolling();
                setTimeout(() => {
                    window.location.href = `/status-pedido?token=${token}`;
                }, 2000);
            }
            
        } catch (error) {
            console.error('Erro ao carregar dados do pedido:', error);
            showError(`Erro ao carregar dados: ${error.message}`);
        } finally {
            if (paymentLoading) paymentLoading.style.display = 'none';
        }
    }
    
    /**
     * Atualiza o status visual do pedido
     */
    function updateStatus(status) {
        if (!statusIndicator || !statusText) return;
        
        // Remover classes de status anteriores
        statusIndicator.className = 'status-indicator';
        
        // Adicionar classe baseada no status
        if (status === 'PENDENTE' || status === 'CRIADO') {
            statusIndicator.classList.add('status-pending');
            if (statusText) statusText.textContent = 'Aguardando Pagamento';
        } else if (status === 'PAGO' || status === 'APROVADO') {
            statusIndicator.classList.add('status-paid');
            if (statusText) statusText.textContent = 'Pagamento Confirmado';
        } else if (status === 'EXPIRADO' || status === 'CANCELADO') {
            statusIndicator.classList.add('status-expired');
            if (statusText) statusText.textContent = status === 'EXPIRADO' ? 'Pagamento Expirado' : 'Pedido Cancelado';
        }
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
        
        // Fazer polling a cada 5 segundos
        pollingInterval = setInterval(async () => {
            try {
                const response = await fetch(`/api/orders/${token}/status`);
                const data = await response.json();
                
                if (data.success && data.status) {
                    updateStatus(data.status);
                    
                    // Se pagamento foi confirmado, recarregar dados completos
                    if (data.status === 'PAGO' || data.status === 'APROVADO') {
                        stopPolling();
                        await loadOrderData();
                    }
                }
            } catch (error) {
                console.error('Erro ao verificar status:', error);
            }
        }, 5000); // 5 segundos
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
     * Mostra mensagem de erro
     */
    function showError(message) {
        const container = document.querySelector('.payment-content');
        if (container) {
            container.innerHTML = `
                <div class="card" style="text-align: center; padding: 40px;">
                    <h2 style="color: #dc3545; margin-bottom: 16px;">Erro</h2>
                    <p style="color: #666; margin-bottom: 24px;">${message}</p>
                    <a href="/checkout" class="btn-primary">Voltar ao Checkout</a>
                </div>
            `;
        }
    }
    
    /**
     * Copia código de barras para área de transferência
     */
    if (copyBarcodeBtn) {
        copyBarcodeBtn.addEventListener('click', async function() {
            if (!barcodeInput || !barcodeInput.value) {
                alert('Código de barras não disponível');
                return;
            }
            
            try {
                await navigator.clipboard.writeText(barcodeInput.value);
                
                // Feedback visual
                const originalText = copyBarcodeBtn.querySelector('.copy-text')?.textContent || 'Copiar';
                copyBarcodeBtn.classList.add('copied');
                if (copyBarcodeBtn.querySelector('.copy-text')) {
                    copyBarcodeBtn.querySelector('.copy-text').textContent = 'Copiado!';
                }
                
                setTimeout(() => {
                    copyBarcodeBtn.classList.remove('copied');
                    if (copyBarcodeBtn.querySelector('.copy-text')) {
                        copyBarcodeBtn.querySelector('.copy-text').textContent = originalText;
                    }
                }, 2000);
            } catch (error) {
                console.error('Erro ao copiar código:', error);
                // Fallback: selecionar texto
                barcodeInput.select();
                document.execCommand('copy');
                alert('Código de barras copiado!');
            }
        });
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
