async function getAuthHeaders() {
    const headers = {
        'Content-Type': 'application/json'
    };

    // A lógica de login Firebase ficaria aqui se você estivesse usando a SDK JS diretamente para autenticação
    // Por simplicidade, vamos assumir que o backend Flask já lida com a sessão para usuários logados
    // e que o X-Session-ID é apenas para anônimos.

    let sessionId = localStorage.getItem('cartSessionId');
    // Se não houver session ID no localStorage, gerar um novo UUID
    // Isso é feito apenas se o usuário NÃO estiver logado.
    // O backend tem a lógica para priorizar o usuário logado (g.user_db_data) sobre o X-Session-ID.
    if (!sessionId) {
        sessionId = crypto.randomUUID(); // Gerar um novo UUID se não existir
        localStorage.setItem('cartSessionId', sessionId);
    }
    headers['X-Session-ID'] = sessionId;
    
    return headers;
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
    const summaryShippingElem = document.getElementById('summary-shipping');
    const summaryDiscountElem = document.getElementById('summary-discount');


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
                summaryShippingElem.textContent = 'A calcular';
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
            summaryShippingElem.textContent = 'A calcular';
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
                    <span class="d-md-none text-muted">Subtotal: </span>
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
        });

        // Atualiza o resumo
        cartTotalPriceElem.textContent = `R$ ${cartData.total_value.toFixed(2).replace('.', ',')}`;
        summarySubtotalElem.textContent = `R$ ${cartData.total_value.toFixed(2).replace('.', ',')}`;
        summaryShippingElem.textContent = 'A calcular'; // Placeholder
        summaryDiscountElem.textContent = '- R$ 0,00'; // Placeholder
        
        if (clearCartBtn) clearCartBtn.disabled = false;
        if (checkoutBtn) checkoutBtn.disabled = false;

        // Adicionar event listeners aos botões de quantidade e remover (DEPOIS que o HTML é renderizado)
        document.querySelectorAll('.plus').forEach(button => {
            button.addEventListener('click', (e) => {
                const cartItemId = e.target.dataset.id;
                const inputElement = document.querySelector(`.quantity-input[data-id="${cartItemId}"]`);
                const currentQuantity = parseInt(inputElement.value);
                updateQuantity(cartItemId, currentQuantity + 1);
            });
        });
        document.querySelectorAll('.minus').forEach(button => {
            button.addEventListener('click', (e) => {
                const cartItemId = e.target.dataset.id;
                const inputElement = document.querySelector(`.quantity-input[data-id="${cartItemId}"]`);
                const currentQuantity = parseInt(inputElement.value);
                updateQuantity(cartItemId, currentQuantity - 1);
            });
        });
        document.querySelectorAll('.remove-btn').forEach(button => {
            button.addEventListener('click', (e) => removeItem(e.target.closest('button').dataset.id));
        });
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
                            <strong style="color: #856404;">Tem certeza que deseja remover este item?</strong>
                        </div>
                        <div style="display: flex; gap: 0.5rem; margin-left: 1rem;">
                            <button class="confirm-remove-yes" style="padding: 0.5rem 1rem; background: #dc3545; color: white; border: none; border-radius: 6px; cursor: pointer; font-weight: 600;">
                                Sim
                            </button>
                            <button class="confirm-remove-no" style="padding: 0.5rem 1rem; background: #6c757d; color: white; border: none; border-radius: 6px; cursor: pointer; font-weight: 600;">
                                Não
                            </button>
                        </div>
                    </div>
                `;
                messagesContainer.appendChild(confirmMessage);
                
                confirmMessage.querySelector('.confirm-remove-yes').onclick = () => {
                    messagesContainer.removeChild(confirmMessage);
                    resolve(true);
                };
                confirmMessage.querySelector('.confirm-remove-no').onclick = () => {
                    messagesContainer.removeChild(confirmMessage);
                    resolve(false);
                };
            });
            
            if (!confirmed) return;
        } else {
            // Fallback para confirm nativo se MessageHelper não estiver disponível
        if (!confirm('Tem certeza que deseja remover este item do carrinho?')) {
            return;
            }
        }

        try {
            // Mostrar loading no botão
            if (removeBtn) {
                const originalHTML = removeBtn.innerHTML;
                removeBtn.disabled = true;
                removeBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
                
            const response = await fetch(`/api/cart/remove/${cartItemId}`, {
                method: 'DELETE',
                headers: await getAuthHeaders()
            });

            if (!response.ok) {
                const errorData = await response.json();
                    if (messagesContainer && window.MessageHelper) {
                        window.MessageHelper.showError(`Erro ao remover item: ${errorData.erro || 'Ocorreu um erro.'}`, messagesContainer);
                    }
                    removeBtn.disabled = false;
                    removeBtn.innerHTML = originalHTML;
                throw new Error(`HTTP error! status: ${response.status}`);
            }

                if (messagesContainer && window.MessageHelper) {
                    window.MessageHelper.showSuccess('Item removido do carrinho!', messagesContainer, 2000);
            }

            fetchAndRenderCart(); // Recarrega o carrinho após remover

            } else {
                const response = await fetch(`/api/cart/remove/${cartItemId}`, {
                    method: 'DELETE',
                    headers: await getAuthHeaders()
                });

                if (!response.ok) {
                    const errorData = await response.json();
                    if (messagesContainer && window.MessageHelper) {
                        window.MessageHelper.showError(`Erro ao remover item: ${errorData.erro || 'Ocorreu um erro.'}`, messagesContainer);
                    }
                    throw new Error(`HTTP error! status: ${response.status}`);
                }

                if (messagesContainer && window.MessageHelper) {
                    window.MessageHelper.showSuccess('Item removido do carrinho!', messagesContainer, 2000);
                }

                fetchAndRenderCart();
            }

        } catch (error) {
            console.error('Erro ao remover item:', error);
        } finally {
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

    // Adicionar evento de submit para o formulário de cupom (lógica mocada)
    const couponForm = document.getElementById('couponForm');
    if (couponForm) {
        couponForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const messagesContainer = document.getElementById('cart-messages-container');
            const couponInput = this.querySelector('input[type="text"]');
            const applyBtn = this.querySelector('button[type="submit"]');
            const couponCode = couponInput.value.trim();
            
            if (couponCode !== '') {
                // Mostrar loading no botão
                if (applyBtn) {
                    const originalHTML = applyBtn.innerHTML;
                    applyBtn.disabled = true;
                    if (window.LoadingHelper) {
                        window.LoadingHelper.setButtonLoading(applyBtn, 'Aplicando...');
                    } else {
                        applyBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Aplicando...';
                    }
                    
                    // Simular delay (remover quando implementar backend)
                    setTimeout(() => {
                        if (messagesContainer && window.MessageHelper) {
                            window.MessageHelper.showSuccess(`Cupom "${couponCode}" aplicado com sucesso! (Função de cupom mocada)`, messagesContainer, 3000);
                        }
                        if (window.LoadingHelper) {
                            window.LoadingHelper.restoreButton(applyBtn, { innerHTML: originalHTML });
                        } else {
                            applyBtn.disabled = false;
                            applyBtn.innerHTML = originalHTML;
                        }
                        couponInput.value = '';
                    }, 1000);
                } else {
                    if (messagesContainer && window.MessageHelper) {
                        window.MessageHelper.showSuccess(`Cupom "${couponCode}" aplicado com sucesso! (Função de cupom mocada)`, messagesContainer, 3000);
                    }
                }
                // Aqui você faria uma chamada AJAX para validar e aplicar o cupom no backend
                // e então recarregaria o carrinho para atualizar os valores.
            } else {
                if (messagesContainer && window.MessageHelper) {
                    window.MessageHelper.showError('Por favor, insira um código de cupom.', messagesContainer);
            } else {
                alert('Por favor, insira um código de cupom.');
                }
                couponInput.focus();
            }
        });
    }

    // Carrega o carrinho quando a página é carregada
    fetchAndRenderCart();
});