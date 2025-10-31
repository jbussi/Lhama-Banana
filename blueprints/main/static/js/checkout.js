document.addEventListener('DOMContentLoaded', () => {
  console.log('checkout.js carregado');
    // --- Global Variables (for cached data) ---
    let userAddresses = [];
    let cartItems = [];
    let cartTotals = {};
    let customerDetails = {}; // Details like name, email, tax_id for PagBank
    let isManualAddressMode = false; // State variable: true if manual form is active

    // --- DOM Elements ---
    const checkoutBtn = document.getElementById('checkout-btn');
    const savedAddressesSection = document.getElementById('saved-addresses-section');
    const addressListContainer = savedAddressesSection ? savedAddressesSection.querySelector('.address-list') : null;
    const noSavedAddressesMessage = document.getElementById('no-saved-addresses-message');
    const addNewAddressBtn = document.getElementById('add-new-address-btn');
    const manualAddressFormSection = document.getElementById('manual-address-form-section');
    const manualAddressForm = document.getElementById('manual-address-form');
    const useSavedAddressesBtn = document.getElementById('use-saved-addresses-btn');

    const orderItemsContainer = document.querySelector('.order-items');
    const orderTotalsContainer = document.querySelector('.order-totals');
    const couponFormInput = document.querySelector('.coupon-input'); // If you add one

    const paymentMethodRadios = document.querySelectorAll('input[name="payment-method"]');
    const creditCardFormSection = document.getElementById('credit-card-form-section');

    // Manual Address Form Fields
    const manualRecipientName = document.getElementById('manual-recipient-name');
    const manualStreet = document.getElementById('manual-street');
    const manualNumber = document.getElementById('manual-number');
    const manualComplement = document.getElementById('manual-complement');
    const manualDistrict = document.getElementById('manual-district');
    const manualCity = document.getElementById('manual-city');
    const manualState = document.getElementById('manual-state');
    const manualPostalCode = document.getElementById('manual-postal-code');
    const manualPhone = document.getElementById('manual-phone');

    // Credit Card Form Fields
    const cardNumber = document.getElementById('card-number');
    const cardHolderName = document.getElementById('card-holder-name');
    const cardExpiry = document.getElementById('card-expiry');
    const cardCvv = document.getElementById('card-cvv');
    const cardInstallments = document.getElementById('card-installments');
    const cardHolderTaxId = document.getElementById('card-holder-tax-id');


    // --- Functions to Fetch Data from Backend API ---

    async function fetchUserAddresses() {
        try {
            console.log('[Checkout] Buscando endereços do usuário...');
            const response = await fetch('/api/user/addresses');
            
            if (!response.ok) {
                // If 401 Unauthorized, maybe user is not logged in, return empty array
                if (response.status === 401) {
                    console.warn("[Checkout] Usuário não autenticado, nenhum endereço salvo para buscar.");
                    return [];
                }
                
                const errorText = await response.text();
                console.error(`[Checkout] Erro HTTP ao buscar endereços: ${response.status} - ${errorText}`);
                throw new Error(`HTTP ${response.status}: ${errorText || 'Erro desconhecido'}`);
            }
            
            const addresses = await response.json();
            console.log(`[Checkout] ${addresses.length} endereço(s) encontrado(s)`);
            return addresses;
        } catch (error) {
            console.error("[Checkout] Erro ao buscar endereços do usuário:", {
                message: error.message,
                stack: error.stack,
                name: error.name
            });
            
            // Não mostrar alert se for apenas falta de autenticação
            if (!error.message.includes('401')) {
                console.warn("[Checkout] Não foi possível carregar endereços, usando modo manual.");
            }
            return [];
        }
    }

    async function fetchCartDetails() {
        try {
            console.log('[Checkout] Buscando detalhes do carrinho...');
            const response = await fetch('/api/cart');
            
            if (!response.ok) {
                const errorText = await response.text();
                console.error(`[Checkout] Erro HTTP ao buscar carrinho: ${response.status} - ${errorText}`);
                throw new Error(`HTTP ${response.status}: ${errorText || 'Erro desconhecido'}`);
            }
            
            const data = await response.json();
            console.log('[Checkout] Dados do carrinho recebidos:', {
                itemsCount: data.items?.length || 0,
                totals: data.totals
            });
            
            // Basic check if cart is empty but returns successfully
            if (!data.items || data.items.length === 0) {
                console.warn("[Checkout] Carrinho está vazio.");
                // Ensure totals are zeroed out if no items
                data.totals = { subtotal: 0, freight: 0, discount: 0, final_total: 0 };
            }
            
            return data;
        } catch (error) {
            console.error("[Checkout] Erro ao buscar detalhes do carrinho:", {
                message: error.message,
                stack: error.stack,
                name: error.name
            });
            
            // Retornar dados vazios ao invés de alert para não interromper o fluxo
            const emptyData = { 
                items: [], 
                totals: { subtotal: 0, freight: 0, discount: 0, final_total: 0 }, 
                customer_name: '', 
                customer_email: '', 
                customer_tax_id: '', 
                customer_phone_area: '', 
                customer_phone_number: ''
            };
            
            console.warn("[Checkout] Retornando carrinho vazio devido ao erro.");
            return emptyData;
        }
    }

    // --- Functions to Render UI Sections ---

    function renderAddresses() {
        if (!addressListContainer) return; // Ensure element exists

        addressListContainer.innerHTML = ''; // Clear existing content

        if (userAddresses.length === 0) {
            savedAddressesSection.style.display = 'none';
            manualAddressFormSection.style.display = 'block';
            if (noSavedAddressesMessage) noSavedAddressesMessage.style.display = 'block'; // Show "Nenhum endereço cadastrado"
            addNewAddressBtn.style.display = 'none'; // Hide "Add new address" button when no saved addresses
            useSavedAddressesBtn.style.display = 'none'; // Hide "Back to saved" when no saved addresses to go back to
            isManualAddressMode = true;
        } else {
            savedAddressesSection.style.display = 'block';
            manualAddressFormSection.style.display = 'none';
            if (noSavedAddressesMessage) noSavedAddressesMessage.style.display = 'none'; // Hide the message
            addNewAddressBtn.style.display = 'block'; // Show "Add new address" button
            isManualAddressMode = false; // Default to saved addresses mode

            userAddresses.forEach((address, index) => {
                const addressCard = document.createElement('div');
                addressCard.classList.add('address-card');
                if (index === 0) addressCard.classList.add('selected'); // Select the first one by default
                addressCard.dataset.addressId = address.id;

                addressCard.innerHTML = `
                    <span class="address-type">${address.nickname}</span>
                    <div class="address-details">
                        <p><strong>${address.recipient_name}</strong></p>
                        <p>${address.street}, ${address.number}${address.complement ? ', ' + address.complement : ''}</p>
                        <p>${address.district} - ${address.city}/${address.state}</p>
                        <p>CEP: ${address.postal_code}</p>
                        <p>Telefone: ${address.phone}</p>
                    </div>
                    <div class="address-actions">
                        <button class="btn-address edit-address-btn">
                            <i class="fas fa-edit"></i> Editar
                        </button>
                        ${!address.is_primary ? `<button class="btn-address text-danger remove-address-btn"><i class="fas fa-trash-alt"></i> Remover</button>` : ''}
                    </div>
                `;
                addressListContainer.appendChild(addressCard);

                // Add listener for address card selection
                addressCard.addEventListener('click', () => {
                    document.querySelectorAll('.address-card').forEach(card => card.classList.remove('selected'));
                    addressCard.classList.add('selected');
                    // TODO: Recalculate freight if it depends on the selected address (API call)
                    updateCheckoutButtonState(); // Update state if selection affects validity
                });
            });
        }
        updateCheckoutButtonState();
    }

    function renderCartItems() {
        if (!orderItemsContainer) return; // Ensure element exists

        orderItemsContainer.innerHTML = ''; // Clear existing content
        const emptyCartMsgElem = orderItemsContainer.querySelector('p.text-muted'); // Check if it exists in the original HTML structure

        if (cartItems.length === 0) {
            if (emptyCartMsgElem) emptyCartMsgElem.style.display = 'block'; // Show message
            else orderItemsContainer.innerHTML = `<p class="text-center text-muted">Seu carrinho está vazio.</p>`;
        } else {
            if (emptyCartMsgElem) emptyCartMsgElem.style.display = 'none'; // Hide message
            cartItems.forEach(item => {
                const itemDiv = document.createElement('div');
                itemDiv.classList.add('order-item');
                itemDiv.innerHTML = `
                    <img src="${item.image_url}" alt="${item.product_name}" class="order-item-img">
                    <div class="order-item-details">
                        <div class="order-item-title">${item.product_name}</div>
                        <div class="order-item-variation">${item.estampa_name} / ${item.tamanho_name}</div>
                        <div class="order-item-price">R$ ${item.price_at_time_of_add.toFixed(2).replace('.', ',')}</div>
                        <div class="order-item-quantity">Quantidade: ${item.quantity}</div>
                    </div>
                `;
                orderItemsContainer.appendChild(itemDiv);
            });
        }
        updateCheckoutButtonState();
    }

    function renderOrderSummary() {
        if (!orderTotalsContainer) return; // Ensure element exists

        orderTotalsContainer.innerHTML = `
            <div class="total-row">
                <span>Subtotal</span>
                <span>R$ ${cartTotals.subtotal.toFixed(2).replace('.', ',')}</span>
            </div>
            <div class="total-row">
                <span>Frete</span>
                <span id="freight-display">R$ ${cartTotals.freight.toFixed(2).replace('.', ',')}</span>
            </div>
            ${cartTotals.discount > 0 ? `
            <div class="total-row">
                <span>Desconto</span>
                <span class="text-danger">- R$ ${cartTotals.discount.toFixed(2).replace('.', ',')}</span>
            </div>` : ''}
            <div class="total-row">
                <strong>Total</strong>
                <strong class="total-amount">R$ ${cartTotals.final_total.toFixed(2).replace('.', ',')}</strong>
            </div>
        `;
        
        if (couponFormInput && cartTotals.coupon_code) {
            couponFormInput.value = cartTotals.coupon_code;
        }

        updateCheckoutButtonState();
    }

    // --- Auxiliary UI/State Management Functions ---

    function toggleCreditCardForm() {
        if (!creditCardFormSection) return;
        const selectedMethod = document.querySelector('input[name="payment-method"]:checked').value;
        if (selectedMethod === 'credit-card') {
            creditCardFormSection.style.display = 'block';
            // Enable required attributes for card fields when visible
            if (cardNumber) cardNumber.required = true;
            if (cardHolderName) cardHolderName.required = true;
            if (cardExpiry) cardExpiry.required = true;
            if (cardCvv) cardCvv.required = true;
            if (cardHolderTaxId) cardHolderTaxId.required = true;
        } else {
            creditCardFormSection.style.display = 'none';
            // Disable required attributes for card fields when hidden
            if (cardNumber) cardNumber.required = false;
            if (cardHolderName) cardHolderName.required = false;
            if (cardExpiry) cardExpiry.required = false;
            if (cardCvv) cardCvv.required = false;
            if (cardHolderTaxId) cardHolderTaxId.required = false;
        }
        updateCheckoutButtonState(); // Update button state based on form validity
    }

    function updateCheckoutButtonState() {
        let disableButton = false;
        let buttonText = '<i class="fas fa-lock"></i> Finalizar Compra';

        if (cartItems.length === 0) {
            disableButton = true;
            buttonText = 'Carrinho vazio';
        } else if (isManualAddressMode) {
            // If in manual mode, validate manual form
            if (!manualAddressForm || !manualAddressForm.checkValidity()) {
                disableButton = true;
                buttonText = 'Preencha o endereço para continuar';
            }
        } else { // Saved address mode
            const selectedAddress = document.querySelector('.address-card.selected');
            if (!selectedAddress) {
                disableButton = true;
                buttonText = 'Selecione um endereço para continuar';
            }
        }
        
        // Also check if credit card form is visible and valid
        if (document.querySelector('input[name="payment-method"]:checked').value === 'credit-card') {
            if (!creditCardFormSection || !creditCardFormSection.querySelector('form').checkValidity()) {
                disableButton = true;
                if (!manualAddressForm.checkValidity() && !isManualAddressMode) { // Prioritize address if it's missing first
                    // Leave address message if it's the main issue
                } else {
                    buttonText = 'Preencha os dados do cartão';
                }
            }
        }

        if (checkoutBtn) {
            checkoutBtn.disabled = disableButton;
            checkoutBtn.innerHTML = buttonText;
        }
    }

    // --- Main Data Loading Function ---
    async function loadCheckoutData() {
        if (!checkoutBtn) return; // Exit if button not found

        // Show a loading indicator
        checkoutBtn.disabled = true;
        checkoutBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Carregando...';

        try {
            // Fetch all necessary data concurrently
            const [addressesData, cartDetailsData] = await Promise.all([
                fetchUserAddresses(),
                fetchCartDetails()
            ]);

            userAddresses = addressesData;
            cartItems = cartDetailsData.items;
            cartTotals = cartDetailsData.totals;
            
            // Populate customerDetails from cartData
            if (cartDetailsData.customer) {
                customerDetails.name = cartDetailsData.customer.name || ''; 
                customerDetails.email = cartDetailsData.customer.email || '';
                customerDetails.tax_id = cartDetailsData.customer.tax_id || '';
                customerDetails.phone_area = cartDetailsData.customer.phone ? cartDetailsData.customer.phone.substring(0, 2) : '';
                customerDetails.phone_number = cartDetailsData.customer.phone ? cartDetailsData.customer.phone.substring(2) : '';
            }

            // Render the UI sections
            renderAddresses();
            renderCartItems();
            renderOrderSummary();

            // Update button state (will enable if everything is valid)
            updateCheckoutButtonState();

            // Re-initialize credit card form display after all elements are rendered
            toggleCreditCardForm();
            
        } catch (error) {
            console.error('Erro ao carregar dados do checkout:', error);
            alert('Erro ao carregar dados do checkout. Tente novamente.');
        }
    }


    // --- Event Listeners and Initial Setup ---
    // Make sure all DOM elements exist before adding listeners
    if (checkoutBtn && orderItemsContainer && orderTotalsContainer && paymentMethodRadios.length) {
        
        // Initial data load on page ready
        loadCheckoutData();

        // Event listener for payment method radios
        paymentMethodRadios.forEach(radio => {
            radio.addEventListener('change', toggleCreditCardForm);
        });

        // Event listeners for address management (only if elements exist)
        if (addNewAddressBtn && manualAddressFormSection && savedAddressesSection) {
            addNewAddressBtn.addEventListener('click', () => {
                savedAddressesSection.style.display = 'none';
                manualAddressFormSection.style.display = 'block';
                if (useSavedAddressesBtn) useSavedAddressesBtn.style.display = 'block';
                isManualAddressMode = true;
                updateCheckoutButtonState();
            });
        }

        if (useSavedAddressesBtn) {
            useSavedAddressesBtn.addEventListener('click', () => {
                if (savedAddressesSection) savedAddressesSection.style.display = 'block';
                if (manualAddressFormSection) manualAddressFormSection.style.display = 'none';
                if (noSavedAddressesMessage) noSavedAddressesMessage.style.display = 'none';
                useSavedAddressesBtn.style.display = 'none';
                isManualAddressMode = false;
                updateCheckoutButtonState();
            });
        }

        // Live validation for manual address form
        if (manualAddressForm) {
            manualAddressForm.addEventListener('input', updateCheckoutButtonState);
        }
        // Live validation for credit card form
        if (creditCardFormSection) {
            creditCardFormSection.querySelector('form').addEventListener('input', updateCheckoutButtonState);
        }

        // Checkout Button Click Listener
        checkoutBtn.addEventListener('click', async () => {
            try {
                if (checkoutBtn.disabled) return; // Prevent double clicks or clicks when disabled

                console.log('[Checkout] Iniciando processo de checkout...');

                // Disable button and show loading state
                checkoutBtn.disabled = true;
                checkoutBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Processando...';

                // 1. Get shipping information (from saved or manual form)
                let shippingInfo = null;
                if (isManualAddressMode) {
                    // Validate manual form fields before proceeding
                    if (!manualAddressForm || !manualAddressForm.checkValidity()) {
                        console.error("[Checkout] Formulário de endereço manual não válido.");
                        alert('Por favor, preencha todos os campos obrigatórios do endereço manual.');
                        if (manualAddressForm) manualAddressForm.reportValidity();
                        checkoutBtn.disabled = false;
                        updateCheckoutButtonState();
                        return;
                    }
                    
                    // Validação de elementos do formulário manual
                    if (!manualRecipientName || !manualStreet || !manualNumber || !manualDistrict || !manualCity || !manualState || !manualPostalCode || !manualPhone) {
                        console.error("[Checkout] Elementos do formulário manual não encontrados.");
                        alert('Erro ao processar formulário. Recarregue a página e tente novamente.');
                        checkoutBtn.disabled = false;
                        updateCheckoutButtonState();
                        return;
                    }
                    
                    shippingInfo = {
                        recipient_name: manualRecipientName.value,
                        street: manualStreet.value,
                        number: manualNumber.value,
                        complement: manualComplement ? manualComplement.value : '',
                        district: manualDistrict.value,
                        city: manualCity.value,
                        state: manualState.value,
                        postal_code: manualPostalCode.value,
                        phone: manualPhone.value
                    };
                    console.log('[Checkout] Endereço manual coletado com sucesso.');
                } else {
                    // Saved address mode
                    const selectedAddressCard = document.querySelector('.address-card.selected');
                    if (!selectedAddressCard) {
                        console.error("[Checkout] Nenhum endereço selecionado.");
                        alert('Por favor, selecione um endereço de entrega ou adicione um novo.');
                        checkoutBtn.disabled = false;
                        updateCheckoutButtonState();
                        return;
                    }
                    
                    const addressId = selectedAddressCard.dataset.addressId;
                    // Find the full address details from our cached userAddresses
                    shippingInfo = userAddresses.find(addr => String(addr.id) === String(addressId));

                    if (!shippingInfo) {
                        console.error("[Checkout] Endereço selecionado não encontrado na lista de endereços.", {
                            addressId: addressId,
                            availableAddresses: userAddresses.map(a => a.id)
                        });
                        alert('Detalhes do endereço selecionado não encontrados na lista. Tente novamente.');
                        checkoutBtn.disabled = false;
                        updateCheckoutButtonState();
                        return;
                    }
                    console.log('[Checkout] Endereço salvo selecionado com sucesso:', addressId);
                }
                
                // 2. Get selected payment method
                const paymentMethodRadio = document.querySelector('input[name="payment-method"]:checked');
                if (!paymentMethodRadio) {
                    console.error("[Checkout] Nenhum método de pagamento selecionado.");
                    alert('Por favor, selecione um método de pagamento.');
                    checkoutBtn.disabled = false;
                    updateCheckoutButtonState();
                    return;
                }
                const selectedPaymentMethod = paymentMethodRadio.value;
                // Normalizar método de pagamento para formato do backend (CREDIT_CARD, PIX, BOLETO)
                let paymentMethodForBackend = selectedPaymentMethod.toUpperCase();
                if (paymentMethodForBackend === 'CREDIT-CARD') {
                    paymentMethodForBackend = 'CREDIT_CARD';
                }
                console.log('[Checkout] Método de pagamento selecionado:', selectedPaymentMethod, '->', paymentMethodForBackend);

                // 3. Coletar informações do cliente (de customerDetails ou shippingInfo)
                const customerName = customerDetails.name || shippingInfo.recipient_name || shippingInfo.nome_recebedor || '';
                const customerEmail = customerDetails.email || (shippingInfo.email || '');
                const customerTaxId = customerDetails.tax_id || (shippingInfo.cpf || '');
                
                // Extrair telefone do shippingInfo se não vier em customerDetails
                let phoneArea = customerDetails.phone_area || '';
                let phoneNumber = customerDetails.phone_number || '';
                
                if (!phoneArea || !phoneNumber) {
                    const phone = shippingInfo.phone || shippingInfo.telefone || '';
                    if (phone) {
                        // Formato esperado: (XX) XXXXX-XXXX ou XXXXXXXXXXX
                        const cleanPhone = phone.replace(/\D/g, '');
                        if (cleanPhone.length >= 10) {
                            phoneArea = cleanPhone.substring(0, 2);
                            phoneNumber = cleanPhone.substring(2);
                        }
                    }
                }
                
                // 3. Collect payment details based on method
                let paymentDetails = {
                    payment_method_type: selectedPaymentMethod,
                    customer_name: customerName,
                    customer_email: customerEmail || 'guest@example.com',
                    customer_cpf_cnpj: customerTaxId,
                    customer_tax_id: customerTaxId,
                    phone_area: phoneArea || '11',
                    phone_number: phoneNumber || '999999999',
                    customer_phone_area: phoneArea || '11',
                    customer_phone_number: phoneNumber || '999999999'
                };

                if (selectedPaymentMethod === 'credit-card') {
                    // Garantir que o formulário de cartão está visível
                    if (!creditCardFormSection) {
                        console.error("[Checkout] Seção de cartão de crédito não encontrada.");
                        alert('Erro ao processar formulário de cartão. Recarregue a página.');
                        checkoutBtn.disabled = false;
                        updateCheckoutButtonState();
                        return;
                    }
                    
                    // Mostrar formulário de cartão se estiver oculto
                    if (creditCardFormSection.style.display === 'none') {
                        creditCardFormSection.style.display = 'block';
                        // Tornar campos obrigatórios
                        if (cardNumber) cardNumber.required = true;
                        if (cardHolderName) cardHolderName.required = true;
                        if (cardExpiry) cardExpiry.required = true;
                        if (cardCvv) cardCvv.required = true;
                        if (cardHolderTaxId) cardHolderTaxId.required = true;
                        if (cardInstallments) cardInstallments.required = true;
                    }
                    
                    // Validação de elementos do formulário de cartão
                    if (!cardNumber || !cardHolderName || !cardExpiry || !cardCvv || !cardInstallments || !cardHolderTaxId) {
                        console.error("[Checkout] Elementos do formulário de cartão não encontrados.");
                        alert('Erro ao processar dados do cartão. Recarregue a página.');
                        checkoutBtn.disabled = false;
                        updateCheckoutButtonState();
                        return;
                    }
                    
                    // Validar se os campos estão preenchidos
                    if (!cardNumber.value || !cardNumber.value.replace(/\s/g, '').match(/^\d{13,19}$/)) {
                        alert('Por favor, informe um número de cartão válido (13 a 19 dígitos).');
                        cardNumber.focus();
                        checkoutBtn.disabled = false;
                        updateCheckoutButtonState();
                        return;
                    }
                    
                    if (!cardHolderName.value || cardHolderName.value.trim().length < 3) {
                        alert('Por favor, informe o nome completo do titular do cartão.');
                        cardHolderName.focus();
                        checkoutBtn.disabled = false;
                        updateCheckoutButtonState();
                        return;
                    }
                    
                    if (!cardExpiry.value || !cardExpiry.value.match(/^\d{2}\/\d{2}$/)) {
                        alert('Por favor, informe a data de validade no formato MM/AA.');
                        cardExpiry.focus();
                        checkoutBtn.disabled = false;
                        updateCheckoutButtonState();
                        return;
                    }
                    
                    if (!cardCvv.value || !cardCvv.value.match(/^\d{3,4}$/)) {
                        alert('Por favor, informe o CVV do cartão (3 ou 4 dígitos).');
                        cardCvv.focus();
                        checkoutBtn.disabled = false;
                        updateCheckoutButtonState();
                        return;
                    }
                    
                    if (!cardHolderTaxId.value || cardHolderTaxId.value.replace(/\D/g, '').length < 11) {
                        alert('Por favor, informe o CPF do titular do cartão.');
                        cardHolderTaxId.focus();
                        checkoutBtn.disabled = false;
                        updateCheckoutButtonState();
                        return;
                    }
                    
                    if (!cardInstallments.value || parseInt(cardInstallments.value) < 1) {
                        alert('Por favor, selecione o número de parcelas.');
                        cardInstallments.focus();
                        checkoutBtn.disabled = false;
                        updateCheckoutButtonState();
                        return;
                    }
                    
                    // Validar data de validade não está expirada
                    const expValue = cardExpiry.value.split('/');
                    const expMonth = parseInt(expValue[0]);
                    const expYear = 2000 + parseInt(expValue[1]);
                    const now = new Date();
                    const expDate = new Date(expYear, expMonth - 1);
                    if (expDate < now) {
                        alert('O cartão está expirado. Por favor, informe uma data de validade válida.');
                        cardExpiry.focus();
                        checkoutBtn.disabled = false;
                        updateCheckoutButtonState();
                        return;
                    }

                    // PAGBANK TOKENIZATION - Integração com SDK do PagBank
                    try {
                        console.log('[Checkout] Iniciando tokenização do cartão via PagBank...');
                        
                        // Formatar dados do cartão para tokenização
                        const cardNumberValue = cardNumber.value.replace(/\s/g, '');
                        const cardExpValue = cardExpiry.value.split('/');
                        const cardExpMonth = cardExpValue[0]?.trim() || '';
                        const cardExpYear = '20' + (cardExpValue[1]?.trim() || '');
                        
                        // Opção 1: Usar SDK do PagBank (recomendado para produção)
                        // Verifique se o SDK está carregado
                        if (typeof PagBank !== 'undefined' && PagBank.tokenization) {
                            console.log('[Checkout] Usando PagBank SDK para tokenização...');
                            
                            const cardToken = await PagBank.tokenization.create({
                                number: cardNumberValue,
                                exp_month: cardExpMonth,
                                exp_year: cardExpYear,
                                security_code: cardCvv.value,
                                holder: {
                                    name: cardHolderName.value,
                                    tax_id: cardHolderTaxId.value.replace(/\D/g, '')
                                }
                            });
                            
                            paymentDetails.card_token = cardToken.id;
                            paymentDetails.security_code = cardCvv.value;
                            console.log('[Checkout] Cartão tokenizado com sucesso via SDK.');
                            
                        } else {
                            // Opção 2: Tokenização via API backend (fallback ou sandbox)
                            console.log('[Checkout] SDK não disponível, usando tokenização via API backend...');
                            
                            const tokenizationResponse = await fetch('/api/pagbank/tokenize-card', {
                                method: 'POST',
                                headers: {
                                    'Content-Type': 'application/json'
                                },
                                body: JSON.stringify({
                                    card_number: cardNumberValue,
                                    exp_month: cardExpMonth,
                                    exp_year: cardExpYear,
                                    security_code: cardCvv.value,
                                    holder_name: cardHolderName.value,
                                    holder_tax_id: cardHolderTaxId.value.replace(/\D/g, '')
                                })
                            });
                            
                            if (!tokenizationResponse.ok) {
                                const errorData = await tokenizationResponse.json();
                                throw new Error(errorData.erro || 'Erro ao tokenizar cartão');
                            }
                            
                            const tokenData = await tokenizationResponse.json();
                            paymentDetails.card_token = tokenData.card_token || tokenData.id;
                            paymentDetails.security_code = cardCvv.value;
                            console.log('[Checkout] Cartão tokenizado com sucesso via API.');
                        }
                        
                        paymentDetails.installments = parseInt(cardInstallments.value);
                        paymentDetails.card_holder_name = cardHolderName.value;
                        paymentDetails.card_holder_cpf_cnpj = cardHolderTaxId.value.replace(/\D/g, '');
                        
                        // Mantém dados originais para fallback se necessário
                        paymentDetails.card_number = cardNumberValue;
                        paymentDetails.card_exp_month = cardExpMonth;
                        paymentDetails.card_exp_year = cardExpYear;
                        paymentDetails.card_cvv = cardCvv.value;

                    } catch (error) {
                        console.error("[Checkout] Erro na tokenização do cartão:", {
                            message: error.message,
                            stack: error.stack
                        });
                        alert("Erro ao tokenizar o cartão: " + error.message + "\n\nVerifique os dados e tente novamente.");
                        checkoutBtn.disabled = false;
                        updateCheckoutButtonState();
                        return;
                    }
                } else if (selectedPaymentMethod === 'pix' || selectedPaymentMethod === 'boleto') {
                    // Para PIX e Boleto, apenas validar dados do cliente
                    if (!customerName || customerName.trim().length < 3) {
                        alert('Por favor, informe o nome completo para continuar.');
                        checkoutBtn.disabled = false;
                        updateCheckoutButtonState();
                        return;
                    }
                    
                    if (!customerEmail || !customerEmail.includes('@')) {
                        alert('Por favor, informe um email válido para continuar.');
                        checkoutBtn.disabled = false;
                        updateCheckoutButtonState();
                        return;
                    }
                    
                    if (!customerTaxId || customerTaxId.replace(/\D/g, '').length < 11) {
                        alert('Por favor, informe o CPF para continuar.');
                        checkoutBtn.disabled = false;
                        updateCheckoutButtonState();
                        return;
                    }
                    
                    console.log('[Checkout] Dados do cliente validados para', selectedPaymentMethod);
                } else {
                    // Método de pagamento não reconhecido
                    alert('Método de pagamento não reconhecido. Por favor, selecione PIX, Boleto ou Cartão de Crédito.');
                    checkoutBtn.disabled = false;
                    updateCheckoutButtonState();
                    return;
                }

                // 4. Preparar shipping_info no formato correto para o backend
                const shippingInfoFormatted = {
                    nome_recebedor: shippingInfo.recipient_name || shippingInfo.nome_recebedor || customerName,
                    rua: shippingInfo.street || shippingInfo.rua || shippingInfo.logradouro || '',
                    numero: shippingInfo.number || shippingInfo.numero || '',
                    complemento: shippingInfo.complement || shippingInfo.complemento || '',
                    bairro: shippingInfo.district || shippingInfo.bairro || shippingInfo.bairro || '',
                    cidade: shippingInfo.city || shippingInfo.cidade || shippingInfo.localidade || '',
                    estado: shippingInfo.state || shippingInfo.estado || shippingInfo.uf || '',
                    cep: (shippingInfo.postal_code || shippingInfo.cep || '').replace(/\D/g, ''),
                    telefone: shippingInfo.phone || shippingInfo.telefone || `${phoneArea}${phoneNumber}` || '',
                    email: customerEmail || ''
                };
                
                // 5. Preparar shipping_option
                const selectedShippingOption = cartTotals.selectedShippingOption || {
                    name: 'Frete Padrão',
                    price: cartTotals.freight || 0,
                    deadline: '10-15 dias úteis'
                };
                
                // 6. Prepare the final payload for the Flask backend
                const payload = {
                    cart_items: cartItems.map(item => ({ // Format cart items for backend
                        product_id: item.product_id,
                        quantity: item.quantity,
                        preco_unitario: item.price_at_time_of_add,
                        nome_produto_snapshot: item.product_name,
                        sku_produto_snapshot: item.sku || 'N/A',
                        detalhes_produto_snapshot: {
                            estampa_name: item.estampa_name,
                            tamanho_name: item.tamanho_name,
                            image_url: item.image_url
                        }
                    })),
                    shipping_info: shippingInfoFormatted,
                    shipping_option: selectedShippingOption,
                    payment_method: paymentMethodForBackend, // Método no formato do backend
                    payment_details: paymentDetails,
                    total_value: cartTotals.final_total,
                    freight_value: cartTotals.freight || 0,
                    discount_value: cartTotals.discount || 0
                };

                // 5. Send to the Flask Backend
                console.log('[Checkout] Enviando pedido para o backend...', {
                    cartItemsCount: cartItems.length,
                    totalValue: cartTotals.final_total,
                    paymentMethod: selectedPaymentMethod
                });

                try {
                    console.log('[Checkout] Enviando payload completo:', JSON.stringify(payload, null, 2));
                    
                    const response = await fetch('/api/checkout/process', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify(payload)
                    });

                    console.log('[Checkout] Resposta recebida - Status:', response.status, response.statusText);

                    let data;
                    let responseText = '';
                    try {
                        responseText = await response.text();
                        console.log('[Checkout] Response text (primeiros 1000 chars):', responseText.substring(0, 1000));
                        
                        if (!responseText || responseText.trim() === '') {
                            console.error("[Checkout] Resposta vazia do servidor!");
                            throw new Error('Resposta vazia do servidor - verifique os logs do servidor');
                        }
                        
                        data = JSON.parse(responseText);
                        console.log('[Checkout] Response JSON parseado:', JSON.stringify(data, null, 2));
                        
                        // Validar se a resposta contém dados essenciais
                        if (!data.codigo_pedido && !data.erro) {
                            console.warn('[Checkout] Resposta não contém codigo_pedido nem erro:', data);
                        }
                        
                    } catch (jsonError) {
                        console.error("[Checkout] Erro ao parsear resposta JSON:", jsonError);
                        console.error("[Checkout] Texto da resposta completa:", responseText);
                        
                        // Tentar extrair erro da resposta
                        let errorMsg = 'Erro desconhecido';
                        try {
                            const errorData = JSON.parse(responseText);
                            errorMsg = errorData.erro || errorData.error || errorData.detalhes || errorMsg;
                            if (errorData.traceback) {
                                console.error("[Checkout] Traceback do servidor:", errorData.traceback);
                            }
                        } catch {
                            errorMsg = responseText || `Status ${response.status}: ${response.statusText}`;
                        }
                        
                        alert(`Erro ao processar checkout:\n\n${errorMsg}\n\nVerifique o console para mais detalhes.`);
                        checkoutBtn.disabled = false;
                        updateCheckoutButtonState();
                        return;
                    }

                    if (response.ok) { // HTTP status 2xx
                        console.log("[Checkout] Checkout processado com sucesso:", {
                            codigoPedido: data.codigo_pedido,
                            paymentMethod: data.payment_method_type,
                            fullResponse: data
                        });
                        
                        // Preparar URL de redirecionamento com dados do pagamento
                        let redirectUrl = `/order-status/${data.codigo_pedido}`;
                        const params = new URLSearchParams();
                        
                        if (data.payment_method_type === 'pix') {
                            if (data.pix_qr_code_link) {
                                params.append('pix_qr', data.pix_qr_code_link);
                            }
                            if (data.pix_qr_code_text) {
                                params.append('pix_text', data.pix_qr_code_text);
                            }
                            if (params.toString()) {
                                redirectUrl += '?' + params.toString();
                            }
                            alert("Pedido criado! Código: " + data.codigo_pedido + "\n\nEscaneie o QR Code do PIX para pagar.");
                        } else if (data.payment_method_type === 'boleto') {
                            if (data.boleto_link) {
                                params.append('boleto_link', data.boleto_link);
                            }
                            if (data.boleto_barcode) {
                                params.append('boleto_barcode', data.boleto_barcode);
                            }
                            if (params.toString()) {
                                redirectUrl += '?' + params.toString();
                            }
                            alert("Pedido criado! Código: " + data.codigo_pedido + "\n\nBaixe o boleto para pagar.");
                        } else if (data.payment_method_type === 'credit_card') {
                            // Cartão: mostrar status do pagamento
                            if (data.payment_approved) {
                                alert("Compra realizada com sucesso! Código do pedido: " + data.codigo_pedido + "\n\nPagamento aprovado!");
                            } else {
                                alert("Pedido criado com sucesso! Código: " + data.codigo_pedido + "\n\nPagamento pendente de confirmação.");
                            }
                        } else {
                            alert("Pedido criado com sucesso! Código: " + data.codigo_pedido);
                        }
                        
                        // Redirecionar
                        window.location.href = redirectUrl;

                    } else { // HTTP status 4xx or 5xx
                        console.error("[Checkout] Erro no processamento do checkout:", {
                            status: response.status,
                            statusText: response.statusText,
                            error: data.error || data.message || 'Erro desconhecido',
                            fullResponse: data
                        });
                        
                        const errorMessage = data.message || data.error || data.erro || "Erro desconhecido ao processar o checkout.";
                        alert(`Erro ao finalizar a compra: ${errorMessage}`);
                        checkoutBtn.disabled = false;
                        updateCheckoutButtonState(); // Restore button state
                    }
                } catch (error) {
                    console.error("[Checkout] Erro ao comunicar com o backend:", {
                        message: error.message,
                        stack: error.stack,
                        name: error.name,
                        cause: error.cause
                    });
                    
                    alert(`Não foi possível conectar com o servidor: ${error.message}. Verifique sua conexão e tente novamente.`);
                    checkoutBtn.disabled = false;
                    updateCheckoutButtonState(); // Restore button state
                }
            } catch (error) {
                // Catch geral para erros não previstos no fluxo
                console.error("[Checkout] Erro inesperado no processo de checkout:", {
                    message: error.message,
                    stack: error.stack,
                    name: error.name,
                    cause: error.cause
                });
                
                alert(`Erro inesperado ao processar checkout: ${error.message}. Tente recarregar a página.`);
                if (checkoutBtn) {
                    checkoutBtn.disabled = false;
                    updateCheckoutButtonState();
                }
            }
        });

    } else {
        console.error("Não foi possível encontrar todos os elementos DOM necessários. Verifique seu checkout.html.");
        if (checkoutBtn) {
            checkoutBtn.disabled = true;
            checkoutBtn.innerHTML = "Erro ao carregar página.";
        }
    }

    // --- Helper Functions ---
    async function getAuthHeaders() {
        const headers = {
            'Content-Type': 'application/json'
        };
        
        // Se o usuário estiver logado, adicionar token de autenticação
        const uid = sessionStorage.getItem('uid');
        if (uid) {
            headers['Authorization'] = `Bearer ${uid}`;
        }
        
        return headers;
    }

    async function calculateShipping(cep) {
        try {
            const response = await fetch('/api/shipping/calculate', {
                method: 'POST',
                headers: await getAuthHeaders(),
                body: JSON.stringify({ cep: cep })
            });
            
            if (response.ok) {
                const data = await response.json();
                return data.shipping_options || [];
            } else {
                const errorData = await response.json();
                throw new Error(errorData.erro || 'Erro ao calcular frete');
            }
        } catch (error) {
            console.error('[Checkout] Erro ao calcular frete:', error);
            return [];
        }
    }

    // --- ViaCEP Integration for Address Auto-fill ---
    /**
     * Busca endereço na ViaCEP API
     * @param {string} cep - CEP no formato 00000000 ou 00000-000
     * @returns {Promise<Object|null>} - Objeto com dados do endereço ou null se erro
     */
    async function fetchAddressByCEP(cep) {
        try {
            // Remove caracteres não numéricos do CEP
            const cleanCEP = cep.replace(/\D/g, '');
            
            // Validação básica do CEP
            if (cleanCEP.length !== 8) {
                console.warn('[Checkout] CEP inválido:', cep);
                return null;
            }
            
            console.log('[Checkout] Buscando endereço na ViaCEP para CEP:', cleanCEP);
            
            const response = await fetch(`https://viacep.com.br/ws/${cleanCEP}/json/`);
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            
            // ViaCEP retorna {erro: true} quando o CEP não é encontrado
            if (data.erro) {
                console.warn('[Checkout] CEP não encontrado na ViaCEP:', cleanCEP);
                return null;
            }
            
            console.log('[Checkout] Endereço encontrado na ViaCEP:', data);
            
            return {
                street: data.logradouro || '',
                district: data.bairro || '',
                city: data.localidade || '',
                state: data.uf || '',
                postal_code: data.cep || cleanCEP
            };
            
        } catch (error) {
            console.error('[Checkout] Erro ao buscar CEP na ViaCEP:', {
                message: error.message,
                stack: error.stack,
                cep: cep
            });
            return null;
        }
    }

    /**
     * Preenche automaticamente os campos de endereço baseado no CEP
     * @param {string} cep - CEP digitado
     * @param {HTMLElement} cepInput - Elemento input do CEP
     */
    async function fillAddressByCEP(cep, cepInput) {
        if (!cep || cep.replace(/\D/g, '').length !== 8) {
            return; // CEP incompleto
        }
        
        // Mostra indicador de carregamento
        const originalPlaceholder = cepInput.placeholder;
        cepInput.placeholder = 'Buscando endereço...';
        cepInput.disabled = true;
        
        try {
            const addressData = await fetchAddressByCEP(cep);
            
            if (addressData && manualAddressFormSection.style.display !== 'none') {
                // Preenche apenas se o formulário manual estiver visível
                if (manualStreet) manualStreet.value = addressData.street;
                if (manualDistrict) manualDistrict.value = addressData.district;
                if (manualCity) manualCity.value = addressData.city;
                if (manualState) manualState.value = addressData.state;
                
                // Formata o CEP de volta
                if (manualPostalCode) {
                    const formattedCEP = addressData.postal_code.replace(/^(\d{5})(\d{3})$/, '$1-$2');
                    manualPostalCode.value = formattedCEP;
                }
                
                console.log('[Checkout] Campos de endereço preenchidos automaticamente.');
                updateCheckoutButtonState(); // Atualiza estado do botão
                
                // Foca no campo de número após preencher
                if (manualNumber) {
                    setTimeout(() => manualNumber.focus(), 100);
                }
            }
        } catch (error) {
            console.error('[Checkout] Erro ao preencher endereço:', error);
        } finally {
            // Restaura estado do campo CEP
            cepInput.disabled = false;
            cepInput.placeholder = originalPlaceholder;
        }
    }

    // Event listener para preenchimento automático de CEP
    if (manualPostalCode) {
        let cepTimeout;
        
        // Formatação automática do CEP enquanto digita (00000-000)
        manualPostalCode.addEventListener('input', function(e) {
            let value = e.target.value.replace(/\D/g, '');
            
            if (value.length > 5) {
                value = value.substring(0, 5) + '-' + value.substring(5, 8);
            }
            
            e.target.value = value;
            
            // Limpa timeout anterior
            clearTimeout(cepTimeout);
            
            // Aguarda 800ms após parar de digitar para buscar o CEP
            if (value.replace(/\D/g, '').length === 8) {
                cepTimeout = setTimeout(() => {
                    fillAddressByCEP(value, e.target);
                }, 800);
            }
        });
        
        // Busca CEP quando o campo perde o foco e tem 8 dígitos
        manualPostalCode.addEventListener('blur', function(e) {
            const cep = e.target.value.replace(/\D/g, '');
            if (cep.length === 8) {
                fillAddressByCEP(cep, e.target);
            }
        });
    }
});