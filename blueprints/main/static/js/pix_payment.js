// JavaScript para página de pagamento PIX
document.addEventListener('DOMContentLoaded', function() {
    console.log('PIX Payment page loaded');
    
    // Obter token da URL
    const urlParams = new URLSearchParams(window.location.search);
    const token = urlParams.get('token');
    
    if (!token) {
        console.error('Token não fornecido na URL');
        showError('Token de acesso não encontrado. Por favor, acesse esta página através do checkout.');
        return;
    }
    
    // Elementos da página
    const qrCodePlaceholder = document.getElementById('qrCodePlaceholder');
    const qrCodeImage = document.getElementById('qrCodeImage');
    const pixCodeInput = document.getElementById('pixCode');
    const copyPixCodeBtn = document.getElementById('copyPixCode');
    const paymentAmount = document.getElementById('paymentAmount');
    const paymentExpiry = document.getElementById('paymentExpiry');
    const orderCode = document.getElementById('orderCode');
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
            
            // Se for PIX, carregar QR Code e código PIX
            if (order.pix) {
                // Carregar QR Code
                if (qrCodeImage && order.pix.qr_code_image) {
                    qrCodeImage.src = order.pix.qr_code_image;
                    qrCodeImage.style.display = 'block';
                    if (qrCodePlaceholder) qrCodePlaceholder.style.display = 'none';
                } else if (qrCodeImage && order.pix.qr_code_link) {
                    // Tentar usar o link como imagem
                    qrCodeImage.src = order.pix.qr_code_link;
                    qrCodeImage.style.display = 'block';
                    if (qrCodePlaceholder) qrCodePlaceholder.style.display = 'none';
                }
                
                // Carregar código PIX
                if (pixCodeInput && order.pix.qr_code_text) {
                    pixCodeInput.value = order.pix.qr_code_text;
                } else if (pixCodeInput && order.pix.qr_code_link) {
                    // Fallback: usar link se não houver código text
                    pixCodeInput.value = order.pix.qr_code_link;
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
     * Copia código PIX para área de transferência
     */
    if (copyPixCodeBtn) {
        copyPixCodeBtn.addEventListener('click', async function() {
            if (!pixCodeInput || !pixCodeInput.value) {
                alert('Código PIX não disponível');
                return;
            }
            
            try {
                await navigator.clipboard.writeText(pixCodeInput.value);
                
                // Feedback visual
                const originalText = copyPixCodeBtn.querySelector('.copy-text')?.textContent || 'Copiar';
                copyPixCodeBtn.classList.add('copied');
                if (copyPixCodeBtn.querySelector('.copy-text')) {
                    copyPixCodeBtn.querySelector('.copy-text').textContent = 'Copiado!';
                }
                
                setTimeout(() => {
                    copyPixCodeBtn.classList.remove('copied');
                    if (copyPixCodeBtn.querySelector('.copy-text')) {
                        copyPixCodeBtn.querySelector('.copy-text').textContent = originalText;
                    }
                }, 2000);
            } catch (error) {
                console.error('Erro ao copiar código:', error);
                // Fallback: selecionar texto
                pixCodeInput.select();
                document.execCommand('copy');
                alert('Código PIX copiado!');
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
