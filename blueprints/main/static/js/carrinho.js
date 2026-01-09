async function getAuthHeaders() {
    const headers = {
        'Content-Type': 'application/json'
    };

    let sessionId = localStorage.getItem('cartSessionId');
    if (!sessionId) {
        sessionId = crypto.randomUUID();
        localStorage.setItem('cartSessionId', sessionId);
    }
    headers['X-Session-ID'] = sessionId;
    
    // Adicionar token Firebase se disponível
    try {
        const { initializeApp } = await import('https://www.gstatic.com/firebasejs/10.12.2/firebase-app.js');
        const { getAuth } = await import('https://www.gstatic.com/firebasejs/10.12.2/firebase-auth.js');
        
        const firebaseConfig = {
            apiKey: "AIzaSyDd13Tl9dJaUqIvNhGWakoEbpYqw7ZrB7Y",
            authDomain: "lhamabanana-981d5.firebaseapp.com",
            projectId: "lhamabanana-981d5",
            storageBucket: "lhamabanana-981d5.firebasestorage.app",
            messagingSenderId: "209130422039",
            appId: "1:209130422039:web:70fcf2089fa90715364152",
            measurementId: "G-4XQSZZB0JK"
        };
        
        const app = initializeApp(firebaseConfig);
        const auth = getAuth(app);
        
        const user = auth.currentUser;
        if (user) {
            const idToken = await user.getIdToken();
            headers['Authorization'] = `Bearer ${idToken}`;
        }
    } catch (error) {
        // Firebase não disponível ou usuário não logado
        console.log('Firebase não disponível ou usuário não logado');
    }
    
    return headers;
}

// Função auxiliar para verificar se o usuário está logado
async function isUserLoggedIn() {
    try {
        const { initializeApp } = await import('https://www.gstatic.com/firebasejs/10.12.2/firebase-app.js');
        const { getAuth } = await import('https://www.gstatic.com/firebasejs/10.12.2/firebase-auth.js');
        
        const firebaseConfig = {
            apiKey: "AIzaSyDd13Tl9dJaUqIvNhGWakoEbpYqw7ZrB7Y",
            authDomain: "lhamabanana-981d5.firebaseapp.com",
            projectId: "lhamabanana-981d5",
            storageBucket: "lhamabanana-981d5.firebasestorage.app",
            messagingSenderId: "209130422039",
            appId: "1:209130422039:web:70fcf2089fa90715364152",
            measurementId: "G-4XQSZZB0JK"
        };
        
        const app = initializeApp(firebaseConfig);
        const auth = getAuth(app);
        return auth.currentUser !== null;
    } catch (error) {
        return false;
    }
}


document.addEventListener('DOMContentLoaded', async function() {
    const cartItemsList = document.getElementById('cart-items-list');
    const cartTotalPriceElem = document.getElementById('cart-total-price');
    const clearCartBtn = document.getElementById('clear-cart-btn');
    const checkoutBtn = document.getElementById('checkout-btn');
    const emptyCartMessage = document.getElementById('empty-cart-message');
    const cartHeader = document.querySelector('.cart-header');
    const cartSummaryContainer = document.querySelector('.cart-summary-container');
    const summarySubtotalElem = document.getElementById('summary-subtotal');
    const summaryDiscountElem = document.getElementById('summary-discount');

    // Configurar delegação de eventos para o botão de remover (uma vez, no container pai)
    if (cartItemsList) {
        cartItemsList.addEventListener('click', function(e) {
            console.log('Clique detectado no carrinho:', e.target);
            // Verificar se o clique foi no botão de remover ou em seus filhos (ícone, texto)
            const removeBtn = e.target.closest('.remove-btn');
            if (removeBtn) {
                console.log('Botão de remover encontrado:', removeBtn);
                e.preventDefault();
                e.stopPropagation();
                const cartItemId = removeBtn.getAttribute('data-id');
                console.log('ID do item do carrinho:', cartItemId);
                if (cartItemId) {
                    removeItem(parseInt(cartItemId));
                } else {
                    console.error('ID do item do carrinho não encontrado!');
                }
            }
        });
    }


    /**
     * Busca os itens do carrinho do backend e os renderiza.
     */
    async function fetchAndRenderCart() {
        try {
            const response = await fetch('/api/cart', {
                method: 'GET',
                headers: await getAuthHeaders()
            });

            // Verificar se a resposta foi bem-sucedida
            if (response.ok) {
                try {
            const cartData = await response.json();
            console.log("Dados do carrinho recebidos:", cartData);
            renderCart(cartData);
                    return;
                } catch (jsonError) {
                    console.error('Erro ao parsear JSON da resposta:', jsonError);
                    // Se não conseguir parsear JSON mas a resposta foi OK, tratar como vazio
                    renderCart({ items: [], total_value: 0 });
                    return;
                }
            }

            // Se a resposta não foi OK, verificar o status
            const status = response.status;
            console.log('Resposta não OK, status:', status);

            // Apenas mostrar erro para status 500 (erro interno do servidor)
            // Outros status (404, 401, etc) são tratados como carrinho vazio
            if (status === 500) {
                let errorMessage = 'Não foi possível carregar o carrinho. Tente novamente mais tarde.';
                
                // Tentar obter mensagem de erro do backend
                try {
                    const errorData = await response.json();
                    if (errorData.erro) {
                        errorMessage = errorData.erro;
                    }
                } catch (e) {
                    // Se não conseguir parsear JSON, usar mensagem padrão
                    console.log('Não foi possível parsear resposta de erro');
                }
                
                const messagesContainer = document.getElementById('cart-messages-container');
                if (messagesContainer && window.MessageHelper) {
                    window.MessageHelper.showError(errorMessage, messagesContainer);
                } else {
                    cartItemsList.innerHTML = `<p style="color: #dc3545; padding: 1rem; text-align: center;">${errorMessage}</p>`;
                }
                
            cartTotalPriceElem.textContent = 'R$ --,--';
            summarySubtotalElem.textContent = 'R$ --,--';
            summaryDiscountElem.textContent = '- R$ 0,00';
            
                if (emptyCartMessage) emptyCartMessage.style.display = 'none';
            if (cartHeader) cartHeader.style.display = 'none';
            if (cartSummaryContainer) cartSummaryContainer.style.display = 'none';
                return;
            }
            
            // Para outros status (404, 401, 403, etc), tratar como carrinho vazio
            // Isso é normal quando o usuário não tem itens no carrinho ou não está logado
            console.log('Status', status, '- tratando como carrinho vazio');
            renderCart({ items: [], total_value: 0 });

        } catch (error) {
            console.error('Erro ao buscar carrinho:', error);
            
            // Erros de rede ou outros erros não tratados são mostrados como carrinho vazio
            // Apenas erros 500 explícitos do servidor mostram mensagem de erro
            console.log('Erro de conexão ou exceção - tratando como carrinho vazio');
            renderCart({ items: [], total_value: 0 });
        }
    }

    /**
     * Renderiza os itens do carrinho no HTML.
     */
    function renderCart(cartData) {
        // Limpar mensagens de erro anteriores
        const messagesContainer = document.getElementById('cart-messages-container');
        if (messagesContainer && window.MessageHelper) {
            window.MessageHelper.clearMessages(messagesContainer);
        }
        
        cartItemsList.innerHTML = ''; // Limpa a lista atual

        // Verificar se o carrinho está vazio
        if (!cartData || !cartData.items || cartData.items.length === 0) {
            // Mostrar mensagem de carrinho vazio
            if (emptyCartMessage) {
                emptyCartMessage.style.display = 'block';
            }
            if (cartHeader) {
                cartHeader.style.display = 'none';
            }
            if (cartSummaryContainer) {
                cartSummaryContainer.style.display = 'none';
            }
            cartTotalPriceElem.textContent = 'R$ 0,00';
            summarySubtotalElem.textContent = 'R$ 0,00';
            summaryDiscountElem.textContent = '- R$ 0,00';
            if (clearCartBtn) clearCartBtn.disabled = true;
            if (checkoutBtn) checkoutBtn.disabled = true;
            return;
        }

        // Se houver itens, mostra as seções do carrinho e esconde a mensagem de vazio
        if (emptyCartMessage) emptyCartMessage.style.display = 'none';
        if (cartHeader) cartHeader.style.display = 'grid'; // Ou block, dependendo do seu CSS original
        if (cartSummaryContainer) cartSummaryContainer.style.display = 'block';


        cartData.items.forEach(item => {
            const itemElement = document.createElement('div');
            itemElement.classList.add('cart-item');
            itemElement.innerHTML = `
                <div class="cart-item-image-container">
                    <img src="${item.image_url}" alt="${item.product_name}" class="cart-item-image">
                </div>
                
                <div class="cart-item-details">
                    <h3>${item.product_name}</h3>
                    <span class="cart-item-category">${item.estampa_name} / ${item.tamanho_name}</span>
                    <p class="d-md-none">
                        <span class="text-muted">Preço: </span>
                        <span class="cart-item-price">R$ ${item.price_at_time_of_add.toFixed(2).replace('.', ',')}</span>
                    </p>
                </div>
                
                <div class="cart-item-price text-md-center d-none d-md-block">
                    R$ ${item.price_at_time_of_add.toFixed(2).replace('.', ',')}
                </div>
                
                <div class="cart-item-quantity">
                    <div class="quantity-selector">
                        <button type="button" class="quantity-btn minus" data-id="${item.cart_item_id}">-</button>
                        <input type="number" class="quantity-input" 
                               value="${item.quantity}" 
                               min="1" 
                               max="999" {# Max de estoque real deveria vir do backend #}
                               data-id="${item.cart_item_id}">
                        <button type="button" class="quantity-btn plus" data-id="${item.cart_item_id}">+</button>
                    </div>
                </div>
                
                <div class="cart-item-subtotal text-md-center">
                    <strong>R$ ${item.item_total.toFixed(2).replace('.', ',')}</strong>
                </div>
                
                <div class="cart-item-actions">
                    <button type="button" class="remove-btn" data-id="${item.cart_item_id}" title="Remover">
                        <i class="far fa-trash-alt"></i>
                        <span class="d-md-none">Remover</span>
                    </button>
                </div>
            `;
            cartItemsList.appendChild(itemElement);
            
            // Adicionar event listener diretamente ao botão de remover após criar o elemento
            const removeBtn = itemElement.querySelector('.remove-btn');
            if (removeBtn) {
                removeBtn.addEventListener('click', function(e) {
                    e.preventDefault();
                    e.stopPropagation();
                    console.log('Botão de remover clicado, cartItemId:', item.cart_item_id);
                    // Prevenir múltiplos cliques
                    if (removeBtn.disabled) {
                        console.log('Botão já está desabilitado, ignorando clique');
                        return;
                    }
                    removeItem(item.cart_item_id);
                });
            }
        });

        // Atualiza o resumo (sem frete, pois é calculado apenas no checkout)
        const subtotal = cartData.total_value;
        
        // Aplicar desconto do cupom se existir
        let totalComDesconto = subtotal;
        if (appliedDiscount > 0) {
            totalComDesconto = Math.max(0, subtotal - appliedDiscount);
            if (summaryDiscountElem) {
                summaryDiscountElem.textContent = `- R$ ${appliedDiscount.toFixed(2).replace('.', ',')}`;
                summaryDiscountElem.style.color = '#28a745';
            }
        } else {
            if (summaryDiscountElem) {
                summaryDiscountElem.textContent = '- R$ 0,00';
                summaryDiscountElem.style.color = '';
            }
        }
        
        cartTotalPriceElem.textContent = `R$ ${totalComDesconto.toFixed(2).replace('.', ',')}`;
        summarySubtotalElem.textContent = `R$ ${subtotal.toFixed(2).replace('.', ',')}`;
        
        if (clearCartBtn) clearCartBtn.disabled = false;
        if (checkoutBtn) checkoutBtn.disabled = false;

        // Adicionar event listeners aos botões de quantidade e remover (DEPOIS que o HTML é renderizado)
        document.querySelectorAll('.plus').forEach(button => {
            button.addEventListener('click', (e) => {
                const cartItemId = e.target.dataset.id;
                const inputElement = document.querySelector(`.quantity-input[data-id="${cartItemId}"]`);
                const currentQuantity = parseInt(inputElement.value) || 1;
                updateQuantity(cartItemId, currentQuantity + 1);
            });
        });
        document.querySelectorAll('.minus').forEach(button => {
            button.addEventListener('click', (e) => {
                const cartItemId = e.target.dataset.id;
                const inputElement = document.querySelector(`.quantity-input[data-id="${cartItemId}"]`);
                const currentQuantity = parseInt(inputElement.value) || 1;
                updateQuantity(cartItemId, currentQuantity - 1);
            });
        });
        // Adicionar event listener para quando o usuário digitar no campo de quantidade
        document.querySelectorAll('.quantity-input').forEach(input => {
            // Atualizar quando o campo perder o foco (blur)
            input.addEventListener('blur', (e) => {
                const cartItemId = e.target.dataset.id;
                const newQuantity = parseInt(e.target.value) || 1;
                // Validar quantidade mínima
                if (newQuantity < 1) {
                    e.target.value = 1;
                    updateQuantity(cartItemId, 1);
                } else {
                    updateQuantity(cartItemId, newQuantity);
                }
            });
            // Validar enquanto digita (opcional, para melhor UX)
            input.addEventListener('input', (e) => {
                const value = e.target.value;
                // Permitir apenas números
                if (value && !/^\d+$/.test(value)) {
                    e.target.value = value.replace(/\D/g, '');
                }
            });
        });
        // Event listeners para botões de quantidade já foram adicionados acima
        // O botão de remover usa delegação de eventos configurada no início do DOMContentLoaded
    }

    /**
     * Atualiza a quantidade de um item no carrinho via API.
     */
    async function updateQuantity(cartItemId, newQuantity) {
        // Validação básica no frontend para melhor UX
        if (newQuantity < 1) {
            newQuantity = 0; // Se a quantidade for 0, o backend vai remover o item
        }

        const messagesContainer = document.getElementById('cart-messages-container');
        const quantityInput = document.querySelector(`.quantity-input[data-id="${cartItemId}"]`);
        const originalValue = quantityInput ? quantityInput.value : newQuantity;

        try {
            // Mostrar loading no input
            if (quantityInput) {
                quantityInput.disabled = true;
                quantityInput.style.opacity = '0.6';
            }

            const response = await fetch(`/api/cart/update/${cartItemId}`, {
                method: 'PUT',
                headers: await getAuthHeaders(),
                body: JSON.stringify({ quantity: newQuantity })
            });

            if (!response.ok) {
                const errorData = await response.json();
                if (messagesContainer && window.MessageHelper) {
                    window.MessageHelper.showError(`Erro ao atualizar quantidade: ${errorData.erro || 'Ocorreu um erro.'}`, messagesContainer);
                }
                // Restaurar valor original
                if (quantityInput) quantityInput.value = originalValue;
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            // Mensagem de sucesso (opcional, pode ser removida se preferir)
            if (messagesContainer && window.MessageHelper && newQuantity > 0) {
                window.MessageHelper.showSuccess('Quantidade atualizada!', messagesContainer, 2000);
            }

            fetchAndRenderCart(); // Recarrega o carrinho para refletir as mudanças

        } catch (error) {
            console.error('Erro ao atualizar quantidade:', error);
        } finally {
            if (quantityInput) {
                quantityInput.disabled = false;
                quantityInput.style.opacity = '1';
            }
        }
    }

    /**
     * Remove um item do carrinho via API.
     */
    async function removeItem(cartItemId) {
        const messagesContainer = document.getElementById('cart-messages-container');
        const removeBtn = document.querySelector(`.remove-btn[data-id="${cartItemId}"]`);

        try {
            // Mostrar loading no botão
            const originalHTML = removeBtn ? removeBtn.innerHTML : '';
            if (removeBtn) {
                removeBtn.disabled = true;
                removeBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
            }
            
            console.log('Fazendo requisição DELETE para /api/cart/remove/' + cartItemId);
            const response = await fetch(`/api/cart/remove/${cartItemId}`, {
                method: 'DELETE',
                headers: await getAuthHeaders()
            });

            console.log('Resposta recebida:', response.status, response.statusText);

            if (!response.ok) {
                let errorData = {};
                try {
                    errorData = await response.json();
                } catch (e) {
                    console.error('Erro ao parsear resposta de erro:', e);
                }
                console.error('Erro na resposta:', errorData);
                if (messagesContainer && window.MessageHelper) {
                    window.MessageHelper.showError(`Erro ao remover item: ${errorData.erro || 'Ocorreu um erro.'}`, messagesContainer);
                }
                if (removeBtn) {
                    removeBtn.disabled = false;
                    removeBtn.innerHTML = originalHTML;
                }
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const responseData = await response.json();
            console.log('Item removido com sucesso:', responseData);

            if (messagesContainer && window.MessageHelper) {
                window.MessageHelper.showSuccess('Item removido do carrinho!', messagesContainer, 2000);
            }

            fetchAndRenderCart(); // Recarrega o carrinho após remover

        } catch (error) {
            console.error('Erro ao remover item:', error);
            if (messagesContainer && window.MessageHelper) {
                window.MessageHelper.showError('Erro ao remover item. Tente novamente.', messagesContainer);
            }
        } finally {
            const currentRemoveBtn = document.querySelector(`.remove-btn[data-id="${cartItemId}"]`);
            if (currentRemoveBtn && originalHTML) {
                currentRemoveBtn.disabled = false;
                if (currentRemoveBtn.innerHTML.includes('fa-spinner')) {
                    currentRemoveBtn.innerHTML = originalHTML;
                }
            }
        }
    }

    /**
     * Limpa todo o carrinho via API.
     */
    async function clearCart() {
        const messagesContainer = document.getElementById('cart-messages-container');
        
        // Criar modal de confirmação inline
        if (messagesContainer && window.MessageHelper) {
            const confirmed = await new Promise((resolve) => {
                const confirmMessage = document.createElement('div');
                confirmMessage.className = 'inline-message inline-message-warning';
                confirmMessage.style.cssText = 'padding: 1rem; margin-bottom: 1rem; border-radius: 8px; background: #fff3cd; border: 1px solid #ffc107;';
                confirmMessage.innerHTML = `
                    <div style="display: flex; align-items: center; justify-content: space-between;">
                        <div style="flex: 1;">
                            <i class="fas fa-exclamation-triangle" style="color: #856404; margin-right: 0.5rem;"></i>
                            <strong style="color: #856404;">Tem certeza que deseja limpar todo o carrinho?</strong>
                        </div>
                        <div style="display: flex; gap: 0.5rem; margin-left: 1rem;">
                            <button class="confirm-clear-yes" style="padding: 0.5rem 1rem; background: #dc3545; color: white; border: none; border-radius: 6px; cursor: pointer; font-weight: 600;">
                                Sim
                            </button>
                            <button class="confirm-clear-no" style="padding: 0.5rem 1rem; background: #6c757d; color: white; border: none; border-radius: 6px; cursor: pointer; font-weight: 600;">
                                Não
                            </button>
                        </div>
                    </div>
                `;
                messagesContainer.appendChild(confirmMessage);
                
                confirmMessage.querySelector('.confirm-clear-yes').onclick = () => {
                    messagesContainer.removeChild(confirmMessage);
                    resolve(true);
                };
                confirmMessage.querySelector('.confirm-clear-no').onclick = () => {
                    messagesContainer.removeChild(confirmMessage);
                    resolve(false);
                };
            });
            
            if (!confirmed) return;
        } else {
            // Fallback para confirm nativo
        if (!confirm('Tem certeza que deseja limpar todo o carrinho?')) {
            return;
        }
        }

        try {
            // Mostrar loading no botão
            if (clearCartBtn) {
                const originalHTML = clearCartBtn.innerHTML;
                clearCartBtn.disabled = true;
                if (window.LoadingHelper) {
                    window.LoadingHelper.setButtonLoading(clearCartBtn, 'Limpando...');
                } else {
                    clearCartBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Limpando...';
                }
            }

            const response = await fetch('/api/cart/clear', {
                method: 'DELETE',
                headers: await getAuthHeaders()
            });

            if (!response.ok) {
                const errorData = await response.json();
                if (messagesContainer && window.MessageHelper) {
                    window.MessageHelper.showError(`Erro ao limpar carrinho: ${errorData.erro || 'Ocorreu um erro.'}`, messagesContainer);
                }
                if (clearCartBtn && window.LoadingHelper) {
                    window.LoadingHelper.restoreButton(clearCartBtn, { innerHTML: originalHTML });
                } else if (clearCartBtn) {
                    clearCartBtn.disabled = false;
                    clearCartBtn.innerHTML = originalHTML;
                }
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            if (messagesContainer && window.MessageHelper) {
                window.MessageHelper.showSuccess('Carrinho limpo com sucesso!', messagesContainer, 2000);
            }

            fetchAndRenderCart(); // Recarrega o carrinho (agora vazio)

        } catch (error) {
            console.error('Erro ao limpar carrinho:', error);
        } finally {
            if (clearCartBtn && window.LoadingHelper) {
                window.LoadingHelper.restoreButton(clearCartBtn, { innerHTML: 'Limpar Carrinho' });
            } else if (clearCartBtn) {
                clearCartBtn.disabled = false;
            }
        }
    }

    // Event Listeners para os botões principais
    if (clearCartBtn) {
        clearCartBtn.addEventListener('click', clearCart);
    }
    if (checkoutBtn) {
        checkoutBtn.addEventListener('click', () => {
            const messagesContainer = document.getElementById('cart-messages-container');
            
            // Verificar se o carrinho tem itens antes de redirecionar
            if (cartItemsList && cartItemsList.children.length === 0) {
                if (messagesContainer && window.MessageHelper) {
                    window.MessageHelper.showError('Seu carrinho está vazio. Adicione produtos antes de finalizar a compra.', messagesContainer);
                } else {
                alert('Seu carrinho está vazio. Adicione produtos antes de finalizar a compra.');
                }
                return;
            }
            
            // Mostrar loading no botão
            if (window.LoadingHelper) {
                window.LoadingHelper.setButtonLoading(checkoutBtn, 'Redirecionando...');
            } else {
                checkoutBtn.disabled = true;
                const originalHTML = checkoutBtn.innerHTML;
                checkoutBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Redirecionando...';
            }
            
            // Redirecionar para a página de checkout
            window.location.href = '/checkout';
        });
    }

    // Variável global para armazenar o cupom aplicado
    let appliedCoupon = null;
    let appliedDiscount = 0;

    // Adicionar evento de submit para o formulário de cupom
    const couponForm = document.getElementById('couponForm');
    if (couponForm) {
        couponForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            const messagesContainer = document.getElementById('cart-messages-container');
            const couponInput = this.querySelector('input[type="text"]');
            const applyBtn = this.querySelector('button[type="submit"]');
            const couponCode = couponInput.value.trim().toUpperCase();
            
            if (!couponCode) {
                if (messagesContainer && window.MessageHelper) {
                    window.MessageHelper.showError('Por favor, insira um código de cupom.', messagesContainer);
                }
                couponInput.focus();
                return;
            }

            // Verificar se o usuário está logado
            const loggedIn = await isUserLoggedIn();
            if (!loggedIn) {
                // Mostrar mensagem explicando que precisa de conta
                if (messagesContainer) {
                    const messageDiv = document.createElement('div');
                    messageDiv.className = 'message warning';
                    messageDiv.style.cssText = 'margin: 1rem 0; padding: 1rem; background: #fff3cd; border: 1px solid #ffc107; border-radius: 8px;';
                    messageDiv.innerHTML = `
                        <div style="display: flex; align-items: center; gap: 1rem; margin-bottom: 1rem;">
                            <i class="fas fa-info-circle" style="font-size: 1.5rem; color: #856404;"></i>
                            <div style="flex: 1;">
                                <strong style="color: #856404; display: block; margin-bottom: 0.5rem;">Conta necessária para usar cupons</strong>
                                <p style="margin: 0; color: #856404;">Para usar cupons de desconto, você precisa ter uma conta cadastrada.</p>
                            </div>
                        </div>
                        <button type="button" class="btn btn-primary" onclick="window.location.href='/auth/register'" style="width: 100%;">
                            <i class="fas fa-user-plus"></i> Criar Conta
                        </button>
                    `;
                    messagesContainer.innerHTML = '';
                    messagesContainer.appendChild(messageDiv);
                    messagesContainer.style.display = 'block';
                }
                couponInput.focus();
                return;
            }

                // Mostrar loading no botão
            let loadingState = null;
                if (applyBtn) {
                if (window.LoadingHelper) {
                    loadingState = window.LoadingHelper.setButtonLoading(applyBtn, 'Aplicando...');
                } else {
                    const originalHTML = applyBtn.innerHTML;
                    applyBtn.disabled = true;
                        applyBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Aplicando...';
                    applyBtn.dataset.originalHTML = originalHTML;
                }
            }

            try {
                // Obter valor total do carrinho
                const cartTotal = cartData?.total_value || 0;
                
                // Chamar API para validar cupom
                const headers = await getAuthHeaders();
                const response = await fetch('/api/cupom/validate', {
                    method: 'POST',
                    headers: headers,
                    body: JSON.stringify({
                        codigo: couponCode,
                        valor_total_carrinho: cartTotal
                    })
                });

                const result = await response.json();

                if (response.ok && result.success) {
                    // Cupom válido - aplicar desconto
                    appliedCoupon = result.cupom;
                    appliedDiscount = result.desconto;
                    
                    // Atualizar exibição do desconto
                    if (summaryDiscountElem) {
                        summaryDiscountElem.textContent = `- R$ ${appliedDiscount.toFixed(2).replace('.', ',')}`;
                        summaryDiscountElem.style.color = '#28a745';
                    }
                    
                    // Atualizar total
                    const newTotal = Math.max(0, cartTotal - appliedDiscount);
                    if (cartTotalPriceElem) {
                        cartTotalPriceElem.textContent = `R$ ${newTotal.toFixed(2).replace('.', ',')}`;
                    }

                    // Mostrar mensagem de sucesso
                        if (messagesContainer && window.MessageHelper) {
                        window.MessageHelper.showSuccess(`Cupom "${couponCode}" aplicado com sucesso! Desconto de R$ ${appliedDiscount.toFixed(2).replace('.', ',')}`, messagesContainer, 3000);
                    }

                    // Limpar campo
                    couponInput.value = '';
                    
                    // Salvar cupom no localStorage para manter após recarregar
                    localStorage.setItem('appliedCoupon', JSON.stringify({
                        codigo: couponCode,
                        desconto: appliedDiscount,
                        cupom: appliedCoupon
                    }));
                } else {
                    // Erro ao validar cupom
                    let errorMessage = result.erro || 'Erro ao validar cupom';
                    
                    if (result.requer_login) {
                        // Mostrar mensagem de login necessária
                        if (messagesContainer) {
                            const messageDiv = document.createElement('div');
                            messageDiv.className = 'message warning';
                            messageDiv.style.cssText = 'margin: 1rem 0; padding: 1rem; background: #fff3cd; border: 1px solid #ffc107; border-radius: 8px;';
                            messageDiv.innerHTML = `
                                <div style="display: flex; align-items: center; gap: 1rem; margin-bottom: 1rem;">
                                    <i class="fas fa-info-circle" style="font-size: 1.5rem; color: #856404;"></i>
                                    <div style="flex: 1;">
                                        <strong style="color: #856404; display: block; margin-bottom: 0.5rem;">${result.mensagem || errorMessage}</strong>
                                    </div>
                                </div>
                                <button type="button" class="btn btn-primary" onclick="window.location.href='/auth/register'" style="width: 100%;">
                                    <i class="fas fa-user-plus"></i> Criar Conta
                                </button>
                            `;
                            messagesContainer.innerHTML = '';
                            messagesContainer.appendChild(messageDiv);
                            messagesContainer.style.display = 'block';
                        }
                        } else {
                        if (messagesContainer && window.MessageHelper) {
                            window.MessageHelper.showError(errorMessage, messagesContainer);
                        }
                    }
                }
            } catch (error) {
                console.error('Erro ao aplicar cupom:', error);
                if (messagesContainer && window.MessageHelper) {
                    window.MessageHelper.showError('Erro ao aplicar cupom. Tente novamente.', messagesContainer);
                }
            } finally {
                // Restaurar botão
                if (applyBtn) {
                    if (window.LoadingHelper && loadingState) {
                        window.LoadingHelper.restoreButton(applyBtn, loadingState);
            } else {
                        applyBtn.disabled = false;
                        applyBtn.innerHTML = applyBtn.dataset.originalHTML || 'Aplicar';
                    }
                }
            }
        });
    }

    // Carregar cupom aplicado do localStorage ao carregar a página
    function loadAppliedCoupon() {
        try {
            const savedCoupon = localStorage.getItem('appliedCoupon');
            if (savedCoupon) {
                const couponData = JSON.parse(savedCoupon);
                appliedCoupon = couponData.cupom;
                appliedDiscount = couponData.desconto || 0;
                
                // Atualizar exibição
                if (summaryDiscountElem && appliedDiscount > 0) {
                    summaryDiscountElem.textContent = `- R$ ${appliedDiscount.toFixed(2).replace('.', ',')}`;
                    summaryDiscountElem.style.color = '#28a745';
                }
                
                // Preencher campo de cupom
                const couponInput = document.querySelector('#couponForm input[type="text"]');
                if (couponInput && couponData.codigo) {
                    couponInput.value = couponData.codigo;
                }
            }
        } catch (error) {
            console.error('Erro ao carregar cupom aplicado:', error);
        }
    }

    // Carregar cupom ao iniciar
    loadAppliedCoupon();

    // Carrega o carrinho quando a página é carregada
    fetchAndRenderCart();
});