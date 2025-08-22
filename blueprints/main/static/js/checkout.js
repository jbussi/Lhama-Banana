document.addEventListener('DOMContentLoaded', function() {
    // Seleção de endereço
    const addressCards = document.querySelectorAll('.address-card');
    addressCards.forEach(card => {
        card.addEventListener('click', function() {
            // Remove 'selected' de todos os cartões e adiciona ao clicado
            addressCards.forEach(c => c.classList.remove('selected'));
            this.classList.add('selected');
            
            // Habilita o botão de checkout se um endereço foi selecionado e o carrinho não está vazio
            // (A lógica de desabilitar/habilitar já é tratada pelo Jinja na renderização inicial,
            // mas podemos adicionar uma checagem aqui para garantir interações futuras)
            const checkoutBtn = document.getElementById('checkout-btn');
            if (checkoutBtn && !checkoutBtn.disabled) { // Só habilita se não estiver disabled inicialmente pelo backend
                 // Nenhuma ação extra de habilitar/desabilitar necessária aqui se já estiver habilitado
            }
        });
    });
    
    // Validação do formulário de cupom
    const couponForm = document.getElementById('coupon-form');
    if (couponForm) {
        couponForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const couponCode = this.querySelector('input').value.trim();
            if (couponCode) {
                // TODO: Lógica para aplicar o cupom via API (requisição assíncrona para o backend)
                console.log('Aplicando cupom:', couponCode);
                alert(`Cupom "${couponCode}" aplicado! (Lógica a ser implementada)`);
            }
        });
    }
    
    // Botão de adicionar endereço
    const addAddressBtn = document.getElementById('add-address-btn');
    if (addAddressBtn) {
        addAddressBtn.addEventListener('click', function() {
            // Redireciona para a página de perfil onde o usuário pode gerenciar endereços
            // Certifique-se de que a rota 'perfil_page' existe e é funcional
            window.location.href = "{{ url_for('perfil_page') }}#addresses"; 
        });
    }
    
    // Botão de finalizar compra
    const checkoutBtn = document.getElementById('checkout-btn');
    if (checkoutBtn) {
        checkoutBtn.addEventListener('click', async function() { // Tornar a função async
            // Se o botão está desabilitado pelo backend (Jinja), não faz nada
            if (this.disabled) {
                console.log("Botão de checkout desabilitado.");
                return;
            }
            
            const selectedAddressCard = document.querySelector('.address-card.selected');
            if (selectedAddressCard) {
                const addressId = selectedAddressCard.getAttribute('data-address-id');
                console.log('Endereço selecionado para checkout:', addressId);
                
                // TODO: Aqui você fará a chamada para a API Flask que integra com o PagSeguro.
                // Esta é a próxima etapa importante!
                // Por enquanto, um alerta:
                alert(`Prosseguindo para o Pagamento com o endereço ${addressId} e itens do carrinho!`);

                // Exemplo de como chamaria a API do PagSeguro (será feito no backend)
                // Isso virá na próxima etapa, quando integrarmos com a API do PagSeguro.
                /*
                showLoadingScreen(); // Supondo que você tem essa função no seu base.html
                try {
                    const response = await fetch('/api/checkout/pagseguro', { // Sua rota do backend
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            // Adicionar o token de autorização se a API for protegida (e deveria ser)
                            // 'Authorization': `Bearer ${firebase.auth().currentUser.getIdToken()}`
                        },
                        body: JSON.stringify({
                            address_id: addressId,
                            // Outros dados que o backend precise
                        })
                    });

                    if (!response.ok) {
                        const errorData = await response.json();
                        alert(`Erro: ${errorData.erro || 'Não foi possível finalizar a compra.'}`);
                        console.error('Erro ao chamar API PagSeguro:', errorData);
                    } else {
                        const data = await response.json();
                        window.location.href = data.checkout_url; // Redireciona para o PagSeguro
                    }
                } catch (error) {
                    console.error('Erro na requisição de checkout:', error);
                    alert('Erro ao tentar finalizar a compra. Tente novamente.');
                } finally {
                    hideLoadingScreen();
                }
                */
            } else {
                alert('Por favor, selecione um endereço de entrega para continuar.');
            }
        });
    }
});