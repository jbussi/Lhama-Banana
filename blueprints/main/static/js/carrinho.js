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
            const response = await fetch('http://localhost:80/api/cart', {
                method: 'GET',
                headers: await getAuthHeaders() // Usar await aqui
            });

            if (!response.ok) {
                const errorData = await response.json();
                console.error('Erro detalhado ao buscar carrinho:', errorData);
                throw new Error(`HTTP error! status: ${response.status} - ${errorData.erro || 'Erro desconhecido'}`);
            }

            const cartData = await response.json();
            console.log("Dados do carrinho recebidos:", cartData);
            renderCart(cartData);

        } catch (error) {
            console.error('Erro ao buscar carrinho:', error);
            cartItemsList.innerHTML = '<p>Não foi possível carregar o carrinho. Tente novamente mais tarde.</p>';
            cartTotalPriceElem.textContent = 'R$ --,--';
            summarySubtotalElem.textContent = 'R$ --,--';
            summaryShippingElem.textContent = 'A calcular';
            summaryDiscountElem.textContent = '- R$ 0,00';
            
            // Se houve um erro, presumimos que o carrinho está "vazio" ou inacessível
            if (emptyCartMessage) emptyCartMessage.style.display = 'block';
            if (cartHeader) cartHeader.style.display = 'none';
            if (cartSummaryContainer) cartSummaryContainer.style.display = 'none';

        } finally {

        }
    }

    /**
     * Renderiza os itens do carrinho no HTML.
     */
    function renderCart(cartData) {
        cartItemsList.innerHTML = ''; // Limpa a lista atual

        if (!cartData.items || cartData.items.length === 0) {
            if (emptyCartMessage) emptyCartMessage.style.display = 'block';
            if (cartHeader) cartHeader.style.display = 'none';
            if (cartSummaryContainer) cartSummaryContainer.style.display = 'none';
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

        try {
            const response = await fetch(`http://localhost:80/api/cart/update/${cartItemId}`, {
                method: 'PUT',
                headers: await getAuthHeaders(),
                body: JSON.stringify({ quantity: newQuantity })
            });

            if (!response.ok) {
                const errorData = await response.json();
                alert(`Erro ao atualizar quantidade: ${errorData.erro || 'Ocorreu um erro.'}`);
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            fetchAndRenderCart(); // Recarrega o carrinho para refletir as mudanças

        } catch (error) {
            console.error('Erro ao atualizar quantidade:', error);
        } finally {
        }
    }

    /**
     * Remove um item do carrinho via API.
     */
    async function removeItem(cartItemId) {
        if (!confirm('Tem certeza que deseja remover este item do carrinho?')) {
            return;
        }
        try {
            const response = await fetch(`http://localhost:80/api/cart/remove/${cartItemId}`, {
                method: 'DELETE',
                headers: await getAuthHeaders()
            });

            if (!response.ok) {
                const errorData = await response.json();
                alert(`Erro ao remover item: ${errorData.erro || 'Ocorreu um erro.'}`);
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            fetchAndRenderCart(); // Recarrega o carrinho após remover

        } catch (error) {
            console.error('Erro ao remover item:', error);
        } finally {
        }
    }

    /**
     * Limpa todo o carrinho via API.
     */
    async function clearCart() {
        if (!confirm('Tem certeza que deseja limpar todo o carrinho?')) {
            return;
        }
        try {
            const response = await fetch('http://localhost:80/api/cart/clear', {
                method: 'DELETE',
                headers: await getAuthHeaders()
            });

            if (!response.ok) {
                const errorData = await response.json();
                alert(`Erro ao limpar carrinho: ${errorData.erro || 'Ocorreu um erro.'}`);
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            fetchAndRenderCart(); // Recarrega o carrinho (agora vazio)

        } catch (error) {
            console.error('Erro ao limpar carrinho:', error);
        } finally {
        }
    }

    // Event Listeners para os botões principais
    if (clearCartBtn) {
        clearCartBtn.addEventListener('click', clearCart);
    }
    if (checkoutBtn) {
        checkoutBtn.addEventListener('click', () => {
            alert('Funcionalidade de Finalizar Compra será implementada aqui!');
            // window.location.href = '/checkout'; // Redirecionar para a página de checkout
        });
    }

    // Adicionar evento de submit para o formulário de cupom (lógica mocada)
    const couponForm = document.getElementById('couponForm');
    if (couponForm) {
        couponForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const couponCode = this.querySelector('input[type="text"]').value;
            if (couponCode.trim() !== '') {
                alert(`Cupom "${couponCode}" aplicado com sucesso! (Função de cupom mocada)`);
                // Aqui você faria uma chamada AJAX para validar e aplicar o cupom no backend
                // e então recarregaria o carrinho para atualizar os valores.
            } else {
                alert('Por favor, insira um código de cupom.');
            }
        });
    }

    // Carrega o carrinho quando a página é carregada
    fetchAndRenderCart();
});