document.addEventListener('DOMContentLoaded', function() {
	console.log('[Checkout] Script de checkout carregado');
    
	// --- Elementos do resumo do pedido ---
	const cartItemsContainer = document.getElementById('cartItems');
	const subtotalElem = document.getElementById('subtotal');
	const freightElem = document.getElementById('freight');
	const totalElem = document.getElementById('total');
    
	// --- Elementos do formulário de endereço ---
	const cepInput = document.getElementById('cep');
	const buscarCepBtn = document.getElementById('buscarCep');
	const ruaInput = document.getElementById('rua');
	const bairroInput = document.getElementById('bairro');
	const cidadeInput = document.getElementById('cidade');
	const estadoSelect = document.getElementById('estado');
	const numeroInput = document.getElementById('numero');
	const complementoInput = document.getElementById('complemento');
	const nomeRecebedorInput = document.getElementById('nome_recebedor');
	
	// --- Elementos de pagamento ---
	const paymentMethodRadios = document.querySelectorAll('input[name="payment_method"]');
	const creditCardForm = document.getElementById('creditCardForm');
	const checkoutForm = document.getElementById('checkoutForm');
	const checkoutLoading = document.getElementById('checkoutLoading');
	const finalizarCompraBtn = document.getElementById('finalizarCompra');
    
	// --- Variáveis globais para dados do carrinho ---
	let cartData = {
		items: [],
		total_value: 0,
		freight: 0
	};
	
	let selectedShippingOption = null;
	let savedAddresses = [];
	let selectedSavedAddressId = null;
    
	/**
	 * Formata valor monetário em R$
	 */
	function formatCurrency(value) {
		return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(value);
	}
	
	/**
	 * Carrega endereços salvos do usuário (se logado)
	 */
	async function loadSavedAddresses() {
		try {
			// Verificar se Firebase está disponível via import dinâmico
			let firebaseAuth = null;
			let onAuthStateChangedFn = null;
			try {
				const { initializeApp } = await import('https://www.gstatic.com/firebasejs/10.12.2/firebase-app.js');
				const { getAuth, onAuthStateChanged } = await import('https://www.gstatic.com/firebasejs/10.12.2/firebase-auth.js');
				
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
				firebaseAuth = getAuth(app);
				onAuthStateChangedFn = onAuthStateChanged;
			} catch (error) {
				console.log('[Checkout] Firebase não disponível:', error);
				return;
			}
			
			if (!firebaseAuth || !onAuthStateChangedFn) return;
			
			// Aguardar o estado de autenticação
			return new Promise((resolve) => {
				onAuthStateChangedFn(firebaseAuth, async (user) => {
					if (!user) {
						console.log('[Checkout] Usuário não logado');
						resolve();
						return;
					}
					
					try {
						const idToken = await user.getIdToken();
						const response = await fetch('/api/addresses', {
							method: 'GET',
							headers: {
								'Authorization': `Bearer ${idToken}`
							}
						});
						
						if (response.ok) {
							const result = await response.json();
							if (result.addresses && Array.isArray(result.addresses) && result.addresses.length > 0) {
								savedAddresses = result.addresses;
								renderSavedAddresses();
							}
						}
					} catch (error) {
						console.error('[Checkout] Erro ao carregar endereços salvos:', error);
					}
					resolve();
				});
			});
		} catch (error) {
			console.error('[Checkout] Erro ao carregar endereços salvos:', error);
		}
	}
	
	/**
	 * Renderiza a lista de endereços salvos
	 */
	function renderSavedAddresses() {
		const section = document.getElementById('saved-addresses-section');
		const list = document.getElementById('saved-addresses-list');
		const addressForm = document.getElementById('address-form');
		
		if (!section || !list) return;
		
		if (savedAddresses.length === 0) {
			section.style.display = 'none';
			if (addressForm) addressForm.style.display = 'flex';
			return;
		}
		
		section.style.display = 'block';
		
		let html = '<div style="display: flex; flex-direction: column; gap: 1rem;">';
		savedAddresses.forEach(address => {
			const typeText = { 'home': 'Casa', 'work': 'Trabalho', 'other': 'Outro' }[address.type] || 'Endereço';
			const formattedCep = address.zipcode ? address.zipcode.replace(/^(\d{5})(\d{3})$/, '$1-$2') : '';
			
			html += `
				<label style="display: flex; align-items: flex-start; padding: 1rem; border: 2px solid #e9ecef; border-radius: 8px; cursor: pointer; transition: all 0.3s; background: #fff;" 
				       onmouseover="this.style.borderColor='#40e0d0'; this.style.boxShadow='0 2px 8px rgba(64, 224, 208, 0.2)'" 
				       onmouseout="this.style.borderColor='#e9ecef'; this.style.boxShadow='none'">
					<input type="radio" name="saved_address" value="${address.id}" style="margin-right: 1rem; margin-top: 0.25rem;" 
					       onchange="selectSavedAddress(${address.id})">
					<div style="flex: 1;">
						<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
							<strong style="color: #2d3436;">${typeText}</strong>
							${address.isDefault ? '<span style="background: #40e0d0; color: white; padding: 0.25rem 0.5rem; border-radius: 12px; font-size: 0.75rem; font-weight: 600;">Padrão</span>' : ''}
						</div>
						<p style="margin: 0.25rem 0; color: #6c757d; font-size: 0.9rem;">${address.street}, ${address.number}${address.complement ? ', ' + address.complement : ''}</p>
						<p style="margin: 0.25rem 0; color: #6c757d; font-size: 0.9rem;">${address.neighborhood} - ${address.city}/${address.state}</p>
						<p style="margin: 0.25rem 0; color: #6c757d; font-size: 0.9rem;">CEP: ${formattedCep}</p>
						${address.phone ? `<p style="margin: 0.25rem 0; color: #6c757d; font-size: 0.9rem;">Telefone: ${address.phone}</p>` : ''}
					</div>
				</label>
			`;
		});
		html += '</div>';
		list.innerHTML = html;
	}
	
	/**
	 * Seleciona um endereço salvo e preenche o formulário
	 */
	window.selectSavedAddress = function(addressId) {
		selectedSavedAddressId = addressId;
		const address = savedAddresses.find(addr => addr.id === addressId);
		if (!address) return;
		
		// IMPORTANTE: Salvar o nome ANTES de fazer qualquer alteração
		// Isso garante que o nome do perfil não seja perdido
		const currentName = nomeRecebedorInput ? nomeRecebedorInput.value : '';
		console.log('[Checkout] Nome atual antes de selecionar endereço:', currentName);
		
		// Preencher formulário com dados do endereço salvo
		if (ruaInput) ruaInput.value = address.street || '';
		if (numeroInput) numeroInput.value = address.number || '';
		if (complementoInput) complementoInput.value = address.complement || '';
		if (bairroInput) bairroInput.value = address.neighborhood || '';
		if (cidadeInput) cidadeInput.value = address.city || '';
		if (estadoSelect) estadoSelect.value = address.state || '';
		if (cepInput) {
			const formattedCep = address.zipcode ? address.zipcode.replace(/^(\d{5})(\d{3})$/, '$1-$2') : '';
			cepInput.value = formattedCep;
		}
		
		// Preencher telefone se disponível no endereço (mas não sobrescrever se já foi preenchido do perfil)
		if (address.phone) {
			const phoneAreaInput = document.getElementById('phone_area');
			const phoneNumberInput = document.getElementById('phone_number');
			// Só preencher se os campos estiverem vazios
			if (phoneAreaInput && !phoneAreaInput.value) {
				const phoneMatch = address.phone.match(/^(\d{2})(\d{4,5}\d{4})$/);
				if (phoneMatch) {
					phoneAreaInput.value = phoneMatch[1];
					if (phoneNumberInput && !phoneNumberInput.value) {
						const number = phoneMatch[2];
						phoneNumberInput.value = number.length === 8 ? 
							number.replace(/^(\d{4})(\d{4})$/, '$1-$2') : 
							number.replace(/^(\d{5})(\d{4})$/, '$1-$2');
					}
				}
			}
		}
		
		// Preencher nome do recebedor: usar nome do endereço se disponível, senão preservar o nome atual
		if (nomeRecebedorInput) {
			if (address.receiver_name && address.receiver_name.trim()) {
				// Endereço tem nome específico, usar ele
				nomeRecebedorInput.value = address.receiver_name;
				console.log('[Checkout] Usando nome do endereço:', address.receiver_name);
			} else {
				// Endereço não tem nome, preservar o nome atual (do perfil)
				if (currentName && currentName.trim()) {
					nomeRecebedorInput.value = currentName;
					console.log('[Checkout] Preservando nome do perfil:', currentName);
				} else {
					console.log('[Checkout] Nenhum nome disponível (nem endereço nem perfil)');
				}
			}
		}
		
		// Ocultar formulário de endereço quando um endereço salvo é selecionado
		// (usuário não pode adicionar novo endereço no checkout, apenas no perfil)
		// IMPORTANTE: Fazer isso DEPOIS de preencher todos os campos
		const addressForm = document.getElementById('address-form');
		if (addressForm) {
			addressForm.style.display = 'none';
		}
		
		// Recalcular frete se CEP foi preenchido
		if (address.zipcode) {
			const cleanCEP = address.zipcode.replace(/\D/g, '');
			if (cleanCEP.length === 8 && window.calculateShipping) {
				window.calculateShipping(cleanCEP);
			}
		}
	};
    
	async function getAuthHeaders() {
		const headers = { 'Content-Type': 'application/json' };
		let sessionId = localStorage.getItem('cartSessionId');
		if (!sessionId) {
			sessionId = crypto.randomUUID();
			localStorage.setItem('cartSessionId', sessionId);
		}
		headers['X-Session-ID'] = sessionId;
		return headers;
	}
    
	async function fetchCartData() {
		try {
			console.log('[Checkout] Buscando dados do carrinho...');
			const headers = await getAuthHeaders();
			const response = await fetch('/api/cart', { method: 'GET', credentials: 'include', headers: headers });
			if (!response.ok) {
				const errorData = await response.json().catch(() => ({ erro: 'Erro desconhecido' }));
				if (response.status === 401) return { items: [], total_value: 0 };
				throw new Error(errorData.erro || `HTTP ${response.status}`);
			}
			const data = await response.json();
			return { items: data.items || [], total_value: data.total_value || 0 };
		} catch (error) {
			console.error('[Checkout] Erro ao buscar dados do carrinho:', error);
			return { items: [], total_value: 0 };
		}
	}
	
	/**
	 * Carrega dados do perfil do usuário e preenche automaticamente os campos
	 */
	async function loadUserProfile() {
		try {
			// Verificar se Firebase está disponível
			let firebaseAuth = null;
			let onAuthStateChangedFn = null;
			try {
				const { initializeApp } = await import('https://www.gstatic.com/firebasejs/10.12.2/firebase-app.js');
				const { getAuth, onAuthStateChanged } = await import('https://www.gstatic.com/firebasejs/10.12.2/firebase-auth.js');
				
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
				firebaseAuth = getAuth(app);
				onAuthStateChangedFn = onAuthStateChanged;
			} catch (error) {
				console.log('[Checkout] Firebase não disponível:', error);
				return;
			}
			
			if (!firebaseAuth || !onAuthStateChangedFn) return;
			
			// Aguardar o estado de autenticação
			return new Promise((resolve) => {
				onAuthStateChangedFn(firebaseAuth, async (user) => {
					if (!user) {
						console.log('[Checkout] Usuário não logado, não carregando perfil');
						resolve();
						return;
					}
					
					try {
						const idToken = await user.getIdToken();
						const response = await fetch('/api/user_data', {
							method: 'GET',
							headers: {
								'Authorization': `Bearer ${idToken}`,
								'Content-Type': 'application/json'
							}
						});
						
						if (response.ok) {
							const userData = await response.json();
							console.log('[Checkout] Dados do perfil carregados:', userData);
							
							// Preencher campos automaticamente
							if (nomeRecebedorInput && userData.nome) {
								nomeRecebedorInput.value = userData.nome;
							}
							
							const emailInput = document.getElementById('email');
							if (emailInput && userData.email) {
								emailInput.value = userData.email;
							}
							
							const cpfInput = document.getElementById('cpf_cnpj');
							if (cpfInput && userData.cpf) {
								// Formatar CPF
								const cpf = userData.cpf.replace(/\D/g, '');
								if (cpf.length === 11) {
									cpfInput.value = cpf.replace(/^(\d{3})(\d{3})(\d{3})(\d{2})$/, '$1.$2.$3-$4');
								} else {
									cpfInput.value = userData.cpf;
								}
							}
							
							// Preencher telefone
							if (userData.telefone) {
								const phone = userData.telefone.replace(/\D/g, '');
								const phoneAreaInput = document.getElementById('phone_area');
								const phoneNumberInput = document.getElementById('phone_number');
								
								if (phone.length >= 10) {
									const area = phone.substring(0, 2);
									const number = phone.substring(2);
									
									if (phoneAreaInput) phoneAreaInput.value = area;
									if (phoneNumberInput) {
										if (number.length === 8) {
											phoneNumberInput.value = number.replace(/^(\d{4})(\d{4})$/, '$1-$2');
										} else if (number.length === 9) {
											phoneNumberInput.value = number.replace(/^(\d{5})(\d{4})$/, '$1-$2');
										} else {
											phoneNumberInput.value = number;
										}
									}
								}
							}
						}
					} catch (error) {
						console.error('[Checkout] Erro ao carregar dados do perfil:', error);
					}
					resolve();
				});
			});
		} catch (error) {
			console.error('[Checkout] Erro ao carregar perfil:', error);
		}
	}
	
	// Carregar endereços salvos e dados do perfil quando a página carregar
	loadSavedAddresses();
	loadUserProfile();
    
	function renderCartItems() {
		if (!cartItemsContainer) return;
		cartItemsContainer.innerHTML = '';
		if (!cartData.items || cartData.items.length === 0) {
			cartItemsContainer.innerHTML = `
				<div style="text-align: center; padding: 20px; color: #666;">
					<p>Seu carrinho está vazio</p>
					<a href="/produtos" style="color: #007bff; text-decoration: none;">← Continuar comprando</a>
				</div>
			`;
			return;
		}
		cartData.items.forEach(item => {
			const itemDiv = document.createElement('div');
			itemDiv.className = 'summary-item';
			itemDiv.style.cssText = 'display: flex; align-items: center; padding: 15px; border-bottom: 1px solid #eee;';
			const itemImage = item.image_url || '/static/img/placeholder.jpg';
			const itemPrice = item.price_at_time_of_add || 0;
			const itemTotal = item.item_total || (item.quantity * itemPrice);
			itemDiv.innerHTML = `
				<img src="${itemImage}" alt="${item.product_name}" 
					 style="width: 60px; height: 60px; object-fit: cover; border-radius: 8px; margin-right: 15px;">
				<div style="flex: 1;">
					<div style="font-weight: 600; margin-bottom: 5px;">${item.product_name}</div>
					<div style="font-size: 0.9em; color: #666; margin-bottom: 3px;">${item.estampa_name} / ${item.tamanho_name}</div>
					<div style="font-size: 0.85em; color: #999;"> Qtd: ${item.quantity} × ${formatCurrency(itemPrice)} </div>
				</div>
				<div style="font-weight: 600; color: #333;"> ${formatCurrency(itemTotal)} </div>
			`;
			cartItemsContainer.appendChild(itemDiv);
		});
	}
    
	function updateTotals() {
		const subtotal = cartData.total_value || 0;
		const freight = cartData.freight || 0;
		const total = subtotal + freight;
		if (subtotalElem) subtotalElem.textContent = formatCurrency(subtotal);
		if (freightElem) freightElem.textContent = formatCurrency(freight);
		if (totalElem) totalElem.textContent = formatCurrency(total);
	}
    
	async function loadCartData() {
		try {
			cartData = await fetchCartData();
			renderCartItems();
			updateTotals();
		} catch (error) {
			console.error('[Checkout] Erro ao carregar dados do carrinho:', error);
			if (cartItemsContainer) {
				cartItemsContainer.innerHTML = `
					<div style="text-align: center; padding: 20px; color: #dc3545;">
						<p>Erro ao carregar carrinho</p>
						<button onclick="window.location.reload()" style="margin-top: 10px; padding: 8px 16px; background: #007bff; color: white; border: none; border-radius: 4px; cursor: pointer;">Recarregar</button>
					</div>
				`;
			}
		}
	}
	loadCartData();
    
	async function fetchAddressByCEP(cep) {
		try {
			const cleanCEP = cep.replace(/\D/g, '');
			if (cleanCEP.length !== 8) return null;
			const response = await fetch(`https://viacep.com.br/ws/${cleanCEP}/json/`);
			if (!response.ok) throw new Error(`HTTP ${response.status}: ${response.statusText}`);
			const data = await response.json();
			if (data.erro) { alert('CEP não encontrado. Verifique o CEP digitado.'); return null; }
			return { street: data.logradouro || '', district: data.bairro || '', city: data.localidade || '', state: data.uf || '', cep: data.cep || cleanCEP };
		} catch (error) {
			console.error('[Checkout] Erro ao buscar CEP na ViaCEP:', error);
			alert('Erro ao buscar CEP. Verifique sua conexão e tente novamente.');
			return null;
		}
	}
    
	async function fillAddressByCEP(cep) {
		if (!cep || cep.replace(/\D/g, '').length !== 8) return;
		const originalPlaceholder = cepInput.placeholder;
		cepInput.disabled = true;
		cepInput.placeholder = 'Buscando endereço...';
		if (buscarCepBtn) { buscarCepBtn.disabled = true; buscarCepBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i>'; }
		try {
			const addressData = await fetchAddressByCEP(cep);
			if (addressData) {
				if (ruaInput) ruaInput.value = addressData.street;
				if (bairroInput) bairroInput.value = addressData.district;
				if (cidadeInput) cidadeInput.value = addressData.city;
				if (estadoSelect && addressData.state) estadoSelect.value = addressData.state;
				const formattedCEP = addressData.cep.replace(/^(\d{5})(\d{3})$/, '$1-$2');
				cepInput.value = formattedCEP;
				if (numeroInput) setTimeout(() => numeroInput.focus(), 100);
				// Calcular frete com CEP limpo (sem formatação)
				const cleanCEP = cep.replace(/\D/g, '');
				if (cleanCEP.length === 8) {
					setTimeout(() => {
						window.calculateShipping(cleanCEP);
					}, 500);
				}
			}
		} catch (error) {
			console.error('[Checkout] Erro ao preencher endereço:', error);
		} finally {
			cepInput.disabled = false;
			cepInput.placeholder = originalPlaceholder;
			if (buscarCepBtn) { buscarCepBtn.disabled = false; buscarCepBtn.innerHTML = '🔍 Buscar'; }
		}
	}
    
	window.calculateShipping = async function(cep) {
		console.log('[Checkout] calculateShipping chamado com CEP:', cep);
		const shippingOptionsContainer = document.getElementById('shippingOptions');
		if (!shippingOptionsContainer) {
			console.error('[Checkout] Container de opções de frete não encontrado');
			return;
		}
		const cleanCEP = cep ? cep.replace(/\D/g, '') : '';
		if (cleanCEP.length !== 8) {
			console.warn('[Checkout] CEP inválido:', cleanCEP);
			return;
		}
		console.log('[Checkout] Calculando frete para CEP:', cleanCEP);
		shippingOptionsContainer.innerHTML = `<div style="text-align: center; padding: 20px;"><div class="loading-spinner" style="font-size: 2rem; margin: 0 auto 10px;"><i class="fas fa-spinner"></i></div><p>Calculando frete...</p></div>`;
		try {
			const headers = await getAuthHeaders();
			const response = await fetch('/api/shipping/calculate', { 
				method: 'POST', 
				credentials: 'include', 
				headers: headers, 
				body: JSON.stringify({ cep: cleanCEP }) 
			});
			if (!response.ok) { 
				const errorData = await response.json().catch(() => ({ erro: 'Erro desconhecido' })); 
				throw new Error(errorData.erro || `HTTP ${response.status}`); 
			}
			const data = await response.json();
			console.log('[Checkout] Resposta do cálculo de frete:', data);
			if (!data.shipping_options || data.shipping_options.length === 0) { 
				shippingOptionsContainer.innerHTML = `<div style="text-align: center; padding: 20px; color: #666;"><p>Não foi possível calcular o frete para este CEP.</p><p style="font-size: 0.9em; color: #999;">Verifique o CEP e tente novamente.</p></div>`; 
				return; 
			}
			renderShippingOptions(data.shipping_options);
		} catch (error) {
			console.error('[Checkout] Erro ao calcular frete:', error);
			shippingOptionsContainer.innerHTML = `<div style="text-align: center; padding: 20px; color: #dc3545;"><p>Erro ao calcular frete</p><p style="font-size: 0.9em; color: #999;">${error.message}</p><button onclick="calculateShipping('${cleanCEP}')" style="margin-top: 10px; padding: 8px 16px; background: #007bff; color: white; border: none; border-radius: 4px; cursor: pointer;">Tentar novamente</button></div>`;
		}
	}
    
	function renderShippingOptions(options) {
		const shippingOptionsContainer = document.getElementById('shippingOptions');
		if (!shippingOptionsContainer) return;
		shippingOptionsContainer.innerHTML = '';
		selectedShippingOption = null;
		options.forEach((option, index) => {
			const optionDiv = document.createElement('div');
			optionDiv.className = 'shipping-option';
			optionDiv.style.cssText = 'display: flex; align-items: center; padding: 15px; margin-bottom: 10px; border: 2px solid #e0e0e0; border-radius: 8px; cursor: pointer; transition: all 0.3s;';
			const priceFormatted = formatCurrency(option.price);
			optionDiv.innerHTML = `
				<input type="radio" name="shipping-option" id="shipping-${index}" value="${option.service}" style="margin-right: 15px; cursor: pointer;">
				<label for="shipping-${index}" style="flex: 1; cursor: pointer;"><div style="font-weight: 600; margin-bottom: 5px;">${option.name}</div><div style="font-size: 0.9em; color: #666;">${option.description || option.delivery_time}</div><div style="font-size: 0.85em; color: #999; margin-top: 3px;">${option.delivery_time}</div></label><div style="font-weight: 700; font-size: 1.2em; color: #007bff;">${priceFormatted}</div>
			`;
			optionDiv.addEventListener('click', function() {
				document.querySelectorAll('input[name="shipping-option"]').forEach(radio => { radio.checked = false; radio.closest('.shipping-option').style.borderColor = '#e0e0e0'; radio.closest('.shipping-option').style.backgroundColor = ''; });
				const radio = optionDiv.querySelector('input[type="radio"]');
				radio.checked = true;
				optionDiv.style.borderColor = '#007bff';
				optionDiv.style.backgroundColor = '#f0f8ff';
				selectedShippingOption = option;
				cartData.freight = option.price;
				updateTotals();
			});
			if (index === 0) setTimeout(() => optionDiv.click(), 100);
			shippingOptionsContainer.appendChild(optionDiv);
		});
	}
	
	// --- Gerenciar exibição do formulário de cartão ---
	function toggleCreditCardForm() {
		const selectedMethod = document.querySelector('input[name="payment_method"]:checked');
		if (creditCardForm) {
			if (selectedMethod && selectedMethod.value === 'CREDIT_CARD') {
				creditCardForm.style.display = 'block';
			} else {
				creditCardForm.style.display = 'none';
			}
		}
	}
	
	// Adicionar listeners aos radio buttons de pagamento
	paymentMethodRadios.forEach(radio => {
		radio.addEventListener('change', toggleCreditCardForm);
	});
	
	// Inicializar estado do formulário de cartão
	toggleCreditCardForm();
	
	// --- Validação e submissão do formulário ---
	if (checkoutForm) {
		checkoutForm.addEventListener('submit', async function(e) {
			e.preventDefault();
			
			// Validar campos obrigatórios
			if (!nomeRecebedorInput || !nomeRecebedorInput.value.trim()) {
				alert('Por favor, preencha o nome do recebedor');
				nomeRecebedorInput?.focus();
				return;
			}
			
			if (!cepInput || !cepInput.value.replace(/\D/g, '').match(/^\d{8}$/)) {
				alert('Por favor, preencha um CEP válido');
				cepInput?.focus();
				return;
			}
			
			if (!ruaInput || !ruaInput.value.trim()) {
				alert('Por favor, preencha a rua');
				ruaInput?.focus();
				return;
			}
			
			if (!numeroInput || !numeroInput.value.trim()) {
				alert('Por favor, preencha o número');
				numeroInput?.focus();
				return;
			}
			
			if (!bairroInput || !bairroInput.value.trim()) {
				alert('Por favor, preencha o bairro');
				bairroInput?.focus();
				return;
			}
			
			if (!cidadeInput || !cidadeInput.value.trim()) {
				alert('Por favor, preencha a cidade');
				cidadeInput?.focus();
				return;
			}
			
			if (!estadoSelect || !estadoSelect.value) {
				alert('Por favor, selecione o estado');
				estadoSelect?.focus();
				return;
			}
			
			if (!selectedShippingOption) {
				alert('Por favor, selecione uma opção de frete');
				return;
			}
			
			const selectedPaymentMethod = document.querySelector('input[name="payment_method"]:checked');
			if (!selectedPaymentMethod) {
				alert('Por favor, selecione um método de pagamento');
				return;
			}
			
			// Validar dados do cartão se necessário
			if (selectedPaymentMethod.value === 'CREDIT_CARD') {
				const cardNumber = document.getElementById('card_number')?.value.replace(/\s/g, '');
				const cardHolderName = document.getElementById('card_holder_name')?.value.trim();
				const cardExpMonth = document.getElementById('card_exp_month')?.value.trim();
				const cardExpYear = document.getElementById('card_exp_year')?.value.trim();
				const cardCvv = document.getElementById('card_cvv')?.value.trim();
				
				if (!cardNumber || cardNumber.length < 13) {
					alert('Por favor, preencha um número de cartão válido');
					document.getElementById('card_number')?.focus();
					return;
				}
				
				if (!cardHolderName || cardHolderName.length < 3) {
					alert('Por favor, preencha o nome no cartão');
					document.getElementById('card_holder_name')?.focus();
					return;
				}
				
				if (!cardExpMonth || !cardExpYear) {
					alert('Por favor, preencha a validade do cartão');
					return;
				}
				
				if (!cardCvv || cardCvv.length < 3) {
					alert('Por favor, preencha o CVV do cartão');
					document.getElementById('card_cvv')?.focus();
					return;
				}
			}
			
			// Verificar se há itens no carrinho
			if (!cartData.items || cartData.items.length === 0) {
				alert('Seu carrinho está vazio. Adicione produtos antes de finalizar a compra.');
				window.location.href = '/produtos';
				return;
			}
			
			// Mostrar loading
			if (checkoutLoading) checkoutLoading.style.display = 'flex';
			if (finalizarCompraBtn) {
				finalizarCompraBtn.disabled = true;
				finalizarCompraBtn.innerHTML = '<span>⏳</span><span>Processando...</span>';
			}
			
			try {
			// Capturar dados adicionais
			const emailInput = document.getElementById('email');
			const cpfCnpjInput = document.getElementById('cpf_cnpj');
			const phoneAreaInput = document.getElementById('phone_area');
			const phoneNumberInput = document.getElementById('phone_number');
			
			// Validar email
			if (!emailInput || !emailInput.value.trim() || !emailInput.value.includes('@')) {
				alert('Por favor, preencha um email válido');
				emailInput?.focus();
				return;
			}
			
			// Validar CPF/CNPJ
			const cpfCnpj = cpfCnpjInput?.value.replace(/\D/g, '') || '';
			if (!cpfCnpj || cpfCnpj.length < 11) {
				alert('Por favor, preencha um CPF/CNPJ válido');
				cpfCnpjInput?.focus();
				return;
			}
			
			// Validar telefone
			const phoneArea = phoneAreaInput?.value.replace(/\D/g, '') || '';
			const phoneNumber = phoneNumberInput?.value.replace(/\D/g, '') || '';
			if (!phoneArea || phoneArea.length < 2) {
				alert('Por favor, preencha o DDD do telefone');
				phoneAreaInput?.focus();
				return;
			}
			if (!phoneNumber || phoneNumber.length < 8) {
				alert('Por favor, preencha o número do telefone');
				phoneNumberInput?.focus();
				return;
			}
			
			// Verificar se está usando um endereço salvo
			let endereco_id = selectedSavedAddressId;
			
			// Preparar dados do checkout
			const checkoutData = {
				shipping_info: {
					endereco_id: endereco_id,  // Incluir ID do endereço salvo se selecionado
					nome_recebedor: nomeRecebedorInput.value.trim(),
					email: emailInput.value.trim(),
					cpf_cnpj: cpfCnpj,
					phone_area: phoneArea,
					phone_number: phoneNumber,
					telefone: phoneArea + phoneNumber,  // Telefone completo para o backend
					cep: cepInput.value.replace(/\D/g, ''),
					rua: ruaInput.value.trim(),
					numero: numeroInput.value.trim(),
					complemento: complementoInput?.value.trim() || '',
					bairro: bairroInput.value.trim(),
					cidade: cidadeInput.value.trim(),
					estado: estadoSelect.value
				},
					shipping_option: {
						name: selectedShippingOption.name,
						price: selectedShippingOption.price,
						service: selectedShippingOption.service,
						deadline: selectedShippingOption.delivery_time || selectedShippingOption.deadline
					},
					freight_value: selectedShippingOption.price,
					payment_method: selectedPaymentMethod.value,
					payment_details: {}
				};
				
				// Adicionar dados do cartão se necessário
				if (selectedPaymentMethod.value === 'CREDIT_CARD') {
					const installments = parseInt(document.getElementById('installments')?.value || '1');
					const cardExpYear = document.getElementById('card_exp_year')?.value.trim() || '';
					
					// Converter ano de 4 dígitos para 2 dígitos se necessário (para compatibilidade)
					let cardExpYearFormatted = cardExpYear;
					if (cardExpYear.length === 4) {
						cardExpYearFormatted = cardExpYear.substring(2); // Pega os últimos 2 dígitos
					}
					
					checkoutData.payment_details = {
						card_number: document.getElementById('card_number')?.value.replace(/\s/g, ''),
						card_holder_name: document.getElementById('card_holder_name')?.value.trim(),
						card_exp_month: document.getElementById('card_exp_month')?.value.trim().padStart(2, '0'),
						card_exp_year: cardExpYearFormatted,
						card_cvv: document.getElementById('card_cvv')?.value.trim(),
						installments: installments,
						customer_name: nomeRecebedorInput.value.trim(),
						customer_email: emailInput.value.trim(),
						customer_cpf_cnpj: cpfCnpj,
						customer_phone_area: phoneArea,
						customer_phone_number: phoneNumber
					};
				} else {
					// Para PIX e Boleto, também enviar dados do cliente
					checkoutData.payment_details = {
						customer_name: nomeRecebedorInput.value.trim(),
						customer_email: emailInput.value.trim(),
						customer_cpf_cnpj: cpfCnpj,
						customer_phone_area: phoneArea,
						customer_phone_number: phoneNumber
					};
				}
				
				// Fazer requisição para processar checkout
				const headers = await getAuthHeaders();
				const response = await fetch('/api/checkout/process', {
					method: 'POST',
					credentials: 'include',
					headers: headers,
					body: JSON.stringify(checkoutData)
				});
				
				const responseData = await response.json();
				
				if (!response.ok) {
					throw new Error(responseData.erro || responseData.message || 'Erro ao processar checkout');
				}
				
				if (!responseData.success) {
					throw new Error(responseData.erro || 'Erro ao processar checkout');
				}
				
				// Obter token público e método de pagamento
				const publicToken = responseData.public_token;
				const paymentMethodType = responseData.payment_method_type || selectedPaymentMethod.value.toLowerCase();
				
				if (!publicToken) {
					throw new Error('Token público não retornado pelo servidor');
				}
				
				// Redirecionar baseado no método de pagamento
				if (selectedPaymentMethod.value === 'CREDIT_CARD') {
					// Cartão de crédito → página de status
					window.location.href = `/status-pedido?token=${publicToken}`;
				} else if (selectedPaymentMethod.value === 'PIX') {
					// PIX → página de pagamento PIX
					window.location.href = `/pagamento/pix?token=${publicToken}`;
				} else if (selectedPaymentMethod.value === 'BOLETO') {
					// Boleto → página de pagamento Boleto
					window.location.href = `/pagamento/boleto?token=${publicToken}`;
				} else {
					// Fallback para página de status
					window.location.href = `/status-pedido?token=${publicToken}`;
				}
				
			} catch (error) {
				console.error('[Checkout] Erro ao processar checkout:', error);
				alert(`Erro ao processar checkout: ${error.message}`);
				
				// Esconder loading
				if (checkoutLoading) checkoutLoading.style.display = 'none';
				if (finalizarCompraBtn) {
					finalizarCompraBtn.disabled = false;
					finalizarCompraBtn.innerHTML = '<span>🛒</span><span>Finalizar Compra</span>';
				}
			}
		});
	}
    
	if (buscarCepBtn && cepInput) {
		buscarCepBtn.addEventListener('click', function(e) { e.preventDefault(); const cep = cepInput.value.replace(/\D/g, ''); if (cep.length === 8) { fillAddressByCEP(cep); } else { alert('Por favor, digite um CEP válido (8 dígitos)'); cepInput.focus(); } });
	}
    
	if (cepInput) {
		cepInput.addEventListener('input', function(e) { let value = e.target.value.replace(/\D/g, ''); if (value.length > 5) value = value.substring(0, 5) + '-' + value.substring(5, 8); e.target.value = value; });
		let cepTimeout;
		cepInput.addEventListener('input', function(e) { 
			const value = e.target.value.replace(/\D/g, ''); 
			clearTimeout(cepTimeout); 
			if (value.length === 8) { 
				cepTimeout = setTimeout(() => { 
					fillAddressByCEP(value); 
				}, 800); 
			}
		});
		cepInput.addEventListener('blur', function(e) { 
			const cep = e.target.value.replace(/\D/g, ''); 
			if (cep.length === 8) { 
				fillAddressByCEP(cep); 
			}
		});
		// Adicionar listener para recalcular frete quando CEP mudar manualmente
		cepInput.addEventListener('change', function(e) {
			const cep = e.target.value.replace(/\D/g, '');
			if (cep.length === 8) {
				window.calculateShipping(cep);
			}
		});
	}
	
	// Máscaras para campos do cartão
	const cardNumberInput = document.getElementById('card_number');
	if (cardNumberInput) {
		cardNumberInput.addEventListener('input', function(e) {
			let value = e.target.value.replace(/\s/g, '');
			if (value.length > 16) value = value.substring(0, 16);
			value = value.replace(/(\d{4})(?=\d)/g, '$1 ');
			e.target.value = value;
		});
	}
	
	const cardExpMonthInput = document.getElementById('card_exp_month');
	const cardExpYearInput = document.getElementById('card_exp_year');
	if (cardExpMonthInput) {
		cardExpMonthInput.addEventListener('input', function(e) {
			let value = e.target.value.replace(/\D/g, '');
			if (value.length > 2) value = value.substring(0, 2);
			if (value.length === 2 && parseInt(value) > 12) value = '12';
			e.target.value = value;
		});
	}
	
	if (cardExpYearInput) {
		cardExpYearInput.addEventListener('input', function(e) {
			// Aceitar 4 dígitos para o ano
			let value = e.target.value.replace(/\D/g, '');
			if (value.length > 4) value = value.substring(0, 4);
			e.target.value = value;
		});
	}
	
	// Máscara para CPF/CNPJ
	const cpfCnpjInput = document.getElementById('cpf_cnpj');
	if (cpfCnpjInput) {
		cpfCnpjInput.addEventListener('input', function(e) {
			let value = e.target.value.replace(/\D/g, '');
			if (value.length <= 11) {
				// CPF: 000.000.000-00
				if (value.length <= 3) {
					value = value;
				} else if (value.length <= 6) {
					value = value.replace(/^(\d{3})(\d*)$/, '$1.$2');
				} else if (value.length <= 9) {
					value = value.replace(/^(\d{3})(\d{3})(\d*)$/, '$1.$2.$3');
				} else {
					value = value.replace(/^(\d{3})(\d{3})(\d{3})(\d{2})$/, '$1.$2.$3-$4');
				}
			} else {
				// CNPJ: 00.000.000/0000-00
				value = value.substring(0, 14);
				if (value.length <= 2) {
					value = value;
				} else if (value.length <= 5) {
					value = value.replace(/^(\d{2})(\d*)$/, '$1.$2');
				} else if (value.length <= 8) {
					value = value.replace(/^(\d{2})(\d{3})(\d*)$/, '$1.$2.$3');
				} else if (value.length <= 12) {
					value = value.replace(/^(\d{2})(\d{3})(\d{3})(\d*)$/, '$1.$2.$3/$4');
				} else {
					value = value.replace(/^(\d{2})(\d{3})(\d{3})(\d{4})(\d{2})$/, '$1.$2.$3/$4-$5');
				}
			}
			e.target.value = value;
		});
	}
	
	// Máscara para telefone
	const phoneAreaInput = document.getElementById('phone_area');
	const phoneNumberInput = document.getElementById('phone_number');
	if (phoneAreaInput) {
		phoneAreaInput.addEventListener('input', function(e) {
			let value = e.target.value.replace(/\D/g, '');
			if (value.length > 2) value = value.substring(0, 2);
			e.target.value = value;
		});
	}
	if (phoneNumberInput) {
		phoneNumberInput.addEventListener('input', function(e) {
			let value = e.target.value.replace(/\D/g, '');
			if (value.length > 9) value = value.substring(0, 9);
			if (value.length > 8) {
				value = value.replace(/^(\d{5})(\d{4})$/, '$1-$2');
			} else if (value.length > 4) {
				value = value.replace(/^(\d{4})(\d*)$/, '$1-$2');
			}
			e.target.value = value;
		});
	}
	
	const cardCvvInput = document.getElementById('card_cvv');
	if (cardCvvInput) {
		cardCvvInput.addEventListener('input', function(e) {
			let value = e.target.value.replace(/\D/g, '');
			if (value.length > 3) value = value.substring(0, 3);
			e.target.value = value;
		});
	}
});
